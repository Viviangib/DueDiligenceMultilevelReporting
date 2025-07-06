from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from utils.indicator_parser import (
    extract_text_from_pdf_bytes,
    extract_text_from_docx_bytes,
    parse_indicators_with_llm,
    save_to_docx
)
import uuid
import os
from pprint import pformat
from controllers.indicator import save_indicator_controller
from sqlalchemy.orm import Session
from db import SessionLocal
from fastapi import Depends
from fastapi import BackgroundTasks
from services.indicator import IndicatorService


router = APIRouter(prefix="/indicators", tags=["indicators"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/extract")
def extract_indicators(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename or not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    # Read file content before starting background task
    content = file.file.read()
    filename = file.filename
    # Create indicator status job
    indicator_service = IndicatorService()
    status_job = indicator_service.create_status_job(db)
    status_id = int(getattr(status_job, 'id'))
    # Start background task to extract and save indicators
    background_tasks.add_task(process_and_save_indicators_bg, content, filename, db, status_id)
    return {"status_id": status_id, "message": "Indicator extraction started. Check status with GET /indicators/extract/status/{status_id}"}

def process_and_save_indicators_bg(content: bytes, filename: str, db: Session, status_id: int):
    import logging
    logger = logging.getLogger(__name__)
    try:
        if filename and filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf_bytes(content)
        elif filename and filename.endswith(".docx"):
            extracted_text = extract_text_from_docx_bytes(content)
        else:
            raise Exception("Unsupported file type or missing filename.")
        if not extracted_text:
            raise Exception("No readable text found in file.")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result_text = loop.run_until_complete(parse_indicators_with_llm(extracted_text))
        # Save all indicators using save_indicator for each one
        indicator_service = IndicatorService()
        if isinstance(result_text, list):
            for indicator in result_text:
                indicator_service.save_indicator(db, indicator)
        else:
            indicator_service.save_indicator(db, result_text)
        indicator_service.update_status_job(db, status_id, "completed")
    except Exception as e:
        logger.error(f"Indicator extraction failed: {str(e)}")
        IndicatorService().update_status_job(db, status_id, "error")

@router.get("/extract/status/{status_id}")
def get_indicator_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    from models.indicator_status import IndicatorStatus
    status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
    if not status_job:
        raise HTTPException(status_code=404, detail="Indicator status not found")
    return status_job

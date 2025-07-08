from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from utils.indicator_parser import (
    extract_text_from_pdf_bytes,
    extract_text_from_docx_bytes,
    parse_indicators_with_llm,
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
import pandas as pd
import json
from models.indicator_status import IndicatorStatus


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
        indicator_service = IndicatorService()
        indicators_saved = []
        if isinstance(result_text, list):
            for indicator in result_text:
                indicators_saved.append(indicator_service.save_indicator(db, indicator))
        else:
            indicators_saved.append(indicator_service.save_indicator(db, result_text))
        # Generate Excel file with Indicator ID and Question
        data = []
        for idx, indicator_obj in enumerate(indicators_saved):
            raw_indicator = indicator_obj.indicator
            if isinstance(raw_indicator, str):
                try:
                    parsed = json.loads(raw_indicator)
                except Exception as e:
                    logger.error(f"Failed to parse indicator JSON: {e}")
                    parsed = {}
            elif isinstance(raw_indicator, dict):
                parsed = raw_indicator
            else:
                logger.error(f"Unexpected type for indicator: {type(raw_indicator)}")
                parsed = {}
            indicator_id = parsed.get("ID", f"IND{idx+1:03d}")
            question = parsed.get("Question", str(parsed))
            data.append({"Indicator ID": indicator_id, "Question": question})
        df = pd.DataFrame(data)
        os.makedirs("results", exist_ok=True)
        excel_path = os.path.join("results", f"indicator_extract_{status_id}.xlsx")
        df.to_excel(excel_path, index=False)
        # Save file path in IndicatorStatus
        status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        if status_job:
            setattr(status_job, 'file', excel_path)
            setattr(status_job, 'status', 'completed')
            db.commit()
        else:
            logger.error(f"IndicatorStatus with id {status_id} not found.")
    except Exception as e:
        logger.error(f"Indicator extraction failed: {str(e)}")
        status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        if status_job:
            setattr(status_job, 'status', 'error')
            db.commit()

@router.get("/extract/status/{status_id}")
def get_indicator_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
    if not status_job:
        raise HTTPException(status_code=404, detail="Indicator status not found")
    file_path = getattr(status_job, 'file', None)
    if isinstance(file_path, str) and file_path and os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(file_path)
        )
    return status_job

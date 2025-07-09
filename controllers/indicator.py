import os
import json
import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enums.indicator import IndicatorStatusEnum
from constants.indicator import (
    INDICATOR_EXTRACT_ERROR,
    INDICATOR_STATUS_NOT_FOUND,
    INDICATOR_FILE_PATH_TEMPLATE,
    INDICATOR_EXCEL_MEDIA_TYPE,
)
from services.indicator import IndicatorService
from models.indicator_status import IndicatorStatus
from utils.file_extraction import extract_text_from_pdf_bytes, extract_text_from_docx_bytes
from utils.indicator_parsing import parse_indicators_with_llm
import logging

indicator_service = IndicatorService()
logger = logging.getLogger(__name__)

def start_indicator_extraction(background_tasks: BackgroundTasks, file: UploadFile, db: Session):
    if not file.filename or not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    content = file.file.read()
    filename = file.filename
    status_job = indicator_service.create_status_job(db)
    status_id = int(getattr(status_job, 'id'))
    background_tasks.add_task(process_and_save_indicators_bg, content, filename, db, status_id)
    return {"status_id": status_id, "message": "Indicator extraction started. Check status with GET /indicators/extract/status/{status_id}"}

def process_and_save_indicators_bg(content: bytes, filename: str, db: Session, status_id: int):
    try:
        if filename.endswith(".pdf"):
            extracted_text = extract_text_from_pdf_bytes(content)
        elif filename.endswith(".docx"):
            extracted_text = extract_text_from_docx_bytes(content)
        else:
            raise Exception("Unsupported file type or missing filename.")
        if not extracted_text:
            raise Exception("No readable text found in file.")
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result_text = loop.run_until_complete(parse_indicators_with_llm(extracted_text))
        indicators_saved = []
        if isinstance(result_text, list):
            for indicator in result_text:
                indicators_saved.append(indicator_service.save_indicator(db, indicator))
        else:
            indicators_saved.append(indicator_service.save_indicator(db, result_text))
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
        excel_path = INDICATOR_FILE_PATH_TEMPLATE.format(status_id)
        df.to_excel(excel_path, index=False)
        status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        if status_job:
            setattr(status_job, 'file', excel_path)
            setattr(status_job, 'status', IndicatorStatusEnum.COMPLETED.value)
            db.commit()
        else:
            logger.error(INDICATOR_STATUS_NOT_FOUND.format(status_id))
    except Exception as e:
        logger.error(INDICATOR_EXTRACT_ERROR.format(str(e)))
        status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        if status_job:
            setattr(status_job, 'status', IndicatorStatusEnum.ERROR.value)
            db.commit()

def get_indicator_status_controller(status_id: int, db: Session):
    status_job = db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
    if not status_job:
        raise HTTPException(status_code=404, detail="Indicator status not found")
    file_path = getattr(status_job, 'file', None)
    if isinstance(file_path, str) and file_path and os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type=INDICATOR_EXCEL_MEDIA_TYPE,
            filename=os.path.basename(file_path)
        )
    return status_job 
import os
import json
import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enums.indicator import IndicatorStatusEnum
from db import SessionLocal
from constants.indicator import (
    INDICATOR_EXTRACT_ERROR,
    INDICATOR_STATUS_NOT_FOUND,
    INDICATOR_FILE_PATH_TEMPLATE,
    INDICATOR_EXCEL_MEDIA_TYPE,
)
from services.indicator import IndicatorService
from models.indicator_status import IndicatorStatus
from utils.file_extraction import (
    extract_text_from_pdf_bytes,
    extract_text_from_docx_bytes,
)
from utils.indicator_parsing import parse_indicators_with_llm
import logging
from db import SessionLocal
import uuid

indicator_service = IndicatorService()
logger = logging.getLogger(__name__)


def start_indicator_extraction(
    background_tasks: BackgroundTasks, file: UploadFile, db: Session
):
    logger.info(f"Received file for indicator extraction: {file.filename}")
    if not file.filename or not file.filename.endswith((".pdf", ".docx")):
        logger.error(f"Unsupported file type: {file.filename}")
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX files are supported"
        )
    content = file.file.read()
    filename = file.filename
    status_job = indicator_service.create_status_job(db)
    status_id = int(getattr(status_job, "id"))
    logger.info(f"Created status job with ID: {status_id}")
    background_tasks.add_task(
        process_and_save_indicators_bg, content, filename, status_id
    )
    logger.info(f"Background task started for status ID: {status_id}")
    return {
        "status_id": status_id,
        "message": "Indicator extraction started. Check status with GET /indicators/extract/status/{status_id}",
    }


def process_and_save_indicators_bg(content: bytes, filename: str, status_id: int):
    logger.info(f"[Status {status_id}] Starting extraction for file: {filename}")
    try:
        if filename.endswith(".pdf"):
            logger.info(f"[Status {status_id}] Extracting text from PDF...")
            extracted_text = extract_text_from_pdf_bytes(content)
        elif filename.endswith(".docx"):
            logger.info(f"[Status {status_id}] Extracting text from DOCX...")
            extracted_text = extract_text_from_docx_bytes(content)
        else:
            logger.error(f"[Status {status_id}] Unsupported file type: {filename}")
            raise Exception("Unsupported file type or missing filename.")
        if not extracted_text:
            logger.error(f"[Status {status_id}] No readable text found in file.")
            raise Exception("No readable text found in file.")
        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"[Status {status_id}] Starting LLM indicator parsing...")
        result_text = loop.run_until_complete(parse_indicators_with_llm(extracted_text))
        logger.info(f"[Status {status_id}] LLM parsing complete.")
        data = []
        if isinstance(result_text, list):
            logger.info(
                f"[Status {status_id}] Extracted {len(result_text)} indicators from LLM."
            )
            for idx, indicator in enumerate(result_text):
                indicator_id = indicator.get("ID", f"IND{idx+1:03d}")
                indicator_text = indicator.get("Question", str(indicator))
                data.append({"Indicator ID": indicator_id, "Indicator": indicator_text})
        else:
            indicator_id = result_text.get("ID", "IND001")
            indicator_text = result_text.get("Question", str(result_text))
            data.append({"Indicator ID": indicator_id, "Indicator": indicator_text})
            logger.info(f"[Status {status_id}] Only one indicator extracted.")
        df = pd.DataFrame(data)
        os.makedirs("indicators", exist_ok=True)
        excel_path = INDICATOR_FILE_PATH_TEMPLATE.format(status_id)
        logger.info(
            f"[Status {status_id}] Saving extracted indicators to: {excel_path}"
        )
        df.to_excel(excel_path, index=False)
        # Only update status job, do not save indicators to DB
        from models.indicator_status import IndicatorStatus
        from enums.indicator import IndicatorStatusEnum
        from sqlalchemy.orm import Session

        db = SessionLocal()
        status_job = (
            db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        )
        if status_job:
            setattr(status_job, "file", excel_path)
            setattr(status_job, "status", IndicatorStatusEnum.COMPLETED.value)
            db.commit()
            logger.info(f"[Status {status_id}] Status updated to COMPLETED.")
        db.close()
    except Exception as e:
        logger.error(f"[Status {status_id}] {INDICATOR_EXTRACT_ERROR.format(str(e))}")
        from models.indicator_status import IndicatorStatus
        from enums.indicator import IndicatorStatusEnum
        from sqlalchemy.orm import Session

        db = SessionLocal()
        status_job = (
            db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        )
        if status_job:
            setattr(status_job, "status", IndicatorStatusEnum.ERROR.value)
            db.commit()
            logger.info(f"[Status {status_id}] Status updated to ERROR.")
        db.close()


def upload_indicators_from_excel(file: UploadFile, db: Session):
    import pandas as pd

    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")
    df = pd.read_excel(file.file)
    required_columns = {"Indicator ID", "Indicator"}
    if not required_columns.issubset(df.columns):
        raise HTTPException(
            status_code=400,
            detail="Excel must have columns: 'Indicator ID' and 'Indicator'",
        )
    process_id = str(uuid.uuid4())
    for _, row in df.iterrows():
        indicator_id = str(row["Indicator ID"]).strip()
        indicator = str(row["Indicator"]).strip()
        if indicator_id and indicator:
            indicator_service.save_indicator(
                db,
                {
                    "indicator_id": indicator_id,
                    "indicator": indicator,
                    "process_id": process_id,
                },
            )
    return {"message": "Indicators uploaded successfully.", "process_id": process_id}


def get_indicator_status_controller(status_id: int, db: Session):
    status_job = (
        db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
    )
    if not status_job:
        raise HTTPException(status_code=404, detail="Indicator status not found")
    file_path = getattr(status_job, "file", None)
    if isinstance(file_path, str) and file_path and os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type=INDICATOR_EXCEL_MEDIA_TYPE,
            filename=os.path.basename(file_path),
        )
    return status_job

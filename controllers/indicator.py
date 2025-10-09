import os
import json
import pandas as pd
from fastapi import BackgroundTasks, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enums.indicator import IndicatorStatusEnum
from db import SessionLocal
from utils.constants import (
    IndicatorMessages,
    IndicatorPaths,
    IndicatorMediaTypes,
)
from services.indicator import IndicatorService
from models.indicator_status import IndicatorStatus
from utils.parser.file import (
    extract_text_from_pdf_bytes,
    extract_text_from_docx_bytes,
)
from utils.parser.indicator import parse_indicators_with_llm
import logging
from db import SessionLocal
import uuid
from utils.cancel import cancel_registry

indicator_service = IndicatorService()
logger = logging.getLogger(__name__)


def _update_indicator_status(status_id: int, status: str, file_path: str = None):
    """Update indicator status with proper connection management."""
    from models.indicator_status import IndicatorStatus
    from enums.indicator import IndicatorStatusEnum
    
    db = SessionLocal()
    try:
        logger.info(f"🔌 Opening DB connection to update indicator status {status_id} to {status}")
        status_job = (
            db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        )
        if status_job:
            setattr(status_job, "status", status)
            if file_path:
                setattr(status_job, "file", file_path)
            db.commit()
            logger.info(f"✅ Updated indicator status {status_id} to {status}")
        else:
            logger.warning(f"⚠️ Indicator status {status_id} not found in database")
    except Exception as e:
        logger.error(f"❌ Failed to update indicator status: {e}")
        raise
    finally:
        db.close()
        logger.info("🔌 Database connection closed after updating indicator status")


def _get_indicator_status(status_id: int) -> dict:
    """Get indicator status with proper connection management."""
    from models.indicator_status import IndicatorStatus
    
    db = SessionLocal()
    try:
        logger.info(f"🔌 Opening DB connection to check indicator status {status_id}")
        status_job = (
            db.query(IndicatorStatus).filter(IndicatorStatus.id == status_id).first()
        )
        if status_job:
            status = str(getattr(status_job, "status", ""))
            file_path = str(getattr(status_job, "file", ""))
            logger.info(f"✅ Indicator status {status_id}: {status}")
            return {
                "id": status_job.id,
                "status": status,
                "file": file_path
            }
        else:
            logger.warning(f"⚠️ Indicator status {status_id} not found")
            return None
    except Exception as e:
        logger.error(f"❌ Failed to get indicator status: {e}")
        raise
    finally:
        db.close()
        logger.info("🔌 Database connection closed after checking indicator status")


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
        # Check cancellation early (no DB needed)
        if cancel_registry.is_cancelled("indicator", status_id):
            logger.info(f"[Status {status_id}] Cancelled before start")
            return

        # Extract text from file (no DB needed)
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

        # Process with LLM (no DB needed)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.info(f"[Status {status_id}] Starting LLM indicator parsing...")
        result_text = loop.run_until_complete(parse_indicators_with_llm(extracted_text, status_id=status_id))
        logger.info(f"[Status {status_id}] LLM parsing complete.")
        
        if cancel_registry.is_cancelled("indicator", status_id):
            logger.info(f"[Status {status_id}] Cancelled after LLM parsing")
            return

        # Process results (no DB needed)
        data = []
        if isinstance(result_text, list):
            logger.info(f"[Status {status_id}] Extracted {len(result_text)} indicators from LLM.")
            for idx, indicator in enumerate(result_text):
                indicator_id = indicator.get("ID", f"IND{idx+1:03d}")
                indicator_text = indicator.get("Question", str(indicator))
                data.append({"Indicator ID": indicator_id, "Indicator": indicator_text})
        else:
            indicator_id = result_text.get("ID", "IND001")
            indicator_text = result_text.get("Question", str(result_text))
            data.append({"Indicator ID": indicator_id, "Indicator": indicator_text})
            logger.info(f"[Status {status_id}] Only one indicator extracted.")

        # Save to Excel (no DB needed)
        df = pd.DataFrame(data)
        from core.config import settings
        indicators_dir = os.path.join(settings.STORAGE_ROOT, "indicators")
        os.makedirs(indicators_dir, exist_ok=True)
        excel_path = IndicatorPaths.FILE_PATH_TEMPLATE.value.format(status_id)
        logger.info(f"[Status {status_id}] Saving extracted indicators to: {excel_path}")
        df.to_excel(excel_path, index=False)

        # Update status in database (open/close DB connection)
        _update_indicator_status(status_id, "completed", excel_path)
        logger.info(f"[Status {status_id}] Status updated to COMPLETED.")

    except Exception as e:
        logger.error(f"[Status {status_id}] {IndicatorMessages.EXTRACT_ERROR.value.format(str(e))}")
        # Update status to error (open/close DB connection)
        _update_indicator_status(status_id, "error")
        logger.info(f"[Status {status_id}] Status updated to ERROR.")


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
    """Get indicator status with proper connection management."""
    status_data = _get_indicator_status(status_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Indicator status not found")
    
    file_path = status_data.get("file")
    if isinstance(file_path, str) and file_path and os.path.exists(file_path):
        return FileResponse(
            file_path,
            media_type=IndicatorMediaTypes.EXCEL.value,
            filename=os.path.basename(file_path),
        )
    
    # Return status data as object-like structure for compatibility
    class StatusObject:
        def __init__(self, data):
            self.id = data["id"]
            self.status = data["status"]
            self.file = data["file"]
    
    return StatusObject(status_data)

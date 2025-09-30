import logging
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Depends,
    Form,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.report import (
    start_report_generation,
    get_report_status_and_file_controller,
)
from services.report import ReportService
from utils.security import get_current_user
from utils.cancel import cancel_registry
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/report", tags=["report"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate", dependencies=[Depends(get_current_user)])
async def request_report_generation(
    background_tasks: BackgroundTasks,
    excel_file: UploadFile = File(
        ..., description="Excel file containing analysis results"
    ),
    sustainability_framework: str = Form(
        "User Standard (version 1.0, 2024)", description="Sustainability framework name, version and year"
    ),
    legal_framework: str = Form(
        "Legal Framework", description="Relevant legal framework"
    ),
    db: Session = Depends(get_db),
):
    """
    Submit an Excel file for report generation.
    Processing is done in the background.
    Returns report_id to track status.
    """
    try:
        return await start_report_generation(
            background_tasks,
            excel_file,
            db,
            sustainability_framework,
            legal_framework,
        )
    except Exception as e:
        logger.error(f"Error starting report generation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start report generation")


@router.get("/{report_id}/status", dependencies=[Depends(get_current_user)])
async def get_report_status(report_id: int, db: Session = Depends(get_db)):
    """
    Get the status of a report by ID.
    Returns status and download link if completed.
    """
    try:
        return await get_report_status_and_file_controller(db, report_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report status for ID {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get report status")


@router.post("/{report_id}/cancel", dependencies=[Depends(get_current_user)])
def cancel_report(report_id: int):
    cancel_registry.cancel("report", report_id)
    return {"message": f"Cancellation requested for report {report_id}"}


@router.get("/{report_id}/download", dependencies=[Depends(get_current_user)])
async def download_report_file(report_id: int, db: Session = Depends(get_db)):
    """
    Download the generated report file by ID.
    """
    try:
        report_service = ReportService()
        file_path = await report_service.get_report_file_for_download(db, report_id)
        if isinstance(file_path, str) and file_path and os.path.exists(file_path):
            # Determine media type based on file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext == '.docx':
                media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file_ext == '.xlsx':
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                media_type = "application/octet-stream"
                
            return FileResponse(
                file_path,
                media_type=media_type,
                filename=os.path.basename(file_path),
            )
        raise HTTPException(status_code=404, detail="Report file not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report file for ID {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download report file")

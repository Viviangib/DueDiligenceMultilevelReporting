from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services.report import ReportService
from enums.report import ReportStatus
import logging
import os

logger = logging.getLogger(__name__)

async def start_report_generation(
    background_tasks: BackgroundTasks,
    excel_file: UploadFile,
    db: Session,
    standard_name: str,
    standard_version: str,
    standard_year: str,
    organization: str,
):
    """
    Start background report generation process.
    """
    report_service = ReportService()
    
    try:
        # Validate file
        if not excel_file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Create report record first
        report = report_service.create_report_record(db)
        # Safely extract the id value from the instance
        report_id = report.__dict__.get("id")
        if not isinstance(report_id, int):
            raise RuntimeError(f"Failed to create report record: id is not an int, got {type(report_id)}")
        if report_id is None:
            raise RuntimeError("Failed to create report record: id is None")
        
        # Save uploaded file temporarily
        temp_file_path = await report_service.save_temp_file(excel_file)

        # Start background task
        background_tasks.add_task(
            report_service.generate_and_save_report,
            report_id,
            temp_file_path,
            standard_name,
            standard_version,
            standard_year,
            organization,
        )
        
        return {
            "report_id": report_id,
            "status": ReportStatus.IN_PROGRESS.value,
            "message": "Report generation started. Use GET /report/{report_id}/status to check progress."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting report generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start report generation: {str(e)}")

async def get_report_status_and_file_controller(db: Session, report_id: int):
    """
    Get report status and return the file if available and completed.
    """
    report_service = ReportService()
    
    try:
        report = report_service.get_report_by_id(db, report_id)
        logger.info(f"[GET] Looking for report_id={report_id}, found: {report}")
        if not report:
            logger.error(f"Report {report_id} not found in DB")
            raise HTTPException(status_code=404, detail="Report not found")
        
        status_value = getattr(report, 'status', 'unknown')
        file_path = getattr(report, 'file', None)
        
        # If the report is completed and the file exists, return the file
        if status_value == ReportStatus.COMPLETED.value and isinstance(file_path, str) and file_path and os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename=os.path.basename(file_path),
            )
        
        # Otherwise, return the status information
        abs_file_path = os.path.abspath(file_path) if file_path else None
        logger.info(f"[GET] Report {report_id} status: {status_value}, file: {file_path}, abs: {abs_file_path}")
        response_data = {
            "report_id": getattr(report, 'id'),
            "status": status_value,
            "created_at": getattr(report, 'created_at').isoformat() if hasattr(report, 'created_at') and getattr(report, 'created_at') else None,
        }
        
        if status_value == ReportStatus.COMPLETED.value:
            if abs_file_path and os.path.exists(abs_file_path):
                response_data.update({
                    "download_url": f"/report/{report_id}/status",
                    "filename": os.path.basename(abs_file_path),
                    "message": "Report is ready for download"
                })
            else:
                logger.error(f"[GET] Report {report_id} status is COMPLETED but file is missing: {abs_file_path}")
                response_data.update({
                    "message": "Report completed but file not found on server"
                })
                report_service.update_report_status(db, report_id, ReportStatus.ERROR.value)
                response_data["status"] = ReportStatus.ERROR.value
        elif status_value == ReportStatus.IN_PROGRESS.value:
            response_data["message"] = "Report generation in progress"
        elif status_value == ReportStatus.ERROR.value:
            response_data["message"] = "Report generation failed"
        else:
            response_data["message"] = "Unknown status"
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting report status for ID {report_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get report status")
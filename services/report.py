"""
Report service for generating and managing reports.
"""
import os
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from db import SessionLocal
from typing import Optional, Dict, Any
from enums.report import ReportStatus

# Import helper modules
from helpers.report.files import save_temp_file, cleanup_temp_file
from helpers.report.database import create_report_record, get_report_by_id, update_report_status
from helpers.report.processors import generate_report_from_data, convert_markdown_to_docx, prepare_report_data_from_excel

logger = logging.getLogger(__name__)

# Import constants
from utils.constants import ReportMediaTypes


class ReportService:
    """Service for managing report generation and operations."""
    
    async def save_temp_file(self, upload_file: UploadFile) -> str:
        """Save uploaded file to temporary directory."""
        return await save_temp_file(upload_file)

    def create_report_record(self, db: Session) -> Any:
        """Create a new report record in the database."""
        return create_report_record(db)

    def get_report_by_id(self, db: Session, report_id: int) -> Optional[Any]:
        """Get report by ID from database."""
        return get_report_by_id(db, report_id)

    def update_report_status(
        self, db: Session, report_id: int, status: str, file_path: Optional[str] = None
    ):
        """Update report status in database."""
        update_report_status(db, report_id, status, file_path)

    async def generate_and_save_report(
        self,
        report_id: int,
        temp_file_path: str,
        sustainability_framework: str,
        legal_framework: str,
    ):
        """Generate and save report from uploaded file."""
        db = SessionLocal()
        try:
            self.update_report_status(db, report_id, ReportStatus.IN_PROGRESS.value)
            logger.info(
                f"Starting report generation for report {report_id} from file: {temp_file_path}"
            )
            
            # Prepare data from Excel file
            analysis_data, num_indicators = prepare_report_data_from_excel(temp_file_path)
            
            # Generate report content
            final_report = await generate_report_from_data(
                analysis_data, num_indicators, sustainability_framework, legal_framework
            )
            
            if not final_report.strip():
                raise Exception("GPT returned an empty response.")
            
            # Convert to DOCX and save
            report_file_path = convert_markdown_to_docx(final_report)
            
            # Update database with the DOCX file path
            logger.info(f"Updating database with DOCX file path: {report_file_path}")
            self.update_report_status(
                db, report_id, ReportStatus.COMPLETED.value, report_file_path
            )
            
            logger.info(f"Report {report_id} generated successfully and status set to COMPLETED")
            
        except Exception as e:
            logger.error(f"Report generation failed for report {report_id}: {str(e)}")
            self.update_report_status(db, report_id, ReportStatus.ERROR.value)
        finally:
            cleanup_temp_file(temp_file_path)
            db.close()

    async def get_report_status_and_file(
        self, db: Session, report_id: int
    ) -> Dict[str, Any]:
        """Get report status and file information."""
        report = self.get_report_by_id(db, report_id)
        logger.info(f"[GET] Looking for report_id={report_id}, found: {report}")
        
        if not report:
            logger.error(f"Report {report_id} not found in DB")
            raise HTTPException(status_code=404, detail="Report not found")
        
        status_value = getattr(report, "status", "unknown")
        file_path = getattr(report, "file", None)
        abs_file_path = os.path.abspath(file_path) if file_path else None
        
        logger.info(
            f"[GET] Report {report_id} status: {status_value}, file: {file_path}, abs: {abs_file_path}"
        )
        
        response_data = {
            "report_id": getattr(report, "id"),
            "status": status_value,
            "created_at": (
                getattr(report, "created_at").isoformat()
                if hasattr(report, "created_at") and getattr(report, "created_at")
                else None
            ),
        }
        
        if status_value == ReportStatus.COMPLETED.value:
            if abs_file_path and os.path.exists(abs_file_path):
                response_data.update(
                    {
                        "download_url": f"/report/{report_id}/download",
                        "filename": os.path.basename(abs_file_path),
                        "message": "Report is ready for download",
                    }
                )
            else:
                logger.error(
                    f"[GET] Report {report_id} status is COMPLETED but file is missing: {abs_file_path}"
                )
                response_data.update(
                    {"message": "Report completed but file not found on server"}
                )
                self.update_report_status(db, report_id, ReportStatus.ERROR.value)
                response_data["status"] = ReportStatus.ERROR.value
        elif status_value == ReportStatus.IN_PROGRESS.value:
            response_data["message"] = "Report generation in progress"
        elif status_value == ReportStatus.ERROR.value:
            response_data["message"] = "Report generation failed"
        else:
            response_data["message"] = "Unknown status"
        
        return response_data

    async def get_report_file_for_download(self, db: Session, report_id: int) -> str:
        """Get report file path for download."""
        report = self.get_report_by_id(db, report_id)
        if not report:
            logger.error(f"Report {report_id} not found for download")
            raise HTTPException(status_code=404, detail="Report not found")
        
        status_value = getattr(report, "status", "unknown")
        file_path = getattr(report, "file", None)
        abs_file_path = os.path.abspath(file_path) if file_path else None

        if status_value != ReportStatus.COMPLETED.value:
            logger.error(
                f"Report {report_id} is not ready for download (status: {status_value})"
            )
            raise HTTPException(
                status_code=400, detail="Report is not ready for download"
            )

        if not abs_file_path or not os.path.exists(abs_file_path):
            logger.error(
                f"Report {report_id} file not found for download: {abs_file_path}"
            )
            raise HTTPException(status_code=404, detail="Report file not found")

        return abs_file_path
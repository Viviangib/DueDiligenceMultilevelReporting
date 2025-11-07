"""
Database operations for report management.
"""
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models.report import Report
from enums.report import ReportStatus

logger = logging.getLogger(__name__)


def create_report_record(db: Session) -> Report:
    """Create a new report record in the database."""
    try:
        report = Report(status=ReportStatus.IN_PROGRESS.value)
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Created report record with id: {report.id}")
        return report
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating report record: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Failed to create report record"
        )


def get_report_by_id(db: Session, report_id: int) -> Report | None:
    """Get report by ID from database."""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        logger.info(
            f"get_report_by_id: Looked up report_id={report_id}, found: {report}"
        )
        return report
    except Exception as e:
        logger.error(f"Error getting report {report_id}: {str(e)}")
        return None


def update_report_status(
    db: Session, report_id: int, status: str, file_path: str | None = None
):
    """Update report status in database."""
    try:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            logger.info(
                f"Updating report {report_id} status to {status} (file: {file_path})"
            )
            setattr(report, "status", status)
            if file_path:
                setattr(report, "file", file_path)
            db.commit()
            db.refresh(report)
            logger.info(f"Report {report_id} status updated and committed.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating report {report_id} status: {str(e)}")
        raise

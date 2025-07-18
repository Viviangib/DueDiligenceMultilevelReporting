from sqlalchemy.orm import Session
from services.regulation import RegulationService
import asyncio
import logging

logger = logging.getLogger(__name__)

regulation_service = RegulationService()


def create_regulation(db: Session, name: str, file_type: str):
    """Create a new regulation entry using the service layer."""
    return regulation_service.create_regulation(db, name, file_type)


def process_regulation(db: Session, file_path: str, reg_id: int):
    """Process a regulation file asynchronously using the service layer."""
    try:
        regulation_service.process_regulation(db, file_path, reg_id)
        logger.info(f"Regulation processing completed for regulation_id={reg_id}")
    except Exception as e:
        logger.error(f"Regulation processing failed for regulation_id={reg_id}: {e}")


def get_regulation_status(db: Session, regulation_id: int):
    """Get the embedding status of a regulation."""
    regulation = regulation_service.get_regulation(db, regulation_id)
    if not regulation:
        return "not found"
    return str(getattr(regulation, "embedding_status", "not found"))


def get_regulation_status_controller(regulation_id: int, db: Session):
    status = get_regulation_status(db, regulation_id)
    logger.info(
        f"Checked regulation status for regulation_id={regulation_id}: {status}"
    )
    return status

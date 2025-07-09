from sqlalchemy.orm import Session
from services.regulation import RegulationService
import asyncio

regulation_service = RegulationService()

def create_regulation(db: Session, name: str, file_type: str):
    """Create a new regulation entry using the service layer."""
    return regulation_service.create_regulation(db, name, file_type)

def process_regulation(db: Session, file_path: str, regulation_id: int):
    """Process a regulation file asynchronously using the service layer."""
    return regulation_service.process_regulation(db, file_path, regulation_id)

def get_regulation_status(db: Session, regulation_id: int):
    """Get the embedding status of a regulation."""
    regulation = regulation_service.get_regulation(db, regulation_id)
    if not regulation:
        return "not found"
    return str(getattr(regulation, 'embedding_status', 'not found'))



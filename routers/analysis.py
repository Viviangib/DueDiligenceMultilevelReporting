import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.analysis import (
    start_analysis_extraction,
    get_analysis_status_controller,
)
from schemas.analysis import AnalysisOut

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/run")
def run_analysis(
    background_tasks: BackgroundTasks,
    vss_files: list[UploadFile] = File(...),
    process_id: str = File(...),
    db: Session = Depends(get_db),
):
    return start_analysis_extraction(background_tasks, vss_files, process_id, db)

@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    return get_analysis_status_controller(analysis_id, db)
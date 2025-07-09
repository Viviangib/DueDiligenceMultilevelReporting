from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.indicator import (
    start_indicator_extraction,
    get_indicator_status_controller,
)

router = APIRouter(prefix="/indicators", tags=["indicators"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/extract")
def extract_indicators(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    return start_indicator_extraction(background_tasks, file, db)

@router.get("/extract/status/{status_id}")
def get_indicator_status(
    status_id: int,
    db: Session = Depends(get_db)
):
    return get_indicator_status_controller(status_id, db)

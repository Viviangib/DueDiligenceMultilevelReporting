from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.indicator import (
    start_indicator_extraction,
    get_indicator_status_controller,
)
from db.db import get_db
from utils.security import get_current_user

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.post("/extract", dependencies=[Depends(get_current_user)])
def extract_indicators(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return start_indicator_extraction(background_tasks, file, db)


@router.get("/extract/status/{status_id}", dependencies=[Depends(get_current_user)])
def get_indicator_status(status_id: int, db: Session = Depends(get_db)):
    return get_indicator_status_controller(status_id, db)


@router.post("/upload", dependencies=[Depends(get_current_user)])
def upload_indicators(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from controllers.indicator import upload_indicators_from_excel

    return upload_indicators_from_excel(file, db)

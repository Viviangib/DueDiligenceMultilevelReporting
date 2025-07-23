import logging
import os
import uuid
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Depends,
    Form,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.analysis import (
    start_analysis_extraction,
    get_analysis_status_controller,
)
from schemas.analysis import AnalysisOut
from utils.security import get_current_user

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


@router.post("/run", dependencies=[Depends(get_current_user)])
def run_analysis(
    background_tasks: BackgroundTasks,
    vss_files: list[UploadFile] = File(...),
    process_id: str = File(...),
    namespace: str = Form(..., description="Pinecone namespace to use for RAG search"),
    db: Session = Depends(get_db),
):
    from vector_store.pinecone_store import namespace_exists

    if not namespace_exists(namespace):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail=f"Pinecone namespace '{namespace}' does not exist."
        )
    return start_analysis_extraction(
        background_tasks, vss_files, process_id, db, namespace
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisOut,
    dependencies=[Depends(get_current_user)],
)
def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    return get_analysis_status_controller(analysis_id, db)

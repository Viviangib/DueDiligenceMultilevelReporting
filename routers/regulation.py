from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    Form,
    BackgroundTasks,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.regulation import (
    create_regulation,
    process_regulation,
    get_regulation_status,
)
from schemas.regulation import RegulationStatus
from utils.security import get_current_user
import os

router = APIRouter(prefix="/regulations", tags=["regulations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload", dependencies=[Depends(get_current_user)])
def upload_regulation(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    from core.config import settings
    base_dir = settings.STORAGE_ROOT
    uploads_dir = os.path.join(base_dir, settings.UPLOADS_DIR)
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, file.filename)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    reg = create_regulation(
        db,
        str(file.filename),
        str(file.content_type) if file.content_type else "application/pdf",
    )
    reg_id = reg.__dict__.get("id", 0)

    background_tasks.add_task(process_regulation, db, file_path, reg_id)

    return {
        "message": "File uploaded, embeddings being created",
        "regulation_id": reg_id,
    }


@router.get(
    "/{regulation_id}/status",
    response_model=RegulationStatus,
    dependencies=[Depends(get_current_user)],
)
def check_status(regulation_id: int, db: Session = Depends(get_db)):
    status = get_regulation_status(db, regulation_id)

    if status == "not found":
        raise HTTPException(status_code=404, detail="Regulation not found")

    return {"regulation_id": regulation_id, "embedding_status": status}

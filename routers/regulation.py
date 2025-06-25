from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.regulation import create_regulation, process_regulation, get_regulation_status, extract_and_analyze_vss, save_analysis_to_excel
from schemas.regulation import RegulationStatus
from utils.security import get_current_user
import os
import uuid

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

    file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    reg = create_regulation(db, str(file.filename), str(file.content_type) if file.content_type else "application/pdf")
    reg_id = reg.__dict__.get('id', 0)

    background_tasks.add_task(process_regulation, db, file_path, reg_id)

    return {"message": "File uploaded, embeddings being created", "regulation_id": reg_id}

@router.get("/{regulation_id}/status", response_model=RegulationStatus, dependencies=[Depends(get_current_user)])

def check_status(
    regulation_id: int,
    db: Session = Depends(get_db)
):
    status = get_regulation_status(db, regulation_id)

    if status == "not found":
        raise HTTPException(status_code=404, detail="Regulation not found")

    return {"regulation_id": regulation_id, "embedding_status": status}

@router.post("/analysis/start", dependencies=[Depends(get_current_user)])

def start_analysis(
    vss_file: UploadFile = File(...),
    regulation_id: int = Form(...),
    db: Session = Depends(get_db)
):
    status = get_regulation_status(db, regulation_id)

    if status != "completed":
        raise HTTPException(status_code=400, detail="Regulation embeddings not ready")

    vss_file_path = f"vss_uploads/{uuid.uuid4()}_{vss_file.filename}"
    os.makedirs("vss_uploads", exist_ok=True)

    with open(vss_file_path, "wb") as f:
        f.write(vss_file.file.read())
    results = extract_and_analyze_vss(vss_file_path, regulation_id, db)

    if results is None:
        raise HTTPException(status_code=500, detail="Failed to analyze VSS document.")

    output_file = save_analysis_to_excel(results)

    if output_file is None:
        raise HTTPException(status_code=500, detail="Failed to generate Excel report.")

    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="benchmark_results.xlsx"
    ) 
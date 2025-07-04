import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from services.analysis import AnalysisService
from models.analysis import Analysis
from schemas.analysis import AnalysisOut
import os
import uuid
from fastapi.responses import StreamingResponse

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
    db: Session = Depends(get_db),
   
):
    logger.info(f"Starting analysis with {len(vss_files)} VSS files")
    vss_paths = []
    for i, file in enumerate(vss_files):
        logger.info(f"Processing file {i+1}/{len(vss_files)}: {file.filename}")
        if not file.filename:
            logger.error("File without filename received")
            raise HTTPException(status_code=400, detail="File must have a name")
        ext = os.path.splitext(file.filename)[1].lower()
        logger.info(f"File extension: {ext}")
        if ext not in [".pdf", ".docx"]:
            logger.error(f"Unsupported file type: {ext}")
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
        path = f"vss_uploads/{uuid.uuid4()}_{file.filename}"
        logger.info(f"Saving file to: {path}")
        os.makedirs("vss_uploads", exist_ok=True)
        with open(path, "wb") as f:
            content = file.file.read()
            f.write(content)
            logger.info(f"File saved successfully. Size: {len(content)} bytes")
        vss_paths.append(path)
    logger.info(f"All files saved. Total paths: {len(vss_paths)}")
    logger.info(f"File paths: {vss_paths}")
    # Create analysis job
    analysis_service = AnalysisService()
    analysis = analysis_service.create_analysis(db)
    analysis_id = int(getattr(analysis, 'id'))
    # Start background task
    background_tasks.add_task(analysis_service.run_analysis, db, vss_paths, analysis_id)
    logger.info(f"Background analysis task started for analysis_id={analysis_id}")
    return {"analysis_id": analysis_id, "message": "Analysis started. Check status with GET /analysis/{analysis_id}"}

@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis_status(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    status = str(getattr(analysis, 'status', ''))
    output_file = str(getattr(analysis, 'output_file', ''))
    if status == "completed" and output_file:
        logger.info(f"Analysis {analysis_id} completed. Returning file.")
        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="analysis_results.xlsx"
        )
    logger.info(f"Analysis {analysis_id} status: {status}")
    return analysis
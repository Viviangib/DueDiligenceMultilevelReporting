import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from services.analysis import AnalysisService
import os
import uuid

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
async def run_analysis(
    vss_files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"Starting analysis with {len(vss_files)} VSS files")
    
    # Save uploaded files
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
            content = await file.read()
            f.write(content)
            logger.info(f"File saved successfully. Size: {len(content)} bytes")
        
        vss_paths.append(path)
    
    logger.info(f"All files saved. Total paths: {len(vss_paths)}")
    logger.info(f"File paths: {vss_paths}")
    
    # Call the analysis service
    logger.info("Starting analysis service")
    try:
        output_file = await AnalysisService().run_analysis(db, vss_paths)
        logger.info(f"Analysis completed successfully. Output file: {output_file}")
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    logger.info("Returning Excel file response")
    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="analysis_results.xlsx"
    ) 
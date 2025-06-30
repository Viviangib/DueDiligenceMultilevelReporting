from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from utils.indicator_parser import (
    extract_text_from_pdf_bytes,
    extract_text_from_docx_bytes,
    parse_indicators_with_llm,
    save_to_docx
)
import uuid
import os
from pprint import pformat
from controllers.indicator import save_indicator_controller
from sqlalchemy.orm import Session
from db import SessionLocal
from fastapi import Depends


router = APIRouter(prefix="/indicators", tags=["indicators"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/extract")
async def extract_indicators(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    content = await file.read()
    if file.filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf_bytes(content)
    else:
        extracted_text = extract_text_from_docx_bytes(content)
    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text found in file.")
    result_text = await parse_indicators_with_llm(extracted_text)
    os.makedirs("llm_outputs", exist_ok=True)
    output_file = f"llm_outputs/extracted_indicators_{uuid.uuid4()}.docx"
    save_to_docx(pformat(result_text), output_file)
    # Save to DB
    if isinstance(result_text, list):
        indicator_records = [save_indicator_controller(db, item) for item in result_text]
    else:
        indicator_records = [save_indicator_controller(db, result_text)]
    return {
        "indicators": indicator_records,
        "file": FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="extracted_indicators.docx"
        )
    }

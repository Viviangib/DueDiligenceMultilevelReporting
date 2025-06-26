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

router = APIRouter(prefix="/indicators", tags=["indicators"])

@router.post("/extract")
async def extract_indicators(file: UploadFile = File(...)):
    if not file.filename.endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    content = await file.read()
    
    # Extract text depending on file type
    if file.filename.endswith(".pdf"):
        extracted_text = extract_text_from_pdf_bytes(content)
    else:
        extracted_text = extract_text_from_docx_bytes(content)

    if not extracted_text:
        raise HTTPException(status_code=400, detail="No readable text found in file.")

    # LLM extraction
    result_text = await parse_indicators_with_llm(extracted_text)

    # Save response to .docx for review
    os.makedirs("llm_outputs", exist_ok=True)
    output_file = f"llm_outputs/extracted_indicators_{uuid.uuid4()}.docx"
    save_to_docx(result_text, output_file)

    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="extracted_indicators.docx"
    )

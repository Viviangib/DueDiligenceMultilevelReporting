import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument
import io
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text = ""
    logger.info(f"Starting PDF extraction, file size: {len(file_bytes)} bytes")
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text( # pyright: ignore[reportAttributeAccessIssue]
                    "text"
                )  
        logger.info(f"PDF extraction successful, extracted {len(text)} characters")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
    return text


def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    text = ""
    logger.info(f"Starting DOCX extraction, file size: {len(file_bytes)} bytes")
    try:
        file_stream = io.BytesIO(file_bytes)
        doc = DocxDocument(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
        logger.info(f"DOCX extraction successful, extracted {len(text)} characters")
    except Exception as e:
        logger.error(f"DOCX extraction failed: {e}")
    return text

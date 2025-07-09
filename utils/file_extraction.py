import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument
import io

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text = ""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text("text") # pyright: ignore[reportAttributeAccessIssue]
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
    return text

def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    text = ""
    try:
        file_stream = io.BytesIO(file_bytes)
        doc = DocxDocument(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"❌ DOCX extraction failed: {e}")
    return text 
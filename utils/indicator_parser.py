import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument
from typing import List
from openai import AsyncOpenAI
from config import settings
from docx import Document as OutputDocx
import io

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    text = ""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    except Exception as e:
        print("PDF extraction failed:", e)
    return text

def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    text = ""
    try:
        file_stream = io.BytesIO(file_bytes)
        doc = DocxDocument(file_stream)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print("DOCX extraction failed:", e)
    return text

async def parse_indicators_with_llm(text: str) -> List[dict]:
    example_table = """
Example:

ID Question Answer Answer Options  
MS.YP8 Does the project have an Environmental and Social Impact Assessment (ESIA) in place? * (Single-select) Yes No No, but commit to

MS.1PV Does the project have a climate risk assessment in place that aligns with TCFD guidelines? * (Single-select) Yes No No, but commit to

---

Given the above text, extract all indicator entries from the following document. 
For each indicator, include:

- ID (optional if not available)
- Question
- Answer (if available)
- Answer Options (if available)

Respond in JSON list format.
"""

    full_prompt = example_table + "\n\nDocument Content:\n" + text[:4000]

    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": full_prompt}]
    )

    return response.choices[0].message.content.strip()

def save_to_docx(text: str, output_path: str):
    doc = OutputDocx()
    doc.add_paragraph(text)
    doc.save(output_path)

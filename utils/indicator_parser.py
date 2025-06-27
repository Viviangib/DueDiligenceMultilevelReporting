import fitz  # PyMuPDF for PDFs
from docx import Document as DocxDocument
from typing import List
from openai import AsyncOpenAI
from config import settings
from docx import Document as OutputDocx
import io
import json
import tiktoken
from utils.prompt import PROMPT_TEMPLATE

MAX_TOKENS = 5000


def chunk_text(text: str, max_tokens: int = MAX_TOKENS) -> List[str]:
    enc = tiktoken.encoding_for_model("gpt-4")
    tokens = enc.encode(text)
    chunks = []

    for i in range(0, len(tokens), max_tokens):
        chunk = tokens[i:i + max_tokens]
        chunks.append(enc.decode(chunk))

    print(f"📦 Split into {len(chunks)} chunks.")
    return chunks


client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    print("🔄 Starting PDF text extraction...")
    print(f"📊 PDF file size: {len(file_bytes)} bytes")
    
    text = ""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            print(f"📄 PDF has {len(doc)} pages")
            for page_num, page in enumerate(doc, 1):  # type: ignore
                page_text = page.get_text("text")
                text += page_text
                print(f"✅ Extracted text from page {page_num}: {len(page_text)} characters")
        
        print(f"✅ PDF extraction completed successfully!")
        print(f"📝 Total extracted text length: {len(text)} characters")
        print(f"🔤 First 200 characters: {text[:200]}...")
        
    except Exception as e:
        print(f"❌ PDF extraction failed: {e}")
    
    return text

def extract_text_from_docx_bytes(file_bytes: bytes) -> str:
    print("🔄 Starting DOCX text extraction...")
    print(f"📊 DOCX file size: {len(file_bytes)} bytes")
    
    text = ""
    try:
        file_stream = io.BytesIO(file_bytes)
        doc = DocxDocument(file_stream)
        
        print(f"📄 DOCX has {len(doc.paragraphs)} paragraphs")
        
        for para_num, para in enumerate(doc.paragraphs, 1):
            para_text = para.text + "\n"
            text += para_text
            if para.text.strip():  # Only log non-empty paragraphs
                print(f"✅ Extracted paragraph {para_num}: {len(para.text)} characters")
        
        print(f"✅ DOCX extraction completed successfully!")
        print(f"📝 Total extracted text length: {len(text)} characters")
        print(f"🔤 First 200 characters: {text[:200]}...")
        
    except Exception as e:
        print(f"❌ DOCX extraction failed: {e}")
    
    return text

async def parse_indicators_with_llm(text: str) -> List[dict]:
    import re

    chunks = chunk_text(text)
    all_indicators = []

    for i, chunk in enumerate(chunks, 1):
        print(f"🚀 Processing chunk {i}/{len(chunks)}...")
        prompt = PROMPT_TEMPLATE.format(chunk=chunk)

        try:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.choices[0].message.content
            print("\n\ncontent: ", content)
            if not content:
                continue

            match = re.search(r"\[\s*{.*?}\s*]", content, re.DOTALL)
            if not match:
                print(f"⚠️ Could not find valid JSON in chunk {i}")
                continue

            parsed = json.loads(match.group())
            print(f"✅ Extracted {len(parsed)} indicators from chunk {i}")
            all_indicators.extend(parsed)

        except Exception as e:
            print(f"❌ Error in chunk {i}: {e}")
            continue

    print(f"🎯 Total indicators extracted: {len(all_indicators)}")
    return all_indicators

        

def save_to_docx(text: str, output_path: str):
    print(f"💾 Saving text to DOCX: {output_path}")
    print(f"📝 Text length to save: {len(text)} characters")
    
    try:
        doc = OutputDocx()
        doc.add_paragraph(text)
        doc.save(output_path)
        print(f"✅ Successfully saved DOCX to: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save DOCX: {e}")

#
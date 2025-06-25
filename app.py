# import asyncio
# import os
# import re
# import uuid
# from datetime import datetime
# from typing import List, Dict

# import pandas as pd
# import pdfplumber
# from fastapi import FastAPI, UploadFile, File, HTTPException, Form
# from fastapi.responses import FileResponse
# from langchain_openai import OpenAIEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from openai import AsyncOpenAI
# from sqlalchemy import create_engine, Column, Integer, String, DateTime
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker

# # Configuration (replace with your actual keys)
# OPENAI_API_KEY = "your-openai-api-key"
# PINECONE_API_KEY = "your-pinecone-api-key"
# INDEX_NAME = "your-pinecone-index-name"
# DATABASE_URL = "postgresql://user:password@localhost/dbname"

# # Initialize FastAPI app
# app = FastAPI()

# # Initialize OpenAI client
# client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# # Database setup
# engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Base = declarative_base()

# class Regulation(Base):
#     __tablename__ = "regulations"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     file_type = Column(String, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     embedding_status = Column(String, default="in process")
#     pinecone_namespace = Column(String, unique=True)

# Base.metadata.create_all(bind=engine)

# # Embeddings setup
# embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", openai_api_key=OPENAI_API_KEY)

# # System prompt and alignment definitions
# system_prompt = """
# You are a helpful expert in law and ESG research. 
# Your users are asking questions about information contained in a sustainability-related regulation.
# You will be shown the users' questions, and relevant information from the regulation.
# Ensure your responses are factual and concise. 
# Avoid generating responses without a factual basis, and if you cannot find relevant data, communicate that.
# """
# alignment_def = {
#     "N/A": {"Definition": "This requirement in the regulation is not applicable...", "Implication": "In certain cases..."},
#     "0": {"Definition": "This requirement in the regulation is not included...", "Implication": "Need to be reviewed or included."},
#     "1": {"Definition": "The assessed standard includes requirements similar...", "Implication": "Some aspects are missing..."},
#     "2": {"Definition": "This requirement in the regulation is fully covered...", "Implication": "Considered to be covered..."},
#     "3": {"Definition": "This requirement in the regulation is equivalent...", "Implication": "Considered to be covered."}
# }

# # Helper functions
# def insert_regulation(name: str, file_type: str) -> int:
#     db = SessionLocal()
#     namespace = f"regulation_{uuid.uuid4()}"
#     regulation = Regulation(name=name, file_type=file_type, pinecone_namespace=namespace)
#     db.add(regulation)
#     db.commit()
#     regulation_id = regulation.id
#     db.close()
#     return regulation_id

# def update_embedding_status(regulation_id: int, status: str):
#     db = SessionLocal()
#     regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
#     if regulation:
#         regulation.embedding_status = status
#         db.commit()
#     db.close()

# def get_regulation_status(regulation_id: int) -> str:
#     db = SessionLocal()
#     regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
#     db.close()
#     return regulation.embedding_status if regulation else "not found"

# def get_regulation_namespace(regulation_id: int) -> str:
#     db = SessionLocal()
#     regulation = db.query(Regulation).filter(Regulation.id == regulation_id).first()
#     db.close()
#     return regulation.pinecone_namespace if regulation else None

# async def process_regulation_task(file_path: str, regulation_id: int):
#     try:
#         namespace = get_regulation_namespace(regulation_id)
#         with pdfplumber.open(file_path) as pdf:
#             text = "".join(page.extract_text() + "\n" for page in pdf.pages if page.extract_text())
        
#         text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
#         chunks = text_splitter.split_text(text)
        
#         PineconeVectorStore.from_texts(
#             texts=chunks,
#             embedding=embeddings,
#             index_name=INDEX_NAME,
#             namespace=namespace
#         )
#         update_embedding_status(regulation_id, "completed")
#     except Exception as e:
#         update_embedding_status(regulation_id, "failed")
#         print(f"Error processing regulation {regulation_id}: {e}")

# def extract_indicators(file_path: str) -> List[str]:
#     indicators = []
#     with pdfplumber.open(file_path) as pdf:
#         for page in pdf.pages:
#             text = page.extract_text()
#             if text and re.search(r'requirements|standards|criteria', text, re.IGNORECASE):
#                 sentences = re.split(r'(?<=[.!?])\s+', text)
#                 for sentence in sentences:
#                     if re.search(r'\b(shall|must|requires?)\b', sentence, re.IGNORECASE):
#                         indicators.append(sentence.strip())
#     return indicators

# async def analyze_indicator(indicator: str, regulation_namespace: str) -> Dict:
#     query_embedding = embeddings.embed_query(indicator)
#     vector_store = PineconeVectorStore.from_existing_index(
#         index_name=INDEX_NAME,
#         embedding=embeddings,
#         namespace=regulation_namespace
#     )
#     retriever = vector_store.as_retriever(search_kwargs={"k": 5})
#     evidence_docs = retriever.get_relevant_documents(indicator)
#     evidence = [doc.page_content for doc in evidence_docs]
    
#     prompt = f"""
#     {system_prompt}
#     Evaluate the following VSS indicator against the provided regulatory text to determine the level of alignment, using the categories: {alignment_def}. Provide a brief justification.

#     Indicator: {indicator}
#     Evidence: {evidence}
#     """
#     response = await client.chat.completions.create(
#         model="gpt-4o",
#         messages=[{"role": "user", "content": prompt}]
#     )
#     content = response.choices[0].message.content
#     # Simplified parsing (assumes LLM returns structured text)
#     alignment_level = content.split("Alignment Level:")[1].split("\n")[0].strip() if "Alignment Level:" in content else "N/A"
#     justification = content.split("Justification:")[1].strip() if "Justification:" in content else "No justification provided."
#     return {"alignment_level": alignment_level, "justification": justification, "evidence": evidence}

# # API Endpoints
# @app.post("/files/upload")
# async def upload_file(file: UploadFile = File(...)):
#     if not file.filename.endswith(".pdf"):
#         raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
#     file_path = f"uploads/{uuid.uuid4()}_{file.filename}"
#     os.makedirs("uploads", exist_ok=True)
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())
    
#     regulation_id = insert_regulation(file.filename, file.content_type)
#     asyncio.create_task(process_regulation_task(file_path, regulation_id))
    
#     return {"message": "File uploaded, embeddings being created", "regulation_id": regulation_id}

# @app.get("/regulations/{regulation_id}/status")
# async def check_status(regulation_id: int):
#     status = get_regulation_status(regulation_id)
#     if status == "not found":
#         raise HTTPException(status_code=404, detail="Regulation not found")
#     return {"regulation_id": regulation_id, "embedding_status": status}

# @app.post("/analysis/start")
# async def start_analysis(vss_file: UploadFile = File(...), regulation_id: int = Form(...)):
#     status = get_regulation_status(regulation_id)
#     if status != "completed":
#         raise HTTPException(status_code=400, detail="Regulation embeddings not ready")
    
#     vss_file_path = f"vss_uploads/{uuid.uuid4()}_{vss_file.filename}"
#     os.makedirs("vss_uploads", exist_ok=True)
#     with open(vss_file_path, "wb") as f:
#         f.write(vss_file.file.read())
    
#     indicators = extract_indicators(vss_file_path)
#     if not indicators:
#         raise HTTPException(status_code=400, detail="No indicators found in VSS document")
    
#     results = []
#     namespace = get_regulation_namespace(regulation_id)
#     for idx, indicator in enumerate(indicators):
#         analysis = await analyze_indicator(indicator, namespace)
#         results.append({
#             "Indicator ID": f"IND{idx+1:03d}",
#             "Indicator Text": indicator,
#             "Alignment Level": analysis["alignment_level"],
#             "Justification": analysis["justification"],
#             "Evidence": str(analysis["evidence"])
#         })
    
#     output_file = f"results/benchmark_results_{uuid.uuid4()}.xlsx"
#     os.makedirs("results", exist_ok=True)
#     pd.DataFrame(results).to_excel(output_file, index=False)
    
#     return FileResponse(output_file, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="benchmark_results.xlsx")
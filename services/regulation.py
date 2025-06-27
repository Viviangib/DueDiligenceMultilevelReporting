"""Service layer for regulation analysis."""

import os
import uuid
from typing import List, Dict, Optional
import pandas as pd
import pdfplumber
from fastapi import HTTPException
from sqlalchemy.orm import Session
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import AsyncOpenAI
from pydantic import SecretStr
import re


from models.regulation import Regulation, AnalysisResult
from config import settings
from vector_store.pinecone import embed_and_store_documents,chunk_text


class RegulationService:
    """Service for handling regulation analysis operations."""

    def __init__(self):
        """Initialize service with necessary clients."""
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
        self.embeddings =  OpenAIEmbeddings(model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY)

    def create_regulation(self, db: Session, name: str, file_type: str) -> Regulation:

        """Create a new regulation record."""
        namespace = settings.PINECONE_NAMESPACE
        regulation = Regulation(
            name=name,
            file_type=file_type,
            pinecone_namespace=namespace
        )
        db.add(regulation)
        db.commit()
        db.refresh(regulation)
        return regulation

    def get_regulation(self, db: Session, regulation_id: int) -> Optional[Regulation]:
        """Get regulation by ID."""
        return db.query(Regulation).filter(Regulation.id == regulation_id).first()

    def update_embedding_status(self, db: Session, regulation_id: int, status: str):
        """Update regulation embedding status."""
        regulation = self.get_regulation(db, regulation_id)
        if regulation:
            setattr(regulation, 'embedding_status', status)
            db.commit()

    def process_regulation(self, db: Session, file_path: str, regulation_id: int):
        try:
            regulation = self.get_regulation(db, regulation_id)
            if not regulation:
                raise Exception("Regulation not found")

            documents = []
            with pdfplumber.open(file_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    chunks = chunk_text(page_text)
                    for chunk_index, chunk in enumerate(chunks):
                        chunk.metadata = {
                            "page": page_number,
                            "chunk_index": chunk_index,
                            "regulation_id": regulation_id
                        }
                        documents.append(chunk)

            embed_and_store_documents(documents, str(regulation.pinecone_namespace))
            self.update_embedding_status(db, regulation_id, "completed")
        except Exception as e:
            self.update_embedding_status(db, regulation_id, "failed")
            raise Exception(str(e))

    # async def analyze_indicator(self, indicator: str, namespace: str) -> Dict:
    #     """Analyze a single indicator against regulation."""
    #     vector_store = PineconeVectorStore.from_existing_index(
    #         index_name=settings.PINECONE_INDEX_NAME,
    #         embedding=self.embeddings,
    #         namespace=namespace
    #     )
    #     retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    #     evidence_docs = retriever.get_relevant_documents(indicator)
    #     evidence = [doc.page_content for doc in evidence_docs]

    #     prompt = f"""
    #     {SYSTEM_PROMPT}
    #     Evaluate the following VSS indicator against the provided regulatory text to determine 
    #     the level of alignment, using the categories: {ALIGNMENT_DEF}. Provide a brief justification.

    #     Indicator: {indicator}
    #     Evidence: {evidence}
    #     """

    #     response = await self.openai_client.chat.completions.create(
    #         model="gpt-4",
    #         messages=[{"role": "user", "content": prompt}]
    #     )
    #     content = response.choices[0].message.content if response.choices and response.choices[0].message.content else ""

    #     alignment_level = content.split("Alignment Level:")[1].split("\n")[0].strip() \
    #         if "Alignment Level:" in content else "N/A"
    #     justification = content.split("Justification:")[1].strip() \
    #         if "Justification:" in content else "No justification provided."

    #     return {
    #         "alignment_level": alignment_level,
    #         "justification": justification,
    #         "evidence": evidence
    #     }

    def save_analysis_result(self, db: Session, regulation_id: int,
                           indicator_id: str, result: Dict) -> AnalysisResult:
        """Save analysis result to database."""
        analysis_result = AnalysisResult(
            regulation_id=regulation_id,
            indicator_id=indicator_id,
            indicator_text=result["indicator_text"],
            alignment_level=result["alignment_level"],
            justification=result["justification"],
            evidence=str(result["evidence"])
        )
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        return analysis_result

    def generate_excel_report(self, results: List[Dict], output_dir: str) -> str:
        """Generate Excel report from analysis results."""
        os.makedirs(output_dir, exist_ok=True)
        output_file = f"{output_dir}/benchmark_results_{uuid.uuid4()}.xlsx"

        df = pd.DataFrame(results)
        df.to_excel(output_file, index=False)

        return output_file

    # def extract_and_analyze_vss(self, file_path: str, regulation_id: int, db):
    #     indicators = extract_indicators_from_pdf(file_path)
    #     if not indicators:
    #         raise Exception("No indicators found in VSS document")
    #     regulation = self.get_regulation(db, regulation_id)
    #     namespace = str(getattr(regulation, 'pinecone_namespace', ''))
    #     results = []
    #     for idx, indicator in enumerate(indicators):
    #         # For demonstration, just return dummy alignment; replace with real analysis logic
    #         analysis = {"alignment_level": "N/A", "justification": "Not implemented", "evidence": []}
    #         results.append({
    #             "indicator_id": f"IND{idx+1:03d}",
    #             "indicator_text": indicator,
    #             "alignment_level": analysis["alignment_level"],
    #             "justification": analysis["justification"],
    #             "evidence": str(analysis["evidence"])
    #         })
    #     return results

    def save_analysis_to_excel(self, results: list) -> str:
        output_file = f"results/benchmark_results_{uuid.uuid4()}.xlsx"
        os.makedirs("results", exist_ok=True)
        pd.DataFrame(results).to_excel(output_file, index=False)
        return output_file
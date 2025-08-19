"""Service layer for regulation analysis."""

import os
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
import logging


from models.regulation import Regulation
from core.config import settings
from infrastructure.vectorstores.pinecone_index import embed_and_store_documents, chunk_text


logger = logging.getLogger(__name__)


class RegulationService:
    """Service for handling regulation analysis operations."""

    def __init__(self):
        """Initialize service with necessary clients."""
        self.openai_client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002", api_key=settings.OPENAI_API_KEY
        )

    def create_regulation(self, db: Session, name: str, file_type: str, namespace: str = None) -> Regulation:
        """Create a new regulation record."""
        # Use provided namespace or fall back to default from settings
        pinecone_namespace = namespace if namespace is not None else settings.PINECONE_NAMESPACE
        logger.info(f"Creating regulation with namespace: {pinecone_namespace} (provided: {namespace}, default: {settings.PINECONE_NAMESPACE})")
        regulation = Regulation(
            name=name, file_type=file_type, pinecone_namespace=pinecone_namespace
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
            setattr(regulation, "embedding_status", status)
            db.commit()

    def process_regulation(self, db: Session, file_path: str, regulation_id: int):
        try:
            regulation = self.get_regulation(db, regulation_id)
            if not regulation:
                raise Exception("Regulation not found")

            documents = []
            source_file = os.path.basename(file_path)  # Extract PDF filename
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)  # Get total number of pages
                logger.info(f"Processing PDF: {source_file}, Total pages: {total_pages}")
                for page_number, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    chunks = chunk_text(page_text)
                    for chunk_index, chunk in enumerate(chunks):
                        chunk.metadata = {
                            "page": page_number,
                            "chunk_index": chunk_index,
                            "regulation_id": regulation_id,
                            "source_file": source_file  
                        }
                        documents.append(chunk)

            embed_and_store_documents(documents, str(regulation.pinecone_namespace))
            self.update_embedding_status(db, regulation_id, "completed")
        except Exception as e:
            self.update_embedding_status(db, regulation_id, "failed")
            raise Exception(str(e))
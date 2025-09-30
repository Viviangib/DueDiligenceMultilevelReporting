"""
Analysis service for processing indicators with RAG and GPT.
"""
import logging
import pandas as pd
import os
import json
import datetime
from sqlalchemy.orm import Session
from models.indicator import Indicator
from models.analysis import Analysis
from utils.prompts import alignment_def
from services.openai import OpenAIClient
from core.config import settings
from utils.cancel import cancel_registry

# Import helper modules
from helpers.analysis.parsers import parse_analysis_response, format_gpt_response
from helpers.analysis.processors import process_rag_evidence_batch, process_gpt_per_indicator

logger = logging.getLogger(__name__)

openai_client = OpenAIClient(model="gpt-4o-mini")


class AnalysisService:
    """Service for running analysis on indicators using RAG and GPT."""
    
    def create_analysis(self, db: Session) -> Analysis:
        """Create a new analysis record."""
        analysis = Analysis(status="in_progress")
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Created new analysis job with id {analysis.id}")
        return analysis

    def update_analysis_status(
        self, db: Session, analysis_id: int, status: str, output_file: str = ""
    ):
        """Update analysis status in database."""
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            setattr(analysis, "status", status)
            if output_file:
                setattr(analysis, "output_file", output_file)
            db.commit()
            logger.info(f"Updated analysis {analysis_id} to status {status}")

    async def run_analysis(
        self,
        vss_paths: list[str],
        analysis_id: int,
        process_id: str,
        namespace: str,
    ) -> None:
        """Run the complete analysis process."""
        # Create a new database session for the background task
        from db import SessionLocal
        db = SessionLocal()
        
        try:
            start_time = datetime.datetime.now()
            logger.info(f"Starting analysis service at {start_time}")
            
            # Check cancellation early
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled before start")
                self.update_analysis_status(db, analysis_id, "error", "")
                return

            # Get indicators from database
            indicators = (
                db.query(Indicator).filter(Indicator.process_id == process_id).all()
            )
            if not indicators:
                raise Exception("No indicators found in DB for this process_id.")

            # Initialize and build VSS vector store
            await self._setup_vss_vector_store(vss_paths)

            # Process RAG evidence
            rag_results = await self._process_rag_evidence(indicators, namespace, start_time, analysis_id)
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled after RAG phase")
                self.update_analysis_status(db, analysis_id, "error", "")
                await self._cleanup()
                return

            # Process with GPT
            gpt_results = await self._process_with_gpt(rag_results, analysis_id)
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled during GPT phase")
                self.update_analysis_status(db, analysis_id, "error", "")
                await self._cleanup()
                return

            # Save results to Excel
            output_file = await self._save_results_to_excel(gpt_results)
            
            # Update analysis status
            self.update_analysis_status(db, analysis_id, "completed", output_file)
            
            # Cleanup
            await self._cleanup()
            
            end_time = datetime.datetime.now()
            logger.info(f"Analysis completed at {end_time}")
            logger.info(f"Total analysis duration: {end_time - start_time}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.update_analysis_status(db, analysis_id, "error", "")
            await self._cleanup_on_error()
            raise
        finally:
            db.close()
            logger.info("Database session closed")

    async def _setup_vss_vector_store(self, vss_paths: list[str]):
        """Initialize and build the VSS vector store."""
        from vectorstores.vss_faiss_store import InMemoryVSSVectorStore
        
        self.vss_vector_store = InMemoryVSSVectorStore()
        
        # Add all VSS documents to vector store
        await self.vss_vector_store.add_vss_documents(vss_paths)
        
        # Build the FAISS index
        await self.vss_vector_store.build_index()
        logger.info(f"Built VSS vector store with stats: {self.vss_vector_store.get_stats()}")

    async def _process_rag_evidence(self, indicators: list, namespace: str, start_time: datetime.datetime, analysis_id: int) -> list:
        """Process RAG evidence for all indicators."""
        from vectorstores.pinecone_retriever import RAGSearcher
        
        rag_searcher = RAGSearcher(namespace=namespace)
        
        # Process RAG evidence in batches
        rag_results = await process_rag_evidence_batch(
            indicators, rag_searcher, start_time, rag_batch_size=40, analysis_id=analysis_id
        )
        
        logger.info(f"RAG phase completed. Retrieved evidence for {len(rag_results)} indicators")
        return rag_results

    async def _process_with_gpt(self, rag_results: list, analysis_id: int) -> list:
        """Process indicators with GPT."""
        # Convert alignment_def to string if necessary
        alignment_def_str = (
            alignment_def
            if isinstance(alignment_def, str)
            else json.dumps(alignment_def)
        )
        logger.info(f"alignment_def type: {type(alignment_def)}, value: {alignment_def_str[:100]}")

        logger.info(f"Processing {len(rag_results)} indicators with improved rate limiting...")
        logger.info(f"RAG phase completed. Starting GPT processing phase...")
        
        gpt_results = await process_gpt_per_indicator(
            rag_results, alignment_def_str, self.vss_vector_store, openai_client, analysis_id=analysis_id
        )

        logger.info(f"GPT processing completed. Total indicators processed: {len(gpt_results)}")
        return gpt_results

    async def _save_results_to_excel(self, results: list) -> str:
        """Save analysis results to Excel file."""
        from core.config import settings
        
        output_dir = os.path.join(settings.STORAGE_ROOT, settings.ANALYSIS_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "llm_results.xlsx")

        # Prepare DataFrame with required columns and formatted GPT response
        data = []
        for row in results:
            data.append(
                {
                    "Indicator ID": row.get("Indicator ID", ""),
                    "Statement": row.get("STATEMENT", ""),
                    "Alignment Category": row.get("ALIGNMENT CATEGORY", ""),
                    "GPT Response": format_gpt_response(row),
                }
            )
        
        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False)
        logger.info(f"Results saved to {output_file}")
        return output_file

    async def _cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'vss_vector_store'):
            self.vss_vector_store.clear()
            logger.info("Cleared in-memory VSS vector store")

    async def _cleanup_on_error(self):
        """Clean up resources on error."""
        try:
            if hasattr(self, 'vss_vector_store'):
                self.vss_vector_store.clear()
                logger.info("Cleared in-memory VSS vector store on error")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup vector store: {cleanup_error}")
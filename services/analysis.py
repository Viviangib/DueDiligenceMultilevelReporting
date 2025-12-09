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

    async def _get_indicators_from_db(self, process_id: str) -> list:
        """Get indicators from database with proper connection management."""
        from db import SessionLocal
        db = SessionLocal()
        try:
            logger.info(f"🔌 Opening DB connection to fetch indicators for process_id: {process_id}")
            indicators = (
                db.query(Indicator).filter(Indicator.process_id == process_id).all()
            )
            logger.info(f"✅ Retrieved {len(indicators)} indicators from database")
            return indicators
        except Exception as e:
            logger.error(f"❌ Failed to fetch indicators from database: {e}")
            raise
        finally:
            db.close()
            logger.info("🔌 Database connection closed after fetching indicators")

    async def _update_analysis_status(self, analysis_id: int, status: str, output_file: str = ""):
        """Update analysis status with proper connection management."""
        from db import SessionLocal
        db = SessionLocal()
        try:
            logger.info(f"🔌 Opening DB connection to update analysis {analysis_id} status to {status}")
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                setattr(analysis, "status", status)
                if output_file:
                    setattr(analysis, "output_file", output_file)
                db.commit()
                logger.info(f"✅ Updated analysis {analysis_id} to status {status}")
            else:
                logger.warning(f"⚠️ Analysis {analysis_id} not found in database")
        except Exception as e:
            logger.error(f"❌ Failed to update analysis status: {e}")
            raise
        finally:
            db.close()
            logger.info("🔌 Database connection closed after updating analysis status")

    async def _get_analysis_status(self, analysis_id: int) -> dict:
        """Get analysis status with proper connection management."""
        from db import SessionLocal
        db = SessionLocal()
        try:
            logger.info(f"🔌 Opening DB connection to check analysis {analysis_id} status")
            analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if analysis:
                status = str(getattr(analysis, "status", ""))
                output_file = str(getattr(analysis, "output_file", ""))
                logger.info(f"✅ Analysis {analysis_id} status: {status}")
                return {
                    "id": analysis.id,
                    "status": status,
                    "output_file": output_file
                }
            else:
                logger.warning(f"⚠️ Analysis {analysis_id} not found")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to get analysis status: {e}")
            raise
        finally:
            db.close()
            logger.info("🔌 Database connection closed after checking analysis status")

    async def run_analysis(
        self,
        vss_paths: list[str],
        analysis_id: int,
        process_id: str,
        namespace: str,
    ) -> None:
        """Run the complete analysis process with proper DB connection management."""
        start_time = datetime.datetime.now()
        logger.info(f"Starting analysis service at {start_time}")
        
        # Store vss_paths for cleanup
        self.vss_paths = vss_paths
        
        try:
            # Check cancellation early (no DB needed)
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled before start")
                await self._update_analysis_status(analysis_id, "error", "")
                return

            # Get indicators from database (open/close DB connection)
            indicators = await self._get_indicators_from_db(process_id)
            if not indicators:
                raise Exception("No indicators found in DB for this process_id.")
            
            # Limit to first 50 indicators for analysis
            # if len(indicators) > 50:
            #     logger.info(f"Limiting analysis to first 50 indicators out of {len(indicators)} total indicators")
            #     indicators = indicators[:50]

            # Initialize and build VSS vector store (no DB needed)
            await self._setup_vss_vector_store(vss_paths)

            # Process RAG evidence (no DB needed)
            rag_results = await self._process_rag_evidence(indicators, namespace, start_time, analysis_id)
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled after RAG phase")
                await self._update_analysis_status(analysis_id, "error", "")
                await self._cleanup()
                return

            # Process with GPT (no DB needed)
            gpt_results = await self._process_with_gpt(rag_results, analysis_id)
            if cancel_registry.is_cancelled("analysis", analysis_id):
                logger.info(f"Analysis {analysis_id} cancelled during GPT phase")
                await self._update_analysis_status(analysis_id, "error", "")
                await self._cleanup()
                return

            # Save results to Excel (no DB needed)
            output_file = await self._save_results_to_excel(gpt_results, indicators)
            
            # Update analysis status (open/close DB connection)
            await self._update_analysis_status(analysis_id, "completed", output_file)
            
            # Cleanup
            await self._cleanup()
            
            end_time = datetime.datetime.now()
            logger.info(f"Analysis completed at {end_time}")
            logger.info(f"Total analysis duration: {end_time - start_time}")
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            await self._update_analysis_status(analysis_id, "error", "")
            await self._cleanup_on_error()
            raise

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
    
        logger.info(f"Processing {len(rag_results)} indicators with improved rate limiting...")
        logger.info(f"RAG phase completed. Starting GPT processing phase...")
        
        gpt_results = await process_gpt_per_indicator(
            rag_results, alignment_def_str, self.vss_vector_store, openai_client, analysis_id=analysis_id
        )

        logger.info(f"GPT processing completed. Total indicators processed: {len(gpt_results)}")
        return gpt_results

    async def _save_results_to_excel(self, results: list, original_indicators: list) -> str:
        """Save analysis results to Excel file."""
        from core.config import settings
        
        output_dir = os.path.join(settings.STORAGE_ROOT, settings.ANALYSIS_OUTPUT_DIR)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "llm_results.xlsx")

        # Create a mapping of indicator_id to original indicator text
        indicator_text_map = {ind.indicator_id: ind.indicator for ind in original_indicators}
        
        # Prepare DataFrame with required columns and formatted GPT response
        data = []
        for row in results:
            indicator_id = row.get("Indicator ID", "")
            original_indicator_text = indicator_text_map.get(indicator_id, "")
            
            data.append(
                {
                    "Indicator": original_indicator_text,
                    "Indicator ID": indicator_id,
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
        
        # Clean up VSS files after analysis is complete
        if hasattr(self, 'vss_paths'):
            await self._cleanup_vss_files(self.vss_paths)
    
    async def _cleanup_vss_files(self, vss_paths: list[str]):
        """Clean up VSS files after processing."""
        import os
        for file_path in vss_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up VSS file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup VSS file {file_path}: {e}")

    async def _cleanup_on_error(self):
        """Clean up resources on error."""
        try:
            if hasattr(self, 'vss_vector_store'):
                self.vss_vector_store.clear()
                logger.info("Cleared in-memory VSS vector store on error")
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup vector store: {cleanup_error}")
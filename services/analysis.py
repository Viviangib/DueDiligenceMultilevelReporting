import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.prompts.alignment import alignment_def
from utils.prompts.analysis import analysis_prompt
from infrastructure.vectorstores.pinecone_retriever import rag_searcher
from openai import AsyncOpenAI, RateLimitError
import os
import re
import json
from models.analysis import Analysis
from typing import List, Dict, Any, Tuple
import asyncio
import datetime
from infrastructure.openai.client import OpenAIClient
import tiktoken
from core.config import settings


# Configure logging
logger = logging.getLogger(__name__)

openai_client = OpenAIClient(model="gpt-4o-mini")
# Using string-based prompts



def format_numbered_items(text: str) -> str:
    """
    SIMPLE post-processing: ONLY adds line breaks before existing numbered items.
    Does NOT modify any content or add numbers - just ensures proper line spacing.
    """
    if not text or not text.strip():
        return text
    
    # Don't process if already has good line breaks
    if '\n(' in text:
        return text
    
    # VERY SIMPLE: Just add a line break before each " (number)" pattern
    # This only affects spacing, not content
    formatted_text = re.sub(r'(\s)(\(\d+\))', r'\n\2', text)
    
    # Clean up any leading line break
    formatted_text = formatted_text.lstrip('\n')
    
    return formatted_text.strip()


def parse_analysis_response(response: str) -> Dict[str, str]:
    try:
        # Clean the response by removing asterisks and extra whitespace
        cleaned_response = re.sub(r'\*+', '', response)  # Remove all asterisks
        cleaned_response = re.sub(r'\s+', ' ', cleaned_response)  # Normalize whitespace
        
        # Updated pattern to handle numbered format (1. STATEMENT:, 2. EVIDENCE:, etc.)
        pattern = r"(?:1\.\s*)?STATEMENT:\s*(.*?)\s*(?:2\.\s*)?EVIDENCE:\s*(.*?)\s*(?:3\.\s*)?CITATIONS:\s*(.*?)\s*(?:4\.\s*)?ALIGNMENT\s+CATEGORY:\s*(.*?)\s*(?:5\.\s*)?JUSTIFICATION:\s*(.*?)$"
        match = re.search(pattern, cleaned_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Apply post-processing to format numbered items
            raw_evidence = match.group(2).strip()
            raw_citations = match.group(3).strip()
            
            evidence = format_numbered_items(raw_evidence)
            citations = format_numbered_items(raw_citations)
            
            logger.info(f"Post-processing applied - Evidence items: {evidence.count('(')}, Citations items: {citations.count('(')}")
            
            return {
                "STATEMENT": match.group(1).strip(),
                "EVIDENCE": evidence,
                "CITATIONS": citations,
                "ALIGNMENT CATEGORY": match.group(4).strip(),
                "JUSTIFICATION": match.group(5).strip(),
            }
        else:
            # Fallback: try original pattern and numbered pattern
            pattern_fallback = r"(?:1\.\s*)?STATEMENT:(.*?)(?:2\.\s*)?EVIDENCE:(.*?)(?:3\.\s*)?CITATIONS:(.*?)(?:4\.\s*)?ALIGNMENT\s+CATEGORY:(.*?)(?:5\.\s*)?JUSTIFICATION:(.*)"
            match_fallback = re.search(pattern_fallback, response, re.DOTALL | re.IGNORECASE)
            if match_fallback:
                # Apply post-processing to format numbered items
                raw_evidence = re.sub(r'\*+', '', match_fallback.group(2)).strip()
                raw_citations = re.sub(r'\*+', '', match_fallback.group(3)).strip()
                
                evidence = format_numbered_items(raw_evidence)
                citations = format_numbered_items(raw_citations)
                
                logger.info(f"Fallback post-processing applied - Evidence items: {evidence.count('(')}, Citations items: {citations.count('(')}")
                
                return {
                    "STATEMENT": re.sub(r'\*+', '', match_fallback.group(1)).strip(),
                    "EVIDENCE": evidence,
                    "CITATIONS": citations,
                    "ALIGNMENT CATEGORY": re.sub(r'\*+', '', match_fallback.group(4)).strip(),
                    "JUSTIFICATION": re.sub(r'\*+', '', match_fallback.group(5)).strip(),
                }
            
            logger.warning(f"Could not parse response correctly:\n{response[:1000]}")
            return {
                "STATEMENT": "",
                "EVIDENCE": "",
                "CITATIONS": "",
                "ALIGNMENT CATEGORY": "",
                "JUSTIFICATION": "",
            }
    except Exception as e:
        logger.error(f"Parsing error: {e}")
        return {
            "STATEMENT": "",
            "EVIDENCE": "",
            "CITATIONS": "",
            "ALIGNMENT CATEGORY": "",
            "JUSTIFICATION": "",
        }


def chunk_text_by_tokens(text, model, max_tokens):
    """
    Splits a string into chunks such that each chunk is ≤ max_tokens for the specified model.
    """
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


def extract_json_array(text: str | None) -> List[Dict[str, Any]]:
    if text is None:
        logger.error("Received None as input to extract_json_array")
        return []
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError as e:
                logger.error(
                    f"Regex-extracted JSON is invalid: {e}\nRaw text: {text[:1000]}"
                )
        logger.error(f"No valid JSON array found in text: {text[:1000]}")
        return []
    return []



async def process_single_indicator(
    indicator: Dict[str, str],
    alignment_def: str,
    vss_vector_store: Any,
    openai_client: Any,
    max_retries: int = 3,
    delay_between_calls: float = 0.5,
    semaphore: asyncio.Semaphore = None,
) -> Dict[str, Any]:
    indicator_id = indicator["indicator_id"]
    question = indicator["question"]
    evidence = indicator["evidence"]

    # Get relevant VSS chunks for this indicator - increased for more comprehensive evidence
    relevant_chunks = vss_vector_store.get_chunks_for_indicator(question, top_k=10)
    vss_text_for_prompt = vss_vector_store.format_chunks_for_prompt(relevant_chunks)

    prompt = analysis_prompt(
        alignment_def=alignment_def,
        indicator_id=indicator_id,
        vss_texts=vss_text_for_prompt,
        question=question,
        evidence=evidence,
    )

    async def _call():
        for attempt in range(max_retries):
            try:
                response = await openai_client.chat(prompt, max_tokens=6000)
                parsed_result = {
                    "Indicator ID": indicator_id,
                    **parse_analysis_response(response),
                }
                logger.info(f"Processed indicator {indicator_id}")
                return parsed_result
            except RateLimitError:
                wait_time = 2 ** attempt
                logger.warning(f"Rate limit hit for {indicator_id}, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"Error processing {indicator_id}: {e}")
                error_dir = os.path.join(settings.STORAGE_ROOT, "errors")
                os.makedirs(error_dir, exist_ok=True)
                with open(os.path.join(error_dir, f"gpt_single_error_{indicator_id}.txt"), "w") as f:
                    f.write(prompt)
                return {
                    "Indicator ID": indicator_id,
                    "STATEMENT": "",
                    "EVIDENCE": "",
                    "CITATIONS": "",
                    "ALIGNMENT CATEGORY": "",
                    "JUSTIFICATION": "",
                }

        return {
            "Indicator ID": indicator_id,
            "STATEMENT": "",
            "EVIDENCE": "",
            "CITATIONS": "",
            "ALIGNMENT CATEGORY": "",
            "JUSTIFICATION": "",
        }

    if semaphore:
        async with semaphore:
            return await _call()
    else:
        return await _call()


async def process_gpt_per_indicator(
    indicators: List[Dict[str, str]],
    alignment_def: str,
    vss_vector_store: Any,
    openai_client: Any,
    max_concurrent_tasks: int = 450
) -> List[Dict[str, Any]]:
    logger.info(f"Processing {len(indicators)} indicators with in-memory VSS vector store")
    logger.info(f"Vector store stats: {vss_vector_store.get_stats()}")

    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    tasks = [
        process_single_indicator(ind, alignment_def, vss_vector_store, openai_client, semaphore=semaphore)
        for ind in indicators
    ]
    results = await asyncio.gather(*tasks)
    return results

class AnalysisService:
    def create_analysis(self, db: Session) -> Analysis:
        analysis = Analysis(status="in_progress")
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Created new analysis job with id {analysis.id}")
        return analysis

    def update_analysis_status(
        self, db: Session, analysis_id: int, status: str, output_file: str = ""
    ):
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            setattr(analysis, "status", status)
            if output_file:
                setattr(analysis, "output_file", output_file)
            db.commit()
            logger.info(f"Updated analysis {analysis_id} to status {status}")

    async def run_analysis(
        self,
        db: Session,
        vss_paths: List[str],
        analysis_id: int,
        process_id: str,
        namespace: str,
    ) -> None:
        try:
            start_time = datetime.datetime.now()
            logger.info(f"Starting analysis service at {start_time}")
            indicators = (
                db.query(Indicator).filter(Indicator.process_id == process_id).all()
            )
            if not indicators:
                raise Exception("No indicators found in DB for this process_id.")

            # Initialize in-memory VSS vector store
            from infrastructure.vectorstores.vss_faiss_store import InMemoryVSSVectorStore
            
            vss_vector_store = InMemoryVSSVectorStore()
            
            # Add all VSS documents to vector store with exact page extraction
            vss_vector_store.add_vss_documents(vss_paths)
            
            # Build the FAISS index
            vss_vector_store.build_index()
            logger.info(f"Built VSS vector store with stats: {vss_vector_store.get_stats()}")

            # Prepare all indicator batches concurrently
            from infrastructure.vectorstores.pinecone_retriever import RAGSearcher

            rag_searcher = RAGSearcher(namespace=namespace)

            async def fetch_evidence(indicator_obj):
                indicator_id = str(indicator_obj.indicator_id)
                question = str(indicator_obj.indicator)
                try:
                    # Increase search results for more comprehensive evidence gathering
                    retrieved_chunks = await rag_searcher.async_search(str(question))

                    formatted_chunks = []
                    for chunk in retrieved_chunks:
                        page = chunk.metadata.get("page", "unknown")
                        source_file = chunk.metadata.get("source_file", "unknown")  # Get source file
                        page_str = f"{page}" if page is not None else "unknown"
                        # Include more context and formatting for better evidence extraction
                        content_for_llm = f"[Source: {source_file}, Page: {page_str}]\n{chunk.page_content.strip()}"
                        formatted_chunks.append(content_for_llm)
                                
                except Exception as e:
                    logger.error(f"RAG search failed for indicator {indicator_id}: {e}")
                    formatted_chunks = []
                return {
                    "indicator_id": indicator_id,
                    "question": question,
                    "evidence": formatted_chunks,
                }


            logger.info(
                f"Fetching RAG evidence for {len(indicators)} indicators concurrently..."
            )
            # Batch RAG searches to avoid rate limits (e.g., 50 at a time)
            rag_batch_size = 50
            all_batches = []
            for i in range(0, len(indicators), rag_batch_size):
                batch = indicators[i : i + rag_batch_size]
                batch_results = await asyncio.gather(
                    *(fetch_evidence(ind) for ind in batch)
                )
                all_batches.extend(batch_results)
                logger.info(
                    f"Completed RAG batch {i // rag_batch_size + 1}/{len(indicators) // rag_batch_size + 1}"
                )
                await asyncio.sleep(1)  # Brief pause to respect rate limits

            # Convert alignment_def to string if necessary
            alignment_def_str = (
                alignment_def
                if isinstance(alignment_def, str)
                else json.dumps(alignment_def)
            )
            logger.info(
                f"alignment_def type: {type(alignment_def)}, value: {alignment_def_str[:100]}"
            )

            # Process all batches in parallel
            logger.info(
                f"Processing {len(all_batches)} indicators in parallel batches of 5..."
            )
            results = await process_gpt_per_indicator(all_batches, alignment_def_str, vss_vector_store, openai_client)

            logger.info(
                f"Total GPT calls made: {len(all_batches) // 5 + (1 if len(all_batches) % 5 else 0)}"
            )

            # Save to Excel
            from core.config import settings
            output_dir = os.path.join(settings.STORAGE_ROOT, settings.ANALYSIS_OUTPUT_DIR)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "llm_results.xlsx")

            # Prepare DataFrame with required columns and formatted GPT response
            def format_gpt_response(row):
                return (
                    f"STATEMENT: {row.get('STATEMENT', '')}\n\n"
                    f"EVIDENCE: {row.get('EVIDENCE', '')}\n\n"
                    f"CITATIONS: {row.get('CITATIONS', '')}\n\n"
                    f"ALIGNMENT CATEGORY: {row.get('ALIGNMENT CATEGORY', '')}\n\n"
                    f"JUSTIFICATION: {row.get('JUSTIFICATION', '')}"
                )

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
            self.update_analysis_status(db, analysis_id, "completed", output_file)
            
            # Clean up the in-memory vector store
            vss_vector_store.clear()
            logger.info("Cleared in-memory VSS vector store")
            
            end_time = datetime.datetime.now()
            logger.info(f"Analysis completed at {end_time}")
            logger.info(f"Total analysis duration: {end_time - start_time}")
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.update_analysis_status(db, analysis_id, "error", "")
            
            # Clean up the in-memory vector store on error
            try:
                if 'vss_vector_store' in locals():
                    vss_vector_store.clear()
                    logger.info("Cleared in-memory VSS vector store on error")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup vector store: {cleanup_error}")
            
            raise

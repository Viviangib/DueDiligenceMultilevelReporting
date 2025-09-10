"""
Analysis processing functions for RAG and GPT operations.
"""
import logging
import asyncio
import datetime
import os
from typing import List, Dict, Any
from openai import RateLimitError
from core.config import settings
from utils.prompts import analysis_prompt

logger = logging.getLogger(__name__)


async def fetch_evidence_for_indicator(indicator_obj, rag_searcher, start_time: datetime.datetime):
    """Fetch evidence for a single indicator using RAG search."""
    indicator_id = str(indicator_obj.indicator_id)
    question = str(indicator_obj.indicator)

    try:   
        retrieved_chunks = await rag_searcher.async_search(str(question))

        formatted_chunks = []
        for chunk in retrieved_chunks:
            page = chunk.metadata.get("page", "unknown")
            source_file = chunk.metadata.get("source_file", "unknown")
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


async def process_single_indicator(
    indicator: Dict[str, str],
    alignment_def: str,
    vss_vector_store: Any,
    openai_client: Any,
    max_retries: int = 3,
    delay_between_calls: float = 0.2,
    semaphore: asyncio.Semaphore = None,
) -> Dict[str, Any]:
    """Process a single indicator with GPT."""
    from helpers.analysis.helpers import parse_analysis_response
    
    indicator_id = indicator["indicator_id"]
    question = indicator["question"]
    evidence = indicator["evidence"]

    # Get relevant VSS chunks for this indicator
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
                wait_time = (2 ** attempt) + 10  # Increased base delay from 5 to 10 seconds
                logger.warning(f"[GPT] Rate limit for {indicator_id}. Backing off for {wait_time}s (attempt {attempt+1}/{max_retries})")
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
            result = await _call()
            return result
    else:
        result = await _call()
        return result


async def process_gpt_per_indicator(
    indicators: List[Dict[str, str]],
    alignment_def: str,
    vss_vector_store: Any,
    openai_client: Any,
    max_concurrent_tasks: int = 500
) -> List[Dict[str, Any]]:
    """Process indicators in batches with GPT."""
    logger.info(f"Processing {len(indicators)} indicators with in-memory VSS vector store")
    logger.info(f"Vector store stats: {vss_vector_store.get_stats()}")
    logger.info(f"Using max_concurrent_tasks: {max_concurrent_tasks}")

    semaphore = asyncio.Semaphore(max_concurrent_tasks)
    results = []
    
    # Process indicators in smaller batches to avoid overwhelming the API
    batch_size = 50
    total_batches = (len(indicators) + batch_size - 1) // batch_size
    
    for i in range(0, len(indicators), batch_size):
        batch = indicators[i : i + batch_size]
        current_batch = i // batch_size + 1
        
        logger.info(f"Processing GPT batch {current_batch}/{total_batches} ({len(batch)} indicators)")
        
        tasks = [
            process_single_indicator(ind, alignment_def, vss_vector_store, openai_client, semaphore=semaphore)
            for ind in batch
        ]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)
      
    
    return results


async def process_rag_evidence_batch(
    indicators: List[Any],
    rag_searcher: Any,
    start_time: datetime.datetime,
    rag_batch_size: int = 50
) -> List[Dict[str, Any]]:
    """Process RAG evidence for indicators in batches."""
    logger.info(f"Fetching RAG evidence for {len(indicators)} indicators concurrently...")
    
    all_batches = []
    total_batches = (len(indicators) + rag_batch_size - 1) // rag_batch_size
    
    for i in range(0, len(indicators), rag_batch_size):
        batch = indicators[i : i + rag_batch_size]
        batch_results = await asyncio.gather(
            *(fetch_evidence_for_indicator(ind, rag_searcher, start_time) for ind in batch)
        )
        all_batches.extend(batch_results)
        current_batch = i // rag_batch_size + 1
        logger.info(f"Completed RAG batch {current_batch}/{total_batches}")
    return all_batches

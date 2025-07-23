import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.prompts.alignment import alignment_def
from utils.prompts.analysis import build_batch_prompt
from vector_store.pinecone_store import rag_searcher
from openai import AsyncOpenAI, RateLimitError
import uuid
import os
import re
import json
from models.analysis import Analysis
from typing import List, Dict, Any, Tuple
import asyncio
import datetime
from services.openAI.chat import OpenAIClient
import tiktoken


# Configure logging
logger = logging.getLogger(__name__)

openai_client = OpenAIClient(model="gpt-4o-mini")


def chunk_text_by_tokens(text, model, max_tokens):
    """
    Splits a string into chunks such that each chunk is ≤ max_tokens for the specified model.
    """
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)

    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
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


async def process_gpt_batch(
    batch: List[Dict[str, str]],
    alignment_def: str,
    vss_texts: List[str],
    openai_client: Any,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    combined_vss_text = " ".join(vss_texts)
    logger.info(
        f"Combined VSS text length: {len(combined_vss_text)} characters (~{len(combined_vss_text)//4} tokens)"
    )

    async def process_single_batch(
        single_batch: List[Dict[str, str]], batch_index: int
    ) -> Tuple[int, List[Dict[str, Any]]]:
        prompt = build_batch_prompt(single_batch, alignment_def, combined_vss_text)
        for attempt in range(max_retries):
            try:
                response = await openai_client.chat(
                    prompt, max_tokens=16000
                )  # Increased for chunk_size=5
                batch_results = extract_json_array(response)
                logger.info(
                    f"Batch {batch_index} token usage: {openai_client.last_response.usage if hasattr(openai_client, 'last_response') else 'unknown'}"
                )
                if isinstance(batch_results, list):
                    input_ids = {item["indicator_id"] for item in single_batch}
                    output_ids = {
                        result["Indicator ID"]
                        for result in batch_results
                        if "Indicator ID" in result
                    }
                    if (
                        len(batch_results) == len(single_batch)
                        and input_ids == output_ids
                    ):
                        return batch_index, batch_results
                    logger.warning(
                        f"Batch {batch_index} output mismatch: expected {len(single_batch)} indicators, got {len(batch_results)}, missing IDs: {input_ids - output_ids}"
                    )
                    return batch_index, batch_results  # Preserve partial results
                logger.warning(f"Batch {batch_index} invalid output: not a list")
            except (RateLimitError, Exception) as e:
                logger.error(
                    f"Batch {batch_index} failed: {e}\nContent: {response[:1000] if 'response' in locals() else 'N/A'}"
                )
                with open(
                    f"gpt_batch_error_output_{uuid.uuid4()}.json", "w", encoding="utf-8"
                ) as f:
                    f.write(response if "response" in locals() else str(e))
                if isinstance(e, RateLimitError) or "503" in str(e) or "520" in str(e):
                    await asyncio.sleep(2**attempt)  # Exponential backoff
        return batch_index, []  # Explicit return for all code paths

    # Split batch into smaller chunks
    chunk_size = 3
    batches = [batch[i : i + chunk_size] for i in range(0, len(batch), chunk_size)]
    logger.info(f"Created {len(batches)} sub-batches for {len(batch)} indicators")

    # Process batches concurrently
    tasks = [process_single_batch(b, i) for i, b in enumerate(batches)]
    results_by_index: Dict[int, List[Dict[str, Any]]] = {}
    for future in asyncio.as_completed(tasks):
        batch_index, batch_result = await future
        if batch_result:
            results_by_index[batch_index] = batch_result

    # Combine results in original order
    results: List[Dict[str, Any]] = []
    missing_indicators: List[Dict[str, str]] = []
    for i in range(len(batches)):
        if i in results_by_index:
            results.extend(results_by_index[i])
        else:
            missing_batch = batches[i]
            missing_indicators.extend(missing_batch)
            logger.warning(f"Batch {i} missing from results")

    # Retry missing indicators individually
    if missing_indicators:
        logger.info(
            f"Retrying {len(missing_indicators)} missing indicators individually"
        )
        retry_tasks = [
            process_single_batch([indicator], i + len(batches))
            for i, indicator in enumerate(missing_indicators)
        ]
        for future in asyncio.as_completed(retry_tasks):
            batch_index, retry_result = await future
            if retry_result:
                results.extend(retry_result)
            else:
                missing_id = missing_indicators[batch_index - len(batches)][
                    "indicator_id"
                ]
                logger.error(f"Failed to retry indicator: {missing_id}")

    # Validate all indicators are included
    input_ids = {item["indicator_id"] for item in batch}
    output_ids = {
        result["Indicator ID"] for result in results if "Indicator ID" in result
    }
    still_missing = input_ids - output_ids
    if still_missing:
        logger.error(f"Still missing {len(still_missing)} indicators: {still_missing}")

    # Sort results by indicator_id to match input order
    input_id_order = {item["indicator_id"]: i for i, item in enumerate(batch)}
    results.sort(key=lambda x: input_id_order.get(x["Indicator ID"], float("inf")))
    logger.info(f"Completed processing {len(results)} indicators")
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

            # Read VSS text
            vss_texts = []
            for path in vss_paths:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".pdf":
                    import pdfplumber

                    with pdfplumber.open(path) as pdf:
                        text = "".join(page.extract_text() or "" for page in pdf.pages)
                        vss_texts.append(text)
                elif ext == ".docx":
                    from docx import Document

                    doc = Document(path)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    vss_texts.append(text)

            # Prepare all indicator batches concurrently
            from vector_store.pinecone_store import RAGSearcher

            rag_searcher = RAGSearcher(namespace=namespace)

            async def fetch_evidence(indicator_obj):
                indicator_id = str(indicator_obj.indicator_id)
                question = str(indicator_obj.indicator)
                try:
                    evidence = await rag_searcher.async_search(str(question))
                except Exception as e:
                    logger.error(f"RAG search failed for indicator {indicator_id}: {e}")
                    evidence = []
                return {
                    "indicator_id": indicator_id,
                    "question": question,
                    "evidence": evidence,
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
            results = await process_gpt_batch(
                all_batches, alignment_def_str, vss_texts, openai_client
            )
            logger.info(
                f"Total GPT calls made: {len(all_batches) // 5 + (1 if len(all_batches) % 5 else 0)}"
            )

            # Save to Excel
            output_dir = "analysis"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"llm_results_{uuid.uuid4()}.xlsx")

            # Prepare DataFrame with required columns and formatted GPT response
            def format_gpt_response(row):
                return (
                    f"STATEMENT: {row.get('STATEMENT', '')}\n"
                    f"EVIDENCE: {row.get('EVIDENCE', '')}\n"
                    f"CITATIONS: {row.get('CITATIONS', '')}\n"
                    f"ALIGNMENT CATEGORY: {row.get('ALIGNMENT CATEGORY', '')}\n"
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
            end_time = datetime.datetime.now()
            logger.info(f"Analysis completed at {end_time}")
            logger.info(f"Total analysis duration: {end_time - start_time}")
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.update_analysis_status(db, analysis_id, "error", "")
            raise

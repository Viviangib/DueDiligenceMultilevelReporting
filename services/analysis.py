import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.prompts.alignment import alignment_def
from utils.prompts.analysis import build_batch_prompt,analysis_prompt
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



def parse_analysis_response(response: str) -> Dict[str, str]:
    try:
        pattern = r"STATEMENT:(.*?)EVIDENCE:(.*?)CITATIONS:(.*?)ALIGNMENT CATEGORY:(.*?)JUSTIFICATION:(.*)"
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            return {
                "STATEMENT": match.group(1).strip(),
                "EVIDENCE": match.group(2).strip(),
                "CITATIONS": match.group(3).strip(),
                "ALIGNMENT CATEGORY": match.group(4).strip(),
                "JUSTIFICATION": match.group(5).strip(),
            }
        else:
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
    combined_vss_text: str,
    openai_client: Any,
    max_retries: int = 3,
    delay_between_calls: float = 0.5,
    semaphore: asyncio.Semaphore = None,
) -> Dict[str, Any]:
    indicator_id = indicator["indicator_id"]
    question = indicator["question"]
    evidence = indicator["evidence"]

    prompt = analysis_prompt(
        alignment_def=alignment_def,
        indicator_id=indicator_id,
        vss_texts=combined_vss_text,
        question=question,
        evidence=evidence,
    )

    async def _call():
        for attempt in range(max_retries):
            try:
                response = await openai_client.chat(prompt, max_tokens=4000)
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
                with open(f"gpt_single_error_{indicator_id}_{uuid.uuid4()}.txt", "w") as f:
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
    vss_texts: List[str],
    openai_client: Any,
    max_concurrent_tasks: int = 450
) -> List[Dict[str, Any]]:
    combined_vss_text = " ".join(vss_texts)
    logger.info(f"Combined VSS text length: {len(combined_vss_text)} characters")

    semaphore = asyncio.Semaphore(max_concurrent_tasks)

    tasks = [
        process_single_indicator(ind, alignment_def, combined_vss_text, openai_client, semaphore=semaphore)
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
                    retrieved_chunks = await rag_searcher.async_search(str(question))

                    formatted_chunks = []
                    for chunk in retrieved_chunks:
                        page = chunk.metadata.get("page", "unknown")
                        source_file = chunk.metadata.get("source_file", "unknown")  # Get source file
                        page_str = f"{page}" if page is not None else "unknown"
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
            results = await process_gpt_per_indicator(all_batches, alignment_def_str, vss_texts, openai_client)

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

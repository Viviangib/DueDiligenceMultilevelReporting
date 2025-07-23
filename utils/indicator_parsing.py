import json
import re
from utils.indicator_parser import openai_client
from utils.prompts.indicator import INDICATOR_PROMPT
from openai import AsyncOpenAI, RateLimitError
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import settings
from services.openAI.chat import OpenAIClient
import logging
from typing import List, Dict, Any, Tuple
import asyncio
import uuid

logger = logging.getLogger(__name__)

openai_client = OpenAIClient()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())


def split_text_into_chunks(text: str, chunk_size=3000, chunk_overlap=200) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " "],
    )
    return splitter.split_documents([Document(page_content=text)])


def try_extract_json(content: str):
    try:
        return json.loads(content)
    except:
        match = re.search(r"\[\s*{[\s\S]*?}\s*]", content)
        if match:
            try:
                return json.loads(match.group())
            except Exception as e:
                print(f"❌ Regex parse failed: {e}")
    return []


async def process_single_chunk(chunk: str, chunk_index: int, max_retries: int = 3) -> Tuple[int, List[Dict[str, Any]]]:
    prompt = INDICATOR_PROMPT.format(chunk=chunk)
    for attempt in range(max_retries):
        try:
            logger.info(f"Processing chunk {chunk_index}, attempt {attempt + 1}")
            response = await openai_client.chat(prompt=prompt, temperature=0, max_tokens=4000)
            if response:
                indicators = try_extract_json(response)
                if isinstance(indicators, list):
                    logger.info(f"Successfully extracted {len(indicators)} indicators from chunk {chunk_index}")
                    return chunk_index, indicators
                logger.warning(f"Invalid response format from chunk {chunk_index}")
        except (RateLimitError, Exception) as e:
            logger.error(f"Chunk {chunk_index} failed: {e}")
            if isinstance(e, RateLimitError) or "503" in str(e) or "520" in str(e):
                await asyncio.sleep(2**attempt)  # Exponential backoff
                continue
    return chunk_index, []

async def parse_indicators_with_llm(text: str) -> List[Dict[str, Any]]:
    chunks = split_text_into_chunks(text)
    logger.info(f"Split text into {len(chunks)} chunks for parallel processing")
    
    # Process chunks in parallel with batch size of 10
    batch_size = 3
    all_indicators = []
    
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
        
        # Create tasks for concurrent processing
        tasks = [
            process_single_chunk(chunk.page_content, idx + i)
            for idx, chunk in enumerate(batch_chunks)
        ]
        
        # Process batch concurrently
        results_by_index: Dict[int, List[Dict[str, Any]]] = {}
        for future in asyncio.as_completed(tasks):
            chunk_index, chunk_indicators = await future
            if chunk_indicators:
                results_by_index[chunk_index] = chunk_indicators
        
        # Combine results in order
        for j in range(len(batch_chunks)):
            chunk_idx = i + j
            if chunk_idx in results_by_index:
                all_indicators.extend(results_by_index[chunk_idx])
            else:
                logger.warning(f"No results for chunk {chunk_idx}")
        
        # Brief pause between batches to avoid rate limits
        if i + batch_size < len(chunks):
            await asyncio.sleep(1)
    
    logger.info(f"Total indicators extracted: {len(all_indicators)}")
    return all_indicators

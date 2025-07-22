import json
import re
from utils.indicator_parser import openai_client
from utils.prompts.indicator import INDICATOR_PROMPT
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config import settings
from services.openAI.chat import OpenAIClient
import logging


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


async def parse_indicators_with_llm(text: str):
    chunks = split_text_into_chunks(text)
    all_indicators = []
    logger.info(f"Splitting text into {len(chunks)} chunks for LLM parsing.")
    for i, chunk_doc in enumerate(chunks):
        chunk = chunk_doc.page_content
        prompt = INDICATOR_PROMPT.format(chunk=chunk)
        logger.info(
            f"Processing chunk {i+1}/{len(chunks)} (length: {len(chunk)} chars)..."
        )
        try:
            logger.info(f"Sending chunk {i+1} to LLM...")
            content = await openai_client.chat(
                prompt=prompt, temperature=0, max_tokens=4000
            )
            logger.info(f"Received response for chunk {i+1}.")
            if content:
                indicators = try_extract_json(content)
                logger.info(f"Extracted {len(indicators)} indicators from chunk {i+1}.")
                all_indicators.extend(indicators)
        except Exception as e:
            logger.error(f"Failed on chunk {i+1}: {e}")
    logger.info(f"Total indicators extracted: {len(all_indicators)}")
    return all_indicators

"""
Report generation and processing logic.
"""
import os
import logging
import asyncio
import pandas as pd
import tiktoken
import pypandoc
from typing import Dict, Any
from services.openai import OpenAIClient
from utils.prompts import report_generation_prompt
from helpers.report.files import get_report_file_path, get_template_path, get_css_path, prepare_pypandoc_args

logger = logging.getLogger(__name__)

openai_client = OpenAIClient(model="gpt-4o-mini")


def chunk_text_by_tokens(text: str, model: str, max_tokens: int) -> list[str]:
    """Split text into chunks based on token count."""
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks


async def generate_report_from_data(
    analysis_data: str,
    num_indicators: int,
    sustainability_framework: str,
    legal_framework: str,
) -> str:
    """Generate report content from analysis data."""
    max_tokens_per_chunk = 100_000
    chunks = chunk_text_by_tokens(
        analysis_data, model="gpt-4o-mini", max_tokens=max_tokens_per_chunk
    )
    
    if len(chunks) > 1:
        logger.info(
            f"Analysis data is too long, splitting into {len(chunks)} token-based chunks..."
        )
        return await _generate_chunked_report(
            chunks, num_indicators, sustainability_framework, legal_framework
        )
    else:
        return await _generate_single_report(
            analysis_data, num_indicators, sustainability_framework, legal_framework
        )


async def _generate_chunked_report(
    chunks: list[str],
    num_indicators: int,
    sustainability_framework: str,
    legal_framework: str,
) -> str:
    """Generate report from multiple chunks."""
    partial_reports = []
    
    for idx, chunk in enumerate(chunks):
        logger.info(f"Generating partial report for chunk {idx+1}/{len(chunks)}...")
        chunk_prompt = report_generation_prompt(
            analysis_data=chunk,
            num_indicators=num_indicators,
            sustainability_framework=sustainability_framework,
            legal_framework=legal_framework,
        )
        chunk_prompt = (
            f"This is part {idx+1} of {len(chunks)} of the analysis data. Generate a partial benchmarking summary for this chunk.\n"
            + chunk_prompt
        )
        partial = await openai_client.chat(chunk_prompt, max_tokens=4000)
        partial_reports.append(partial)
        # Add delay between report chunks to avoid rate limiting
        await asyncio.sleep(2)
    
    logger.info("Synthesizing final report from partials...")
    synthesis_prompt = (
        f"You are a professional benchmarking report writer. Combine the following {len(partial_reports)} partial benchmarking summaries into a single, cohesive, professional report. Remove any duplicate sections, merge tables, and ensure the report flows as a single document.\n\n"
        + "\n\n---\n\n".join(partial_reports)
    )
    final_report = await openai_client.chat(synthesis_prompt, max_tokens=4000)
    # Add delay after synthesis
    await asyncio.sleep(1)
    
    return final_report


async def _generate_single_report(
    analysis_data: str,
    num_indicators: int,
    sustainability_framework: str,
    legal_framework: str,
) -> str:
    """Generate report from single data chunk."""
    prompt = report_generation_prompt(
        analysis_data=analysis_data,
        num_indicators=num_indicators,
        sustainability_framework=sustainability_framework,
        legal_framework=legal_framework,
    )
    logger.info("Sending report generation prompt to GPT...")
    final_report = await openai_client.chat(prompt, max_tokens=4000)
    # Add delay after report generation
    await asyncio.sleep(1)
    
    return final_report


def convert_markdown_to_docx(final_report: str) -> str:
    """Convert markdown report to DOCX format."""
    report_file_path = get_report_file_path()
    template_path = get_template_path()
    css_path = get_css_path()
    
    logger.info(f"Converting markdown content to DOCX at: {report_file_path}")
    logger.info(f"Using reference template: {template_path}")
    
    enhanced_args = prepare_pypandoc_args(template_path, css_path)
    logger.info(f"Converting with pypandoc args: {enhanced_args}")
    
    try:
        pypandoc.convert_text(
            final_report,
            'docx',
            format='md',
            outputfile=report_file_path,
            extra_args=enhanced_args
        )
        
        # Verify DOCX file was created
        if not os.path.exists(report_file_path):
            raise Exception(f"Failed to create DOCX file at {report_file_path}")
        
        logger.info(f"DOCX report saved successfully at: {report_file_path}")
        return report_file_path
        
    except Exception as e:
        logger.error(f"Failed to convert markdown to DOCX: {str(e)}")
        raise Exception(f"Failed to convert markdown to DOCX: {str(e)}")


def prepare_report_data_from_excel(file_path: str) -> tuple[str, int]:
    """Load and prepare data from Excel file."""
    df = pd.read_excel(file_path)
    logger.info(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
    
    if df.empty:
        raise Exception("Excel file contains no data.")
    
    analysis_data = df.to_string(index=False, max_rows=None, max_colwidth=None)
    num_indicators = len(df)
    
    return analysis_data, num_indicators

"""
Helper functions for analysis processing.
"""
import logging
import re
import json
import asyncio
import datetime
from typing import List, Dict, Any
from openai import RateLimitError
from core.config import settings

logger = logging.getLogger(__name__)


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
    """Parse GPT response into structured format."""
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


def extract_json_array(text: str | None) -> List[Dict[str, Any]]:
    """Extract JSON array from text."""
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


def format_gpt_response(row: Dict[str, Any]) -> str:
    """Format GPT response for Excel output."""
    return (
        f"STATEMENT: {row.get('STATEMENT', '')}\n\n"
        f"EVIDENCE: {row.get('EVIDENCE', '')}\n\n"
        f"CITATIONS: {row.get('CITATIONS', '')}\n\n"
        f"ALIGNMENT CATEGORY: {row.get('ALIGNMENT CATEGORY', '')}\n\n"
        f"JUSTIFICATION: {row.get('JUSTIFICATION', '')}"
    )

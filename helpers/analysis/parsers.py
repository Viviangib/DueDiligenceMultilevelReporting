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


def fix_section_spacing(text: str) -> str:
    """
    Fix spacing between major sections to ensure 2 blank lines between each section.
    Handles the new format: (1) STATEMENT:, (2) VSS CONTEXT:, etc.
    """
    if not text or not text.strip():
        return text
    
    # Pattern to match section headers: (1) STATEMENT:, (2) VSS CONTEXT:, etc.
    section_patterns = [
        r'\(1\)\s*STATEMENT:',
        r'\(2\)\s*VSS\s*CONTEXT:',
        r'\(3\)\s*REGULATION\s*EVIDENCE:',
        r'\(4\)\s*CITATIONS:',
        r'\(5\)\s*ALIGNMENT\s*CATEGORY:',
        r'\(6\)\s*JUSTIFICATION:',
    ]
    
    # Fix spacing before each section header (except the first one)
    formatted_text = text
    
    # Ensure each section header is on its own line
    for pattern in section_patterns:
        # Add newline before section header if it's not already there
        formatted_text = re.sub(rf'([^\n])({pattern})', r'\1\n\n\2', formatted_text, flags=re.IGNORECASE)
        # Ensure section header is followed by newline
        formatted_text = re.sub(rf'({pattern})([^\n])', r'\1\n\2', formatted_text, flags=re.IGNORECASE)
    
    # Normalize spacing: ensure exactly 2 blank lines between sections
    # Replace any sequence of 1-3 newlines before a section header with exactly 2 newlines
    for pattern in section_patterns[1:]:  # Skip first section
        formatted_text = re.sub(rf'(\n{{1,3}})({pattern})', r'\n\n\2', formatted_text, flags=re.IGNORECASE)
    
    # Clean up excessive blank lines (more than 2 consecutive newlines)
    formatted_text = re.sub(r'\n{3,}', '\n\n', formatted_text)
    
    return formatted_text.strip()


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
        # Remove asterisks but preserve newlines for spacing
        cleaned_response = re.sub(r'\*+', '', response)
        
        # Try new format first: (1) STATEMENT:, (2) VSS CONTEXT:, (3) REGULATION EVIDENCE:, etc.
        pattern_new = r"\(1\)\s*STATEMENT:\s*(.*?)\s*\(2\)\s*VSS\s*CONTEXT:\s*(.*?)\s*\(3\)\s*REGULATION\s*EVIDENCE:\s*(.*?)\s*\(4\)\s*CITATIONS:\s*(.*?)\s*\(5\)\s*ALIGNMENT\s*CATEGORY:\s*(.*?)\s*\(6\)\s*JUSTIFICATION:\s*(.*?)$"
        match = re.search(pattern_new, cleaned_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Extract sections
            statement = match.group(1).strip()
            vss_context = match.group(2).strip()
            regulation_evidence = match.group(3).strip()
            citations = match.group(4).strip()
            alignment = match.group(5).strip()
            justification = match.group(6).strip()
            
            # Combine VSS CONTEXT and REGULATION EVIDENCE into EVIDENCE field
            evidence = f"VSS CONTEXT:\n{vss_context}\n\nREGULATION EVIDENCE:\n{regulation_evidence}"
            
            logger.info(f"Parsed new format - Statement: {len(statement)}, Evidence: {len(evidence)}, Citations: {len(citations)}")
            
            return {
                "STATEMENT": statement,
                "EVIDENCE": evidence,
                "CITATIONS": citations,
                "ALIGNMENT CATEGORY": alignment,
                "JUSTIFICATION": justification,
            }
        
        # Fallback: Try old format patterns
        # Pattern for numbered format (1. STATEMENT:, 2. EVIDENCE:, etc.)
        pattern_old = r"(?:1\.\s*)?STATEMENT:\s*(.*?)\s*(?:2\.\s*)?EVIDENCE:\s*(.*?)\s*(?:3\.\s*)?CITATIONS:\s*(.*?)\s*(?:4\.\s*)?ALIGNMENT\s+CATEGORY:\s*(.*?)\s*(?:5\.\s*)?JUSTIFICATION:\s*(.*?)$"
        match = re.search(pattern_old, cleaned_response, re.DOTALL | re.IGNORECASE)
        
        if match:
            raw_evidence = match.group(2).strip()
            raw_citations = match.group(3).strip()
            
            evidence = format_numbered_items(raw_evidence)
            citations = format_numbered_items(raw_citations)
            
            logger.info(f"Parsed old format - Evidence items: {evidence.count('(')}, Citations items: {citations.count('(')}")
            
            return {
                "STATEMENT": match.group(1).strip(),
                "EVIDENCE": evidence,
                "CITATIONS": citations,
                "ALIGNMENT CATEGORY": match.group(4).strip(),
                "JUSTIFICATION": match.group(5).strip(),
            }
        
        # Final fallback: try without numbers
        pattern_final = r"STATEMENT:(.*?)(?:VSS\s*CONTEXT:|EVIDENCE:)(.*?)(?:REGULATION\s*EVIDENCE:|CITATIONS:)(.*?)(?:ALIGNMENT\s*CATEGORY:|ALIGNMENT\s+CATEGORY:)(.*?)(?:JUSTIFICATION:)(.*)"
        match_final = re.search(pattern_final, cleaned_response, re.DOTALL | re.IGNORECASE)
        if match_final:
            return {
                "STATEMENT": match_final.group(1).strip(),
                "EVIDENCE": match_final.group(2).strip(),
                "CITATIONS": match_final.group(3).strip(),
                "ALIGNMENT CATEGORY": match_final.group(4).strip(),
                "JUSTIFICATION": match_final.group(5).strip(),
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

import re
import pdfplumber
from typing import List

def extract_indicators_from_pdf(file_path: str) -> List[str]:
    """
    Extracts indicators from a PDF file by searching for sentences containing regulatory keywords.
    """
    indicators = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and re.search(r'requirements|standards|criteria', text, re.IGNORECASE):
                sentences = re.split(r'(?<=[.!?])\s+', text)
                for sentence in sentences:
                    if re.search(r'\b(shall|must|requires?)\b', sentence, re.IGNORECASE):
                        indicators.append(sentence.strip())
    return indicators 
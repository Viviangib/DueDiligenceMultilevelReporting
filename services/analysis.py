import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.alignment import alignment_def, system_prompt
from vector_store.pinecone_store import rag_search
from openai import AsyncOpenAI
import uuid
import os
import re
import json
from models.analysis import Analysis
import ast


# Configure logging
logger = logging.getLogger(__name__)

class AnalysisService:
    def create_analysis(self, db: Session) -> Analysis:
        analysis = Analysis(status="in_progress")
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        logger.info(f"Created new analysis job with id {analysis.id}")
        return analysis

    def update_analysis_status(self, db: Session, analysis_id: int, status: str, output_file: str = ""):
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            setattr(analysis, 'status', status)
            if output_file:
                setattr(analysis, 'output_file', output_file)
            db.commit()
            logger.info(f"Updated analysis {analysis_id} to status {status}")

    async def run_analysis(self, db: Session, vss_paths: list[str], analysis_id: int) -> None:
        try:
            logger.info("Starting analysis service")

            # 1. Get 20 indicators from DB
            indicators = (
                db.query(Indicator)
                .offset(193)  # skip first 213 records, start at 214th
                .all()        # fetch all records from there
            )
            if not indicators:
                raise Exception("No indicators found in DB.")

            # 2. Read all VSS text
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

            # 3. Process indicators with RAG + GPT
            client = AsyncOpenAI()
            results = []

            for idx, indicator_obj in enumerate(indicators):
                raw_indicator = indicator_obj.indicator
                logger.info(f"Raw indicator: {raw_indicator} (type: {type(raw_indicator)})")

                if isinstance(raw_indicator, str):
                    try:
                        parsed = json.loads(raw_indicator)
                    except Exception as e:
                        logger.error(f"Failed to parse indicator JSON: {e}")
                        parsed = {}
                elif isinstance(raw_indicator, dict):
                    parsed = raw_indicator
                else:
                    logger.error(f"Unexpected type for indicator: {type(raw_indicator)}")
                    parsed = {}

                indicator_id = parsed.get("ID", f"IND{idx+1:03d}")
                question = parsed.get("Question", str(parsed))

                evidence = rag_search(str(question))

                # Prompt for GPT
                prompt = f"""
{system_prompt}

You are given the following indicator:

You are given the following Indicator from a voluntary sustainability standard (VSS):


You are also provided with the following information:
-

Alignment Definitions:
{alignment_def}

Criteria ID: {indicator_id}
Type: Statement
Indicator: {question}

 Supporting Documents (from the VSS): {vss_texts}
 
- Results from Regulation (RAG results): {evidence}

Alignment Definitions: {alignment_def}

For this indicator, provide the following in your response:

(1) STATEMENT: <repeat the indicator as a positive statement>
(2) EVIDENCE: <quote relevant evidence from the supporting documents that alligns with the regulations >
(3) CITATIONS: <list the source and location of each evidence>
(4) ALIGNMENT CATEGORY: <choose from alignment_def>
(5) JUSTIFICATION: <justify the alignment category>

Format your response as:
STATEMENT: ...
EVIDENCE: ...
CITATIONS: ...
ALIGNMENT CATEGORY: ...
JUSTIFICATION: ...
"""

                try:
                    response = await client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    content = response.choices[0].message.content or ""
                except Exception as e:
                    content = f"GPT-4 analysis failed: {e}"

                def extract_section(label):
                    match = re.search(rf"{label}:\s*(.*?)\n(?=\w+:|$)", content, re.DOTALL)
                    return match.group(1).strip() if match else ""

                alignment_key = extract_section("ALIGNMENT CATEGORY")
                alignment_label = alignment_key
                alignment_description = alignment_def.get(alignment_key, alignment_def.get(str(alignment_key), {})).get("Definition", "")

                results.append({
                    "Indicator ID": indicator_id,
                    "Question": question,
                    "GPT-4 Response": content,
                    "Alignment Label": alignment_label,
                    "Alignment Definition": alignment_description
                })

            # Save to Excel
            output_file = f"results/analysis_results_{uuid.uuid4()}.xlsx"
            os.makedirs("results", exist_ok=True)

            df = pd.DataFrame(results)
            df.to_excel(output_file, index=False)
            self.update_analysis_status(db, analysis_id, "completed", output_file)
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            self.update_analysis_status(db, analysis_id, "error", "")
            raise

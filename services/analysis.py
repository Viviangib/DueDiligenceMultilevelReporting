import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.prompts.alignment import alignment_def
from utils.prompts.analysis import analysis_prompt
from vector_store.pinecone_store import rag_search
from openai import AsyncOpenAI
import uuid
import os
import re
import json
from models.analysis import Analysis
import ast
from services.openAI.chat import OpenAIClient


# Configure logging
logger = logging.getLogger(__name__)

openai_client = OpenAIClient()
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

    async def run_analysis(self, db: Session, vss_paths: list[str], analysis_id: int, process_id: str) -> None:
        try:
            logger.info("Starting analysis service")

            indicators = (
                db.query(Indicator)
                .filter(Indicator.process_id == process_id)
                .all()
            )
            if not indicators:
                raise Exception("No indicators found in DB for this process_id.")

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
                indicator_id = str(indicator_obj.indicator_id)
                question = str(indicator_obj.indicator)

                evidence = rag_search(str(question))

                # Prompt for GPT
                prompt= analysis_prompt(alignment_def, indicator_id, vss_texts, question, evidence)

                content = await openai_client.chat(prompt)

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

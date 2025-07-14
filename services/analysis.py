import logging
import pandas as pd
from sqlalchemy.orm import Session
from models.indicator import Indicator
from utils.prompts.alignment import alignment_def
from utils.prompts.analysis import analysis_prompt
from utils.prompts.report import report_generation_prompt
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

    async def generate_summary_report(
        self, 
        excel_file_path: str,
        standard_name: str = "User Standard",
        standard_version: str = "1.0", 
        standard_year: str = "2024",
        organization: str = "User Organization"
    ) -> str:
        """
        Generate a comprehensive summary report from analysis Excel file.
        
        Args:
            excel_file_path: Path to the Excel file containing analysis results
            standard_name: Name of the benchmarked standard
            standard_version: Version of the standard
            standard_year: Year of publication
            organization: Name of the founding organization
            
        Returns:
            Path to the generated report file
        """
        try:
            logger.info(f"Starting report generation for file: {excel_file_path}")
            
            # Read the Excel file
            df = pd.read_excel(excel_file_path)
            logger.info(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            
            # Convert DataFrame to string representation for GPT
            analysis_data = df.to_string(index=False, max_rows=None, max_colwidth=None)
            
            # Generate report using GPT
            prompt = report_generation_prompt(
                analysis_data=analysis_data,
                standard_name=standard_name,
                standard_version=standard_version,
                standard_year=standard_year,
                organization=organization
            )
            
            logger.info("Sending report generation request to GPT")
            report_content = await openai_client.chat(prompt,max_tokens=16384)
            
            # Save report to file
            report_filename = f"results/summary_report_{uuid.uuid4()}.md"
            os.makedirs("results", exist_ok=True)
            
            with open(report_filename, "w", encoding="utf-8") as f:
                f.write(report_content)
            
            logger.info(f"Report generated successfully: {report_filename}")
            return report_filename
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise

    async def run_analysis(self, db: Session, vss_paths: list[str], analysis_id: int, process_id: str) -> None:
        try:
            logger.info("Starting analysis service")

            indicators = (
                db.query(Indicator)
                .filter(Indicator.process_id == process_id)
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

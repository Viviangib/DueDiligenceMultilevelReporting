import os
import uuid
import logging
from sqlalchemy.orm import Session
from models.report import Report
from enums.report import ReportStatus
from fastapi import HTTPException, UploadFile
from db import SessionLocal
from typing import Optional, Dict, Any
import asyncio
import pandas as pd
from services.openAI.chat import OpenAIClient
import tiktoken

logger = logging.getLogger(__name__)

TEMP_UPLOAD_DIR = "temp_uploads"
REPORTS_DIR = "summary_reports"
REPORT_EXCEL_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

openai_client = OpenAIClient(model="gpt-4o-mini")

def chunk_text_by_tokens(text, model, max_tokens):
    enc = tiktoken.encoding_for_model(model)
    tokens = enc.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

class ReportService:
    async def save_temp_file(self, upload_file: UploadFile) -> str:
        filename = upload_file.filename or "unknown.xlsx"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in [".xlsx", ".xls"]:
            logger.error(f"Rejected file with extension: {ext}")
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.abspath(os.path.join(TEMP_UPLOAD_DIR, unique_filename))
        try:
            content = await upload_file.read()
            with open(file_path, 'wb') as f:
                f.write(content)
            logger.info(f"Saved temp file at: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving temp file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")

    def create_report_record(self, db: Session) -> Report:
        try:
            report = Report(status=ReportStatus.IN_PROGRESS.value)
            db.add(report)
            db.commit()
            db.refresh(report)
            logger.info(f"Created report record with id: {report.id}")
            return report
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating report record: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to create report record")

    def get_report_by_id(self, db: Session, report_id: int) -> Optional[Report]:
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            logger.info(f"get_report_by_id: Looked up report_id={report_id}, found: {report}")
            return report
        except Exception as e:
            logger.error(f"Error getting report {report_id}: {str(e)}")
            return None

    def update_report_status(self, db: Session, report_id: int, status: str, file_path: Optional[str] = None):
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                logger.info(f"Updating report {report_id} status to {status} (file: {file_path})")
                setattr(report, 'status', status)
                if file_path:
                    setattr(report, 'file', file_path)
                db.commit()
                db.refresh(report)
                logger.info(f"Report {report_id} status updated and committed.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating report {report_id} status: {str(e)}")
            raise

    async def generate_and_save_report(
        self,
        report_id: int,
        temp_file_path: str,
        standard_name: str,
        standard_version: str,
        standard_year: str,
        organization: str,
    ):
        db = SessionLocal()
        try:
            self.update_report_status(db, report_id, ReportStatus.IN_PROGRESS.value)
            logger.info(f"Starting report generation for report {report_id} from file: {temp_file_path}")
            # --- LLM/Report Generation Logic ---
            df = pd.read_excel(temp_file_path)
            logger.info(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            if df.empty:
                raise Exception("Excel file contains no data.")
            analysis_data = df.to_string(index=False, max_rows=None, max_colwidth=None)
            num_indicators = len(df)
            max_tokens_per_chunk = 100_000
            chunks = chunk_text_by_tokens(analysis_data, model="gpt-4o", max_tokens=max_tokens_per_chunk)
            if len(chunks) > 1:
                logger.info(f"Analysis data is too long, splitting into {len(chunks)} token-based chunks...")
                partial_reports = []
                from utils.prompts.report import report_generation_prompt
                from utils.prompts.alignment import alignment_def
                for idx, chunk in enumerate(chunks):
                    logger.info(f"Generating partial report for chunk {idx+1}/{len(chunks)}...")
                    chunk_prompt = report_generation_prompt(
                        analysis_data=chunk,
                        num_indicators=num_indicators,
                        standard_name=standard_name,
                        standard_version=standard_version,
                        standard_year=standard_year,
                        organization=organization,
                    )
                    chunk_prompt = (
                        f"This is part {idx+1} of {len(chunks)} of the analysis data. Generate a partial benchmarking summary for this chunk.\n" + chunk_prompt
                    )
                    partial = await openai_client.chat(chunk_prompt, max_tokens=4000)
                    partial_reports.append(partial)
                logger.info("Synthesizing final report from partials...")
                synthesis_prompt = (
                    f"You are a professional benchmarking report writer. Combine the following {len(partial_reports)} partial benchmarking summaries into a single, cohesive, professional report. Remove any duplicate sections, merge tables, and ensure the report flows as a single document.\n\n"
                    + "\n\n---\n\n".join(partial_reports)
                )
                final_report = await openai_client.chat(synthesis_prompt, max_tokens=4000)
            else:
                from utils.prompts.report import report_generation_prompt
                from utils.prompts.alignment import alignment_def
                prompt = report_generation_prompt(
                    analysis_data=analysis_data,
                    num_indicators=num_indicators,
                    standard_name=standard_name,
                    standard_version=standard_version,
                    standard_year=standard_year,
                    organization=organization,
                )
                logger.info("Sending report generation prompt to GPT...")
                final_report = await openai_client.chat(prompt, max_tokens=4000)
            if not final_report.strip():
                raise Exception("GPT returned an empty response.")
            os.makedirs(REPORTS_DIR, exist_ok=True)
            report_file_path = os.path.abspath(os.path.join(REPORTS_DIR, f"benchmarking_summary_report_{uuid.uuid4()}.md"))
            with open(report_file_path, "w", encoding="utf-8") as f:
                f.write(final_report)
            logger.info(f"Report saved at: {report_file_path}")
            self.update_report_status(db, report_id, ReportStatus.COMPLETED.value, report_file_path)
            logger.info(f"Report {report_id} generated successfully and status set to COMPLETED")
        except Exception as e:
            logger.error(f"Report generation failed for report {report_id}: {str(e)}")
            self.update_report_status(db, report_id, ReportStatus.ERROR.value)
        finally:
            await self._cleanup_temp_file(temp_file_path)
            db.close()

    async def _cleanup_temp_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete temp file {file_path}: {e}")

    async def get_report_status_and_file(self, db: Session, report_id: int) -> Dict[str, Any]:
        report = self.get_report_by_id(db, report_id)
        logger.info(f"[GET] Looking for report_id={report_id}, found: {report}")
        if not report:
            logger.error(f"Report {report_id} not found in DB")
            raise HTTPException(status_code=404, detail="Report not found")
        status_value = getattr(report, 'status', 'unknown')
        file_path = getattr(report, 'file', None)
        abs_file_path = os.path.abspath(file_path) if file_path else None
        logger.info(f"[GET] Report {report_id} status: {status_value}, file: {file_path}, abs: {abs_file_path}")
        response_data = {
            "report_id": getattr(report, 'id'),
            "status": status_value,
            "created_at": getattr(report, 'created_at').isoformat() if hasattr(report, 'created_at') and getattr(report, 'created_at') else None,
        }
        if status_value == ReportStatus.COMPLETED.value:
            if abs_file_path and os.path.exists(abs_file_path):
                response_data.update({
                    "download_url": f"/report/{report_id}/download",
                    "filename": os.path.basename(abs_file_path),
                    "message": "Report is ready for download"
                })
            else:
                logger.error(f"[GET] Report {report_id} status is COMPLETED but file is missing: {abs_file_path}")
                response_data.update({
                    "message": "Report completed but file not found on server"
                })
                self.update_report_status(db, report_id, ReportStatus.ERROR.value)
                response_data["status"] = ReportStatus.ERROR.value
        elif status_value == ReportStatus.IN_PROGRESS.value:
            response_data["message"] = "Report generation in progress"
        elif status_value == ReportStatus.ERROR.value:
            response_data["message"] = "Report generation failed"
        else:
            response_data["message"] = "Unknown status"
        return response_data

    async def get_report_file_for_download(self, db: Session, report_id: int) -> str:

        report = self.get_report_by_id(db, report_id)
        if not report:
            logger.error(f"Report {report_id} not found for download")
            raise HTTPException(status_code=404, detail="Report not found")
        status_value = getattr(report, 'status', 'unknown')
        file_path = getattr(report, 'file', None)
        abs_file_path = os.path.abspath(file_path) if file_path else None

        if status_value != ReportStatus.COMPLETED.value:
            logger.error(f"Report {report_id} is not ready for download (status: {status_value})")
            raise HTTPException(status_code=400, detail="Report is not ready for download")

        if not abs_file_path or not os.path.exists(abs_file_path):
            logger.error(f"Report {report_id} file not found for download: {abs_file_path}")
            raise HTTPException(status_code=404, detail="Report file not found")

        return abs_file_path
import os
import uuid
from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enums.analysis import AnalysisStatusEnum
from constants.analysis import (
    ANALYSIS_EXTRACT_ERROR,
    ANALYSIS_STATUS_NOT_FOUND,
    ANALYSIS_FILE_PATH_TEMPLATE,
    ANALYSIS_EXCEL_MEDIA_TYPE,
)
from services.analysis import AnalysisService
from models.analysis import Analysis
import logging

analysis_service = AnalysisService()
logger = logging.getLogger(__name__)


def start_analysis_extraction(
    background_tasks: BackgroundTasks,
    vss_files: list[UploadFile],
    process_id: str,
    db: Session,
    namespace: str,
):
    from vector_store.pinecone_store import namespace_exists

    if not namespace_exists(namespace):
        raise HTTPException(
            status_code=400, detail=f"Pinecone namespace '{namespace}' does not exist."
        )
    vss_paths = []
    for file in vss_files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a name")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(
                status_code=400, detail="Only PDF and DOCX files are supported"
            )
        path = f"vss_uploads/{uuid.uuid4()}_{file.filename}"
        os.makedirs("vss_uploads", exist_ok=True)
        with open(path, "wb") as f:
            content = file.file.read()
            f.write(content)
        vss_paths.append(path)
    analysis = analysis_service.create_analysis(db)
    analysis_id = int(getattr(analysis, "id"))
    background_tasks.add_task(
        analysis_service.run_analysis, db, vss_paths, analysis_id, process_id, namespace
    )
    return {
        "analysis_id": analysis_id,
        "message": "Analysis started. Check status with GET /analysis/{analysis_id}",
    }


def get_analysis_status_controller(analysis_id: int, db: Session):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    status = str(getattr(analysis, "status", ""))
    output_file = str(getattr(analysis, "output_file", ""))
    if status == AnalysisStatusEnum.COMPLETED.value and output_file:
        return FileResponse(
            output_file,
            media_type=ANALYSIS_EXCEL_MEDIA_TYPE,
            filename="analysis_results.xlsx",
        )
    return analysis


async def generate_report_controller(
    excel_file_path: str,
    standard_name: str = "User Standard",
    standard_version: str = "1.0",
    standard_year: str = "2024",
    organization: str = "User Organization",
):
    """
    Controller function to generate summary report from analysis Excel file.

    Args:
        excel_file_path: Path to the Excel file containing analysis results
        standard_name: Name of the benchmarked standard
        standard_version: Version of the standard
        standard_year: Year of publication
        organization: Name of the founding organization

    Returns:
        FileResponse with the generated report
    """
    try:
        # Validate file exists
        if not os.path.exists(excel_file_path):
            raise HTTPException(status_code=404, detail="Excel file not found")

        # Generate report
        report_file_path = await analysis_service.generate_summary_report(
            excel_file_path=excel_file_path,
            standard_name=standard_name,
            standard_version=standard_version,
            standard_year=standard_year,
            organization=organization,
        )

        # Return the report file
        return FileResponse(
            report_file_path,
            media_type="text/markdown",
            filename="benchmarking_summary_report.md",
        )

    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )

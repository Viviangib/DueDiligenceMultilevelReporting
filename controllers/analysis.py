import os
from fastapi import BackgroundTasks, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from enums.analysis import AnalysisStatusEnum
from utils.constants import (
    AnalysisMessages,
    AnalysisPaths,
    AnalysisMediaTypes,
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
    from vectorstores.pinecone_retriever import namespace_exists

    if not namespace_exists(namespace):
        raise HTTPException(
            status_code=400, detail=f"Pinecone namespace '{namespace}' does not exist."
        )
    print(f"\n\nNamespace: {namespace}\n\n")
    vss_paths = []
    for file in vss_files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a name")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".pdf", ".docx"]:
            raise HTTPException(
                status_code=400, detail="Only PDF and DOCX files are supported"
            )
        from core.config import settings
        base_dir = settings.STORAGE_ROOT
        vss_dir = os.path.join(base_dir, settings.VSS_UPLOADS_DIR)
        os.makedirs(vss_dir, exist_ok=True)
        path = os.path.join(vss_dir, file.filename)
        with open(path, "wb") as f:
            content = file.file.read()
            f.write(content)
        vss_paths.append(path)
    analysis = analysis_service.create_analysis(db)
    analysis_id = int(getattr(analysis, "id"))
    background_tasks.add_task(
        analysis_service.run_analysis, vss_paths, analysis_id, process_id, namespace
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
            media_type=AnalysisMediaTypes.EXCEL.value,
            filename="analysis_results.xlsx",
        )
    return analysis

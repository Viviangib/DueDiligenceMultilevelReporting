import logging
import os
import uuid
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Depends,
    Form,
    Query,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from db import SessionLocal
from controllers.analysis import (
    start_analysis_extraction,
    get_analysis_status_controller,
    generate_report_controller,
)
from schemas.analysis import AnalysisOut
from utils.security import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["analysis"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/run", dependencies=[Depends(get_current_user)])
def run_analysis(
    background_tasks: BackgroundTasks,
    vss_files: list[UploadFile] = File(...),
    process_id: str = File(...),
    namespace: str = Form(..., description="Pinecone namespace to use for RAG search"),
    db: Session = Depends(get_db),
):
    from vector_store.pinecone_store import namespace_exists

    if not namespace_exists(namespace):
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400, detail=f"Pinecone namespace '{namespace}' does not exist."
        )
    return start_analysis_extraction(
        background_tasks, vss_files, process_id, db, namespace
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisOut,
    dependencies=[Depends(get_current_user)],
)
def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    return get_analysis_status_controller(analysis_id, db)


@router.post("/generate-report", dependencies=[Depends(get_current_user)])
async def generate_summary_report_from_upload(
    excel_file: UploadFile = File(
        ..., description="Excel file containing analysis results"
    ),
    standard_name: str = Form(
        "User Standard", description="Name of the benchmarked standard"
    ),
    standard_version: str = Form("1.0", description="Version of the standard"),
    standard_year: str = Form("2024", description="Year of publication"),
    organization: str = Form(
        "User Organization", description="Name of the founding organization"
    ),
):
    """
    Generate a comprehensive benchmarking summary report from uploaded Excel file.

    This endpoint accepts an Excel file upload containing analysis results and generates
    a professional benchmarking summary report following the GIB template format.

    The report includes:
    - General information about the standard
    - Abbreviations and definitions
    - Benchmarking results with alignment levels
    - Preliminary benchmarking summary
    - Recommendations and potential gaps
    - References and appendices
    """
    try:
        # Validate file type
        if not excel_file.filename:
            raise HTTPException(status_code=400, detail="File must have a name")

        ext = os.path.splitext(excel_file.filename)[1].lower()
        if ext not in [".xlsx", ".xls"]:
            raise HTTPException(
                status_code=400, detail="Only Excel files (.xlsx, .xls) are supported"
            )

        # Save uploaded file temporarily
        temp_file_path = f"temp_uploads/{uuid.uuid4()}_{excel_file.filename}"
        os.makedirs("temp_uploads", exist_ok=True)

        with open(temp_file_path, "wb") as f:
            content = excel_file.file.read()
            f.write(content)

        # Generate report
        report_response = await generate_report_controller(
            excel_file_path=temp_file_path,
            standard_name=standard_name,
            standard_version=standard_version,
            standard_year=standard_year,
            organization=organization,
        )

        # Clean up temporary file
        try:
            os.remove(temp_file_path)
        except:
            pass  # Ignore cleanup errors

        return report_response

    except Exception as e:
        logger.error(f"Report generation from upload failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Report generation failed: {str(e)}"
        )

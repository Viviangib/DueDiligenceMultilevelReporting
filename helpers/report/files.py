"""
Helper functions for report processing.
"""
import os
import logging
from typing import Optional
from fastapi import HTTPException, UploadFile
from core.config import settings

logger = logging.getLogger(__name__)

TEMP_UPLOAD_DIR = os.path.join(settings.STORAGE_ROOT, settings.TEMP_UPLOADS_DIR)
REPORTS_DIR = os.path.join(settings.STORAGE_ROOT, settings.SUMMARY_REPORTS_DIR)

# Ensure directories exist
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


async def save_temp_file(upload_file: UploadFile) -> str:
    """Save uploaded file to temporary directory."""
    filename = upload_file.filename or "unknown.xlsx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".xlsx", ".xls"]:
        logger.error(f"Rejected file with extension: {ext}")
        raise HTTPException(
            status_code=400, detail="Only Excel files (.xlsx, .xls) are supported"
        )
    file_path = os.path.abspath(os.path.join(TEMP_UPLOAD_DIR, filename))
    try:
        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved temp file at: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save uploaded file")


def cleanup_temp_file(file_path: str):
    """Clean up temporary file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up temp file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete temp file {file_path}: {e}")


def get_report_file_path() -> str:
    """Get the path for the report file."""
    return os.path.abspath(os.path.join(REPORTS_DIR, "benchmarking_summary_report.docx"))


def get_template_path() -> str:
    """Get the path for the report template."""
    return os.path.abspath(os.path.join(REPORTS_DIR, "template.docx"))


def get_css_path() -> str:
    """Get the path for the report CSS."""
    return os.path.abspath(os.path.join(REPORTS_DIR, "template.css"))


def prepare_pypandoc_args(template_path: str, css_path: str) -> list:
    """Prepare arguments for pypandoc conversion."""
    if not os.path.exists(template_path):
        logger.warning(f"Template file not found at {template_path}, using default styling")
        template_args = ['--standalone']
    else:
        logger.info(f"Using professional template: {template_path}")
        template_args = ['--standalone', f'--reference-doc={template_path}']
    
    enhanced_args = template_args + [
        '--wrap=auto',
        '--toc',  # Add table of contents
        f'--css={css_path}' if os.path.exists(css_path) else ''
    ]
    
    # Remove empty CSS argument if file doesn't exist
    return [arg for arg in enhanced_args if arg]

"""
Consolidated constants for the application.
"""
from enum import Enum


# =============================================================================
# ANALYSIS ENUMS
# =============================================================================

class AnalysisMessages(Enum):
    """Analysis-related error messages."""
    EXTRACT_ERROR = "Analysis extraction failed: {}"
    STATUS_NOT_FOUND = "AnalysisStatus with id {} not found."


class AnalysisPaths(Enum):
    """Analysis-related file paths."""
    FILE_PATH_TEMPLATE = "storage/analysis/llm_results_{}.xlsx"


class AnalysisMediaTypes(Enum):
    """Analysis-related media types."""
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# =============================================================================
# INDICATOR ENUMS
# =============================================================================

class IndicatorMessages(Enum):
    """Indicator-related error messages."""
    EXTRACT_ERROR = "Indicator extraction failed: {}"
    STATUS_NOT_FOUND = "IndicatorStatus with id {} not found."


class IndicatorPaths(Enum):
    """Indicator-related file paths."""
    FILE_PATH_TEMPLATE = "storage/indicators/extract_{}.xlsx"


class IndicatorMediaTypes(Enum):
    """Indicator-related media types."""
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# =============================================================================
# REPORT ENUMS
# =============================================================================

class ReportMediaTypes(Enum):
    """Report-related media types."""
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"



from enum import Enum

class ReportStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    ERROR = "error"
    COMPLETED = "completed"
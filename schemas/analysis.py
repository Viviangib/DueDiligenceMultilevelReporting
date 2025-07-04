from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnalysisBase(BaseModel):
    status: str
    output_file: Optional[str] = None

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisOut(AnalysisBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True 
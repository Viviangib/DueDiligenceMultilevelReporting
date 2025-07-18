from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enums.analysis import AnalysisStatusEnum


class AnalysisSchema(BaseModel):
    id: int
    status: AnalysisStatusEnum
    output_file: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


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

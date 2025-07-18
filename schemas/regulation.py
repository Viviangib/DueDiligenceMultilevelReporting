"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class RegulationBase(BaseModel):
    """Base schema for regulation."""

    name: str
    file_type: str


class RegulationCreate(RegulationBase):
    """Schema for creating a regulation."""

    pass


class RegulationStatus(BaseModel):
    regulation_id: int
    embedding_status: str


class Regulation(RegulationBase):
    id: int
    created_at: datetime
    embedding_status: str
    pinecone_namespace: str

    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    indicator_id: str
    indicator_text: str
    alignment_level: str
    justification: str
    evidence: str


class AnalysisResultBase(BaseModel):
    """Base schema for analysis result."""

    indicator_id: str
    indicator_text: str
    alignment_level: str
    justification: str
    evidence: str


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating an analysis result."""

    regulation_id: int


class AnalysisResultResponse(AnalysisResultBase):
    """Schema for analysis result response."""

    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisBatchResponse(BaseModel):
    """Schema for batch analysis response."""

    regulation_id: int
    results: List[AnalysisResultResponse]
    excel_url: Optional[str] = None

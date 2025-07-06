from pydantic import BaseModel
from datetime import datetime

class IndicatorStatusBase(BaseModel):
    status: str

class IndicatorStatusCreate(IndicatorStatusBase):
    pass

class IndicatorStatusOut(IndicatorStatusBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True 
from pydantic import BaseModel
from typing import Optional
from enums.indicator import IndicatorStatusEnum


class IndicatorStatusSchema(BaseModel):
    id: int
    status: IndicatorStatusEnum
    created_at: Optional[str]
    file: Optional[str]

    class Config:
        orm_mode = True

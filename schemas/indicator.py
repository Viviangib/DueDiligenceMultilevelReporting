from pydantic import BaseModel
from typing import Any


class IndicatorBase(BaseModel):
    indicator: Any


class IndicatorCreate(IndicatorBase):
    pass


class Indicator(IndicatorBase):
    id: int

    class Config:
        from_attributes = True

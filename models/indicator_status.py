from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from datetime import datetime
from enums.indicator import IndicatorStatusEnum


class IndicatorStatus(Base):
    __tablename__ = "indicator_statuses"
    __allow_unmapped__ = True
    id = Column(Integer, primary_key=True, index=True)
    status = Column(
        String, default=IndicatorStatusEnum.IN_PROGRESS.value
    )  # in_progress, completed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    file = Column(String, nullable=True)  # Path to the generated Excel file

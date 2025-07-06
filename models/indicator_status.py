from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from datetime import datetime

class IndicatorStatus(Base):
    __tablename__ = "indicator_statuses"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="in_progress")  # in_progress, completed, error
    created_at = Column(DateTime, default=datetime.utcnow) 
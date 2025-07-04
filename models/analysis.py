from sqlalchemy import Column, Integer, String, DateTime
from db import Base
from datetime import datetime

class Analysis(Base):
    __tablename__ = "analysis"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="in_progress")  # in_progress, error, completed
    output_file = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow) 
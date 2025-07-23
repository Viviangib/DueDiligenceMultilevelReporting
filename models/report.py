from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Report(Base):
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    status = Column(String, nullable=False)
    file = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    
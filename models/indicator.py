from sqlalchemy import Column, Integer, JSON
from db import Base

class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(JSON, nullable=False) 
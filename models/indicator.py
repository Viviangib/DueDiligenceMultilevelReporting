from sqlalchemy import Column, Integer, Text
from db import Base

class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True, index=True)
    indicator = Column(Text, nullable=False) 
from sqlalchemy import Column, Integer, String
from db import Base


class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True, index=True)
    indicator_id = Column(String, nullable=False)
    indicator = Column(String, nullable=False)
    process_id = Column(String, index=True, nullable=False)

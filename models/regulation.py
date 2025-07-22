"""Models for regulations and analysis results."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from db import Base


class Regulation(Base):
    """Model for storing regulation information."""

    __tablename__ = "regulations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    embedding_status = Column(String, default="in process")
    pinecone_namespace = Column(String, unique=False)

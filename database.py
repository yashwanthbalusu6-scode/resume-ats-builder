"""SQLite database models."""
import os
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///resume_tracker.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class ApplicationRecord(Base):
    """Track job applications."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    job_title = Column(String(200))
    company = Column(String(200))
    date_applied = Column(DateTime, default=datetime.utcnow)
    resume_version = Column(String(100))
    ats_score = Column(Integer)
    status = Column(String(50), default="applied")
    notes = Column(Text, default="")


def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass


def get_session() -> Any:
    return SessionLocal()

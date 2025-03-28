	from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Enum as SQLAlchemyEnum, 
    ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class JobStatus(str, Enum):
    """Enum representing the status of a batch job."""
    ACTIVE = "active"
    PAUSED = "paused"


class WebexRecording(Base):
    """SQLAlchemy model for Webex recordings."""
    __tablename__ = "webex_recordings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recording_id = Column(String(255), unique=True, nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    host_email = Column(String(255), nullable=False)
    creation_time = Column(DateTime, nullable=False)
    duration = Column(Integer, nullable=False)  # Duration in seconds
    size_bytes = Column(Integer, nullable=False)
    format = Column(String(50), nullable=False)
    webex_download_url = Column(Text, nullable=False)
    
    # Storage information
    minio_bucket = Column(String(255), nullable=True)
    minio_object_path = Column(String(512), nullable=True)
    download_completed = Column(Boolean, default=False, nullable=False)
    download_time = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    download_job_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=True)
    download_job = relationship("BatchJob", back_populates="recordings")

    def __repr__(self):
        return f"<WebexRecording(id={self.id}, recording_id='{self.recording_id}', topic='{self.topic}')>"


class BatchJob(Base):
    """SQLAlchemy model for batch jobs."""
    __tablename__ = "batch_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    status = Column(SQLAlchemyEnum(JobStatus), default=JobStatus.ACTIVE, nullable=False)
    interval_minutes = Column(Integer, default=60, nullable=False)
    last_run_time = Column(DateTime, nullable=True)
    next_run_time = Column(DateTime, nullable=True)
    
    # Job configuration
    from_date = Column(DateTime, nullable=True)
    to_date = Column(DateTime, nullable=True)
    host_email_filter = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    recordings = relationship("WebexRecording", back_populates="download_job")

    def __repr__(self):
        return f"<BatchJob(id={self.id}, name='{self.name}', status={self.status})>"


class JobExecutionLog(Base):
    """SQLAlchemy model for job execution logs."""
    __tablename__ = "job_execution_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("batch_jobs.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=False)  # success, failure, in_progress
    recordings_found = Column(Integer, default=0, nullable=False)
    recordings_downloaded = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship
    job = relationship("BatchJob")

    def __repr__(self):
        return f"<JobExecutionLog(id={self.id}, job_id={self.job_id}, status='{self.status}')>"
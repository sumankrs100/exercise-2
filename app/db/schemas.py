from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator


class WebexRecordingBase(BaseModel):
    """Base Pydantic model for Webex recordings."""
    recording_id: str
    topic: str
    host_email: str
    creation_time: datetime
    duration: int
    size_bytes: int
    format: str
    webex_download_url: str


class WebexRecordingCreate(WebexRecordingBase):
    """Pydantic model for creating a Webex recording."""
    pass


class WebexRecordingUpdate(BaseModel):
    """Pydantic model for updating a Webex recording."""
    minio_bucket: Optional[str] = None
    minio_object_path: Optional[str] = None
    download_completed: Optional[bool] = None
    download_time: Optional[datetime] = None


class WebexRecordingResponse(WebexRecordingBase):
    """Pydantic model for Webex recording response."""
    id: int
    minio_bucket: Optional[str] = None
    minio_object_path: Optional[str] = None
    download_completed: bool
    download_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    download_job_id: Optional[int] = None

    class Config:
        from_attributes = True


class BatchJobBase(BaseModel):
    """Base Pydantic model for batch jobs."""
    name: str
    status: str = "active"
    interval_minutes: int = 60
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    host_email_filter: Optional[str] = None


class BatchJobCreate(BatchJobBase):
    """Pydantic model for creating a batch job."""
    pass


class BatchJobUpdate(BaseModel):
    """Pydantic model for updating a batch job."""
    name: Optional[str] = None
    status: Optional[str] = None
    interval_minutes: Optional[int] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    host_email_filter: Optional[str] = None
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None


class BatchJobResponse(BatchJobBase):
    """Pydantic model for batch job response."""
    id: int
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobExecutionLogBase(BaseModel):
    """Base Pydantic model for job execution logs."""
    job_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    recordings_found: int = 0
    recordings_downloaded: int = 0
    error_message: Optional[str] = None


class JobExecutionLogCreate(JobExecutionLogBase):
    """Pydantic model for creating a job execution log."""
    pass


class JobExecutionLogUpdate(BaseModel):
    """Pydantic model for updating a job execution log."""
    end_time: Optional[datetime] = None
    status: Optional[str] = None
    recordings_found: Optional[int] = None
    recordings_downloaded: Optional[int] = None
    error_message: Optional[str] = None


class JobExecutionLogResponse(JobExecutionLogBase):
    """Pydantic model for job execution log response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
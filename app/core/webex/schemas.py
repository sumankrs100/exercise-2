from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WebexRecordingResponse(BaseModel):
    """Pydantic model for Webex API recording response."""
    recording_id: str = Field(..., description="Unique ID of the recording")
    topic: str = Field(..., description="Recording topic/name")
    host_email: str = Field(..., description="Email of the recording host")
    creation_time: datetime = Field(..., description="Time the recording was created")
    duration: int = Field(..., description="Duration of the recording in seconds")
    size_bytes: int = Field(..., description="Size of the recording in bytes")
    format: str = Field(..., description="Format of the recording (e.g., mp4)")
    webex_download_url: str = Field(..., description="URL for downloading the recording")
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.db.schemas import WebexRecordingResponse
from app.services.recording_service import RecordingService

router = APIRouter(prefix="/recordings", tags=["recordings"])
recording_service = RecordingService()


@router.get("/", response_model=List[WebexRecordingResponse])
async def get_recordings(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    host_email: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recordings with optional filters.
    
    Args:
        from_date: Filter recordings from this date
        to_date: Filter recordings to this date
        host_email: Filter recordings by host email
        skip: Number of recordings to skip
        limit: Maximum number of recordings to return
        
    Returns:
        List of recordings
    """
    recordings = recording_service.get_recordings(
        db, from_date, to_date, host_email, skip, limit
    )
    
    return recordings


@router.get("/undownloaded", response_model=List[WebexRecordingResponse])
async def get_undownloaded_recordings(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recordings that haven't been downloaded yet.
    
    Args:
        limit: Maximum number of recordings to return
        
    Returns:
        List of undownloaded recordings
    """
    recordings = recording_service.get_undownloaded_recordings(db, limit)
    return recordings


@router.get("/{recording_id}", response_model=WebexRecordingResponse)
async def get_recording(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a recording by ID.
    
    Args:
        recording_id: Database ID of the recording
        
    Returns:
        Recording details
    """
    recording = recording_service.get_recording(db, recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    return recording


@router.post("/fetch", response_model=List[WebexRecordingResponse])
async def fetch_recordings(
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    host_email: Optional[str] = Query(None),
    max_recordings: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Fetch recordings from Webex API.
    
    Args:
        from_date: Filter recordings from this date
        to_date: Filter recordings to this date
        host_email: Filter recordings by host email
        max_recordings: Maximum number of recordings to retrieve
        
    Returns:
        List of fetched recordings
    """
    recordings, _ = await recording_service.fetch_recordings(
        db, from_date, to_date, host_email, max_recordings
    )
    
    return recordings


@router.post("/{recording_id}/download", response_model=WebexRecordingResponse)
async def download_recording(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Download a recording from Webex and store it in MinIO.
    
    Args:
        recording_id: Database ID of the recording
        
    Returns:
        Updated recording details
    """
    recording = recording_service.get_recording(db, recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if recording.download_completed:
        raise HTTPException(status_code=400, detail="Recording already downloaded")
    
    try:
        updated_recording = await recording_service.download_recording(db, recording_id)
        return updated_recording
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading recording: {str(e)}")


@router.get("/{recording_id}/download-url")
async def get_download_url(
    recording_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a download URL for a recording.
    
    Args:
        recording_id: Database ID of the recording
        
    Returns:
        Presigned URL for downloading the recording
    """
    recording = recording_service.get_recording(db, recording_id)
    
    if not recording:
        raise HTTPException(status_code=404, detail="Recording not found")
    
    if not recording.download_completed:
        raise HTTPException(status_code=400, detail="Recording not yet downloaded")
    
    download_url = recording_service.get_download_url(db, recording_id)
    
    if not download_url:
        raise HTTPException(status_code=500, detail="Error generating download URL")
    
    return {"download_url": download_url}
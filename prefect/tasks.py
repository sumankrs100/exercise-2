import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from prefect import task

from app.db.connection import db_session
from app.db.models import BatchJob, WebexRecording
from app.services.job_service import JobService
from app.services.recording_service import RecordingService


@task(name="fetch_webex_recordings")
async def fetch_webex_recordings(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    host_email: Optional[str] = None,
    max_recordings: int = 100
) -> Tuple[int, int]:
    """
    Fetch recordings from Webex API.
    
    Args:
        from_date: Filter recordings from this date
        to_date: Filter recordings to this date
        host_email: Filter recordings by host email
        max_recordings: Maximum number of recordings to retrieve
        
    Returns:
        Tuple of total recordings count and new recordings count
    """
    recording_service = RecordingService()
    
    with db_session() as db:
        recordings, new_count = await recording_service.fetch_recordings(
            db, from_date, to_date, host_email, max_recordings
        )
        
        return len(recordings), new_count


@task(name="download_recording")
async def download_recording(recording_id: int) -> bool:
    """
    Download a recording from Webex and store it in MinIO.
    
    Args:
        recording_id: Database ID of the recording
        
    Returns:
        Success flag
    """
    recording_service = RecordingService()
    
    with db_session() as db:
        try:
            updated_recording = await recording_service.download_recording(db, recording_id)
            return updated_recording is not None
        except Exception as e:
            logging.error(f"Error downloading recording {recording_id}: {e}")
            return False


@task(name="download_undownloaded_recordings")
async def download_undownloaded_recordings(limit: int = 10) -> Tuple[int, int]:
    """
    Download recordings that haven't been downloaded yet.
    
    Args:
        limit: Maximum number of recordings to download
        
    Returns:
        Tuple of total undownloaded recordings and successfully downloaded count
    """
    recording_service = RecordingService()
    
    with db_session() as db:
        undownloaded = recording_service.get_undownloaded_recordings(db, limit)
        
        total = len(undownloaded)
        success_count = 0
        
        for recording in undownloaded:
            try:
                updated_recording = await recording_service.download_recording(db, recording.id)
                if updated_recording:
                    success_count += 1
            except Exception as e:
                logging.error(f"Error downloading recording {recording.id}: {e}")
        
        return total, success_count


@task(name="execute_batch_job")
async def execute_batch_job(job_id: int) -> Tuple[bool, str]:
    """
    Execute a batch job.
    
    Args:
        job_id: ID of the job to execute
        
    Returns:
        Tuple of success flag and message
    """
    job_service = JobService()
    
    with db_session() as db:
        return await job_service.execute_job(db, job_id)


@task(name="execute_due_jobs")
async def execute_due_jobs() -> Dict[int, bool]:
    """
    Execute all batch jobs that are due for execution.
    
    Returns:
        Dictionary mapping job IDs to success flags
    """
    job_service = JobService()
    results = {}
    
    with db_session() as db:
        due_jobs = job_service.get_jobs_due_for_execution(db)
        
        for job in due_jobs:
            success, _ = await job_service.execute_job(db, job.id)
            results[job.id] = success
    
    return results
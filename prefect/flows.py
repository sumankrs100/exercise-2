from datetime import datetime, timedelta
from typing import Optional

from prefect import flow, task

from prefect.tasks import (
    download_recording,
    download_undownloaded_recordings,
    execute_batch_job,
    execute_due_jobs,
    fetch_webex_recordings
)


@flow(name="webex_recording_sync_flow")
async def webex_recording_sync_flow(
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    host_email: Optional[str] = None,
    max_recordings: int = 100,
    download_limit: int = 10
):
    """
    Flow to synchronize Webex recordings.
    
    Args:
        from_date: Filter recordings from this date
        to_date: Filter recordings to this date
        host_email: Filter recordings by host email
        max_recordings: Maximum number of recordings to retrieve
        download_limit: Maximum number of recordings to download
    """
    # Set default dates if not provided
    if not from_date:
        from_date = datetime.utcnow() - timedelta(days=7)
    
    if not to_date:
        to_date = datetime.utcnow()
    
    # Fetch recordings from Webex
    total_count, new_count = await fetch_webex_recordings(
        from_date, to_date, host_email, max_recordings
    )
    
    # Download undownloaded recordings
    undownloaded_count, downloaded_count = await download_undownloaded_recordings(
        download_limit
    )
    
    return {
        "total_recordings": total_count,
        "new_recordings": new_count,
        "undownloaded_count": undownloaded_count,
        "downloaded_count": downloaded_count
    }


@flow(name="execute_batch_job_flow")
async def execute_batch_job_flow(job_id: int):
    """
    Flow to execute a batch job.
    
    Args:
        job_id: ID of the job to execute
    """
    success, message = await execute_batch_job(job_id)
    
    return {
        "job_id": job_id,
        "success": success,
        "message": message
    }


@flow(name="execute_due_jobs_flow")
async def execute_due_jobs_flow():
    """Flow to execute all batch jobs that are due for execution."""
    results = await execute_due_jobs()
    
    successful = sum(1 for success in results.values() if success)
    failed = len(results) - successful
    
    return {
        "total_jobs": len(results),
        "successful_jobs": successful,
        "failed_jobs": failed,
        "results": results
    }
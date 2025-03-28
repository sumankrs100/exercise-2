from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.db.models import JobStatus
from app.db.schemas import (
    BatchJobCreate, BatchJobResponse, BatchJobUpdate,
    JobExecutionLogResponse
)
from app.services.job_service import JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])
job_service = JobService()


@router.get("/", response_model=List[BatchJobResponse])
async def get_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all batch jobs with pagination.
    
    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return
        
    Returns:
        List of jobs
    """
    jobs = job_service.get_jobs(db, skip, limit)
    return jobs


@router.post("/", response_model=BatchJobResponse)
async def create_job(
    job_data: BatchJobCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new batch job.
    
    Args:
        job_data: Data for the new job
        
    Returns:
        Created job
    """
    # Check if a job with the same name already exists
    existing_job = job_service.get_job_by_name(db, job_data.name)
    
    if existing_job:
        raise HTTPException(
            status_code=400,
            detail=f"Job with name '{job_data.name}' already exists"
        )
    
    return job_service.create_job(db, job_data)


@router.get("/{job_id}", response_model=BatchJobResponse)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a batch job by ID.
    
    Args:
        job_id: ID of the job
        
    Returns:
        Job details
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job


@router.put("/{job_id}", response_model=BatchJobResponse)
async def update_job(
    job_id: int,
    job_data: BatchJobUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a batch job.
    
    Args:
        job_id: ID of the job to update
        job_data: Data to update
        
    Returns:
        Updated job
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if the job name is being updated and if it already exists
    if job_data.name and job_data.name != job.name:
        existing_job = job_service.get_job_by_name(db, job_data.name)
        
        if existing_job:
            raise HTTPException(
                status_code=400,
                detail=f"Job with name '{job_data.name}' already exists"
            )
    
    return job_service.update_job(db, job_id, job_data)


@router.post("/{job_id}/start", response_model=BatchJobResponse)
async def start_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Start a batch job.
    
    Args:
        job_id: ID of the job to start
        
    Returns:
        Updated job
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Job is already active")
    
    return job_service.start_job(db, job_id)


@router.post("/{job_id}/pause", response_model=BatchJobResponse)
async def pause_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Pause a batch job.
    
    Args:
        job_id: ID of the job to pause
        
    Returns:
        Updated job
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == JobStatus.PAUSED:
        raise HTTPException(status_code=400, detail="Job is already paused")
    
    return job_service.pause_job(db, job_id)


@router.post("/{job_id}/execute")
async def execute_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Execute a batch job immediately.
    
    Args:
        job_id: ID of the job to execute
        
    Returns:
        Execution result
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    success, message = await job_service.execute_job(db, job_id)
    
    return {
        "success": success,
        "message": message
    }


@router.get("/{job_id}/logs", response_model=List[JobExecutionLogResponse])
async def get_job_logs(
    job_id: int,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    Get execution logs for a job.
    
    Args:
        job_id: ID of the job
        limit: Maximum number of logs to return
        
    Returns:
        List of execution logs
    """
    job = job_service.get_job(db, job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logs = job_service.get_execution_logs(db, job_id, limit)
    return logs
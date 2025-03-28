from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.db.models import BatchJob, JobExecutionLog, JobStatus
from app.db.repositories.base import BaseRepository
from app.db.schemas import BatchJobCreate, BatchJobUpdate, JobExecutionLogCreate, JobExecutionLogUpdate


class BatchJobRepository(BaseRepository[BatchJob, BatchJobCreate, BatchJobUpdate]):
    """Repository for BatchJob model."""

    def __init__(self):
        super().__init__(BatchJob)

    def get_by_name(self, db: Session, name: str) -> Optional[BatchJob]:
        """
        Get a batch job by name.
        
        Args:
            db: Database session
            name: Job name
            
        Returns:
            BatchJob or None if not found
        """
        return db.query(BatchJob).filter(BatchJob.name == name).first()

    def get_active_jobs(self, db: Session) -> List[BatchJob]:
        """
        Get all active batch jobs.
        
        Args:
            db: Database session
            
        Returns:
            List of active batch jobs
        """
        return db.query(BatchJob).filter(BatchJob.status == JobStatus.ACTIVE).all()

    def get_jobs_due_for_execution(self, db: Session) -> List[BatchJob]:
        """
        Get batch jobs that are due for execution.
        
        Jobs are due if:
        1. They are active
        2. They have never run (next_run_time is None) or
           their next_run_time is in the past
        
        Args:
            db: Database session
            
        Returns:
            List of jobs due for execution
        """
        now = datetime.utcnow()
        
        return db.query(BatchJob).filter(
            and_(
                BatchJob.status == JobStatus.ACTIVE,
                or_(
                    BatchJob.next_run_time == None,
                    BatchJob.next_run_time <= now
                )
            )
        ).all()

    def update_job_run_times(
        self, db: Session, job_id: int, last_run_time: datetime = None
    ) -> BatchJob:
        """
        Update a job's run times.
        
        Args:
            db: Database session
            job_id: ID of the job to update
            last_run_time: Time the job was last run (defaults to now)
            
        Returns:
            Updated job
        """
        job = self.get(db, job_id)
        
        if not job:
            return None
        
        if last_run_time is None:
            last_run_time = datetime.utcnow()
        
        # Calculate the next run time based on the interval
        next_run_time = last_run_time + timedelta(minutes=job.interval_minutes)
        
        update_data = BatchJobUpdate(
            last_run_time=last_run_time,
            next_run_time=next_run_time
        )
        
        return self.update(db, db_obj=job, obj_in=update_data)

    def change_job_status(self, db: Session, job_id: int, status: JobStatus) -> BatchJob:
        """
        Change a job's status.
        
        Args:
            db: Database session
            job_id: ID of the job to update
            status: New status
            
        Returns:
            Updated job
        """
        job = self.get(db, job_id)
        
        if not job:
            return None
        
        update_data = BatchJobUpdate(status=status)
        return self.update(db, db_obj=job, obj_in=update_data)


class JobExecutionLogRepository(BaseRepository[JobExecutionLog, JobExecutionLogCreate, JobExecutionLogUpdate]):
    """Repository for JobExecutionLog model."""

    def __init__(self):
        super().__init__(JobExecutionLog)

    def get_logs_for_job(
        self, db: Session, job_id: int, limit: int = 100
    ) -> List[JobExecutionLog]:
        """
        Get execution logs for a specific job.
        
        Args:
            db: Database session
            job_id: ID of the job
            limit: Maximum number of logs to return
            
        Returns:
            List of execution logs
        """
        return db.query(JobExecutionLog).filter(
            JobExecutionLog.job_id == job_id
        ).order_by(JobExecutionLog.start_time.desc()).limit(limit).all()

    def start_execution(self, db: Session, job_id: int) -> JobExecutionLog:
        """
        Create a new execution log entry for a job start.
        
        Args:
            db: Database session
            job_id: ID of the job
            
        Returns:
            Created execution log
        """
        now = datetime.utcnow()
        
        log_data = JobExecutionLogCreate(
            job_id=job_id,
            start_time=now,
            status="in_progress",
            recordings_found=0,
            recordings_downloaded=0
        )
        
        return self.create(db, obj_in=log_data)

    def complete_execution(
        self,
        db: Session,
        log_id: int,
        status: str,
        recordings_found: int,
        recordings_downloaded: int,
        error_message: str = None
    ) -> JobExecutionLog:
        """
        Update an execution log entry when a job completes.
        
        Args:
            db: Database session
            log_id: ID of the execution log
            status: Final status (success or failure)
            recordings_found: Number of recordings found
            recordings_downloaded: Number of recordings downloaded
            error_message: Error message if the job failed
            
        Returns:
            Updated execution log
        """
        log = self.get(db, log_id)
        
        if not log:
            return None
        
        update_data = JobExecutionLogUpdate(
            end_time=datetime.utcnow(),
            status=status,
            recordings_found=recordings_found,
            recordings_downloaded=recordings_downloaded,
            error_message=error_message
        )
        
        return self.update(db, db_obj=log, obj_in=update_data)
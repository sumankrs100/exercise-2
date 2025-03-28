import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.db.models import BatchJob, JobExecutionLog, JobStatus
from app.db.repositories.job_repository import BatchJobRepository, JobExecutionLogRepository
from app.db.schemas import BatchJobCreate, BatchJobUpdate
from app.services.recording_service import RecordingService

logger = logging.getLogger(__name__)


class JobService:
    """Service for handling batch job operations."""

    def __init__(self):
        self.job_repository = BatchJobRepository()
        self.log_repository = JobExecutionLogRepository()
        self.recording_service = RecordingService()

    def create_job(self, db: Session, job_data: BatchJobCreate) -> BatchJob:
        """
        Create a new batch job.
        
        Args:
            db: Database session
            job_data: Data for the new job
            
        Returns:
            Created job
        """
        return self.job_repository.create(db, obj_in=job_data)

    def update_job(
        self, db: Session, job_id: int, job_data: BatchJobUpdate
    ) -> Optional[BatchJob]:
        """
        Update a batch job.
        
        Args:
            db: Database session
            job_id: ID of the job to update
            job_data: Data to update
            
        Returns:
            Updated job or None if not found
        """
        job = self.job_repository.get(db, job_id)
        
        if not job:
            return None
        
        return self.job_repository.update(db, db_obj=job, obj_in=job_data)

    def get_job(self, db: Session, job_id: int) -> Optional[BatchJob]:
        """
        Get a batch job by ID.
        
        Args:
            db: Database session
            job_id: ID of the job
            
        Returns:
            Job or None if not found
        """
        return self.job_repository.get(db, job_id)

    def get_job_by_name(self, db: Session, name: str) -> Optional[BatchJob]:
        """
        Get a batch job by name.
        
        Args:
            db: Database session
            name: Name of the job
            
        Returns:
            Job or None if not found
        """
        return self.job_repository.get_by_name(db, name)

    def get_jobs(self, db: Session, skip: int = 0, limit: int = 100) -> List[BatchJob]:
        """
        Get all batch jobs with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of jobs
        """
        return self.job_repository.get_multi(db, skip=skip, limit=limit)

    def get_active_jobs(self, db: Session) -> List[BatchJob]:
        """
        Get all active batch jobs.
        
        Args:
            db: Database session
            
        Returns:
            List of active jobs
        """
        return self.job_repository.get_active_jobs(db)

    def get_jobs_due_for_execution(self, db: Session) -> List[BatchJob]:
        """
        Get batch jobs that are due for execution.
        
        Args:
            db: Database session
            
        Returns:
            List of jobs due for execution
        """
        return self.job_repository.get_jobs_due_for_execution(db)

    def start_job(self, db: Session, job_id: int) -> Optional[BatchJob]:
        """
        Start a batch job.
        
        Args:
            db: Database session
            job_id: ID of the job to start
            
        Returns:
            Updated job or None if not found
        """
        return self.job_repository.change_job_status(db, job_id, JobStatus.ACTIVE)

    def pause_job(self, db: Session, job_id: int) -> Optional[BatchJob]:
        """
        Pause a batch job.
        
        Args:
            db: Database session
            job_id: ID of the job to pause
            
        Returns:
            Updated job or None if not found
        """
        return self.job_repository.change_job_status(db, job_id, JobStatus.PAUSED)

    def get_execution_logs(
        self, db: Session, job_id: int, limit: int = 100
    ) -> List[JobExecutionLog]:
        """
        Get execution logs for a job.
        
        Args:
            db: Database session
            job_id: ID of the job
            limit: Maximum number of logs to return
            
        Returns:
            List of execution logs
        """
        return self.log_repository.get_logs_for_job(db, job_id, limit)

    async def execute_job(self, db: Session, job_id: int) -> Tuple[bool, str]:
        """
        Execute a batch job.
        
        Args:
            db: Database session
            job_id: ID of the job to execute
            
        Returns:
            Tuple of success flag and message
        """
        job = self.job_repository.get(db, job_id)
        
        if not job:
            return False, f"Job not found: {job_id}"
        
        if job.status != JobStatus.ACTIVE:
            return False, f"Job is not active: {job_id}"
        
        # Create execution log
        execution_log = self.log_repository.start_execution(db, job_id)
        
        try:
            # Fetch recordings from Webex
            recordings, new_count = await self.recording_service.fetch_recordings(
                db,
                from_date=job.from_date,
                to_date=job.to_date,
                host_email=job.host_email_filter
            )
            
            # Download undownloaded recordings
            undownloaded = self.recording_service.get_undownloaded_recordings(db)
            
            downloaded_count = 0
            for recording in undownloaded:
                try:
                    await self.recording_service.download_recording(db, recording.id)
                    downloaded_count += 1
                except Exception as e:
                    logger.error(f"Error downloading recording {recording.id}: {e}")
            
            # Update job run times
            self.job_repository.update_job_run_times(db, job_id)
            
            # Complete execution log
            self.log_repository.complete_execution(
                db,
                execution_log.id,
                "success",
                len(recordings),
                downloaded_count
            )
            
            return True, f"Job executed successfully: {job_id}"
        except Exception as e:
            # Complete execution log with error
            self.log_repository.complete_execution(
                db,
                execution_log.id,
                "failure",
                0,
                0,
                str(e)
            )
            
            logger.error(f"Error executing job {job_id}: {e}")
            return False, f"Error executing job: {str(e)}"
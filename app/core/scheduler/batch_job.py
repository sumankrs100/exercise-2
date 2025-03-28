import asyncio
import logging
import time
from datetime import datetime
from typing import List

from app.db.connection import db_session
from app.db.models import BatchJob, JobStatus
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


class BatchJobScheduler:
    """Scheduler for batch jobs."""

    def __init__(self, check_interval_seconds: int = 60):
        """
        Initialize the scheduler.
        
        Args:
            check_interval_seconds: Interval in seconds to check for due jobs
        """
        self.check_interval_seconds = check_interval_seconds
        self.job_service = JobService()
        self.running = False

    async def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        self.running = True
        logger.info("Starting batch job scheduler")
        
        try:
            while self.running:
                await self.check_and_execute_due_jobs()
                await asyncio.sleep(self.check_interval_seconds)
        except Exception as e:
            logger.error(f"Error in batch job scheduler: {e}")
            self.running = False
            raise

    def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping batch job scheduler")
        self.running = False

    async def check_and_execute_due_jobs(self):
        """Check for due jobs and execute them."""
        logger.debug("Checking for due jobs")
        
        with db_session() as db:
            # Get jobs that are due for execution
            due_jobs = self.job_service.get_jobs_due_for_execution(db)
            
            if not due_jobs:
                logger.debug("No jobs due for execution")
                return
            
            logger.info(f"Found {len(due_jobs)} jobs due for execution")
            
            for job in due_jobs:
                logger.info(f"Executing job: {job.name} (ID: {job.id})")
                
                try:
                    success, message = await self.job_service.execute_job(db, job.id)
                    
                    if success:
                        logger.info(f"Job executed successfully: {job.name} (ID: {job.id})")
                    else:
                        logger.error(f"Job execution failed: {job.name} (ID: {job.id}) - {message}")
                except Exception as e:
                    logger.error(f"Error executing job {job.name} (ID: {job.id}): {e}")
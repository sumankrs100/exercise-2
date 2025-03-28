import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.core.storage.minio_client import MinIOClient
from app.core.webex.client import WebexClient
from app.core.webex.schemas import WebexRecordingResponse
from app.db.models import WebexRecording
from app.db.repositories.recording_repository import RecordingRepository
from app.db.schemas import WebexRecordingCreate, WebexRecordingResponse as DBWebexRecordingResponse

logger = logging.getLogger(__name__)


class RecordingService:
    """Service for handling Webex recording operations."""

    def __init__(self):
        self.webex_client = WebexClient()
        self.minio_client = MinIOClient()
        self.recording_repository = RecordingRepository()

    async def fetch_recordings(
        self,
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        host_email: Optional[str] = None,
        max_recordings: int = 100
    ) -> Tuple[List[WebexRecording], int]:
        """
        Fetch recordings from Webex API and store them in the database.
        
        Args:
            db: Database session
            from_date: Filter recordings from this date
            to_date: Filter recordings to this date
            host_email: Filter recordings by host email
            max_recordings: Maximum number of recordings to retrieve
            
        Returns:
            Tuple containing list of recordings and count of new recordings
        """
        logger.info(f"Fetching recordings from Webex API")
        
        # Fetch recordings from Webex API
        recordings = await self.webex_client.get_recordings(
            from_date=from_date,
            to_date=to_date,
            host_email=host_email,
            max_recordings=max_recordings
        )
        
        # Count of new recordings
        new_count = 0
        
        # Store recordings in the database
        db_recordings = []
        
        for recording in recordings:
            # Check if the recording already exists
            existing_recording = self.recording_repository.get_by_recording_id(
                db, recording.recording_id
            )
            
            if existing_recording:
                # Recording already exists, add it to the list
                db_recordings.append(existing_recording)
                continue
            
            # Recording doesn't exist, create it
            recording_create = WebexRecordingCreate(
                recording_id=recording.recording_id,
                topic=recording.topic,
                host_email=recording.host_email,
                creation_time=recording.creation_time,
                duration=recording.duration,
                size_bytes=recording.size_bytes,
                format=recording.format,
                webex_download_url=recording.webex_download_url
            )
            
            db_recording = self.recording_repository.create(db, obj_in=recording_create)
            db_recordings.append(db_recording)
            new_count += 1
        
        logger.info(f"Fetched {len(recordings)} recordings, {new_count} new")
        
        return db_recordings, new_count

    async def download_recording(
        self, db: Session, recording_id: int
    ) -> Optional[WebexRecording]:
        """
        Download a recording from Webex and store it in MinIO.
        
        Args:
            db: Database session
            recording_id: Database ID of the recording
            
        Returns:
            Updated recording or None if not found
        """
        # Get the recording from the database
        recording = self.recording_repository.get(db, recording_id)
        
        if not recording:
            logger.error(f"Recording not found: {recording_id}")
            return None
        
        logger.info(f"Downloading recording: {recording.recording_id}")
        
        try:
            # Get a temporary download link
            download_url = await self.webex_client.get_recording_download_link(
                recording.recording_id
            )
            
            # Download the recording
            data = await self.webex_client.download_recording(download_url)
            
            # Upload to MinIO
            object_path = self.minio_client.upload_recording(
                recording_id=recording.recording_id,
                data=data,
                host_email=recording.host_email,
                creation_time=recording.creation_time,
                format=recording.format
            )
            
            # Mark as downloaded in the database
            updated_recording = self.recording_repository.mark_as_downloaded(
                db,
                recording_id,
                self.minio_client.bucket_name,
                object_path
            )
            
            logger.info(f"Successfully downloaded recording: {recording.recording_id}")
            
            return updated_recording
        except Exception as e:
            logger.error(f"Error downloading recording {recording.recording_id}: {e}")
            raise

    def get_recording(self, db: Session, recording_id: int) -> Optional[WebexRecording]:
        """
        Get a recording by ID.
        
        Args:
            db: Database session
            recording_id: Database ID of the recording
            
        Returns:
            Recording or None if not found
        """
        return self.recording_repository.get(db, recording_id)

    def get_recordings(
        self,
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        host_email: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WebexRecording]:
        """
        Get recordings with optional filters.
        
        Args:
            db: Database session
            from_date: Filter recordings from this date
            to_date: Filter recordings to this date
            host_email: Filter recordings by host email
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recordings
        """
        return self.recording_repository.get_recordings_by_date_range(
            db, from_date, to_date, host_email, skip, limit
        )

    def get_undownloaded_recordings(
        self, db: Session, limit: int = 10
    ) -> List[WebexRecording]:
        """
        Get recordings that haven't been downloaded yet.
        
        Args:
            db: Database session
            limit: Maximum number of recordings to return
            
        Returns:
            List of undownloaded recordings
        """
        return self.recording_repository.get_undownloaded_recordings(db, limit)

    def get_download_url(self, db: Session, recording_id: int) -> Optional[str]:
        """
        Get a download URL for a recording.
        
        Args:
            db: Database session
            recording_id: Database ID of the recording
            
        Returns:
            Presigned URL for downloading the recording or None if not found
        """
        recording = self.recording_repository.get(db, recording_id)
        
        if not recording or not recording.download_completed:
            return None
        
        return self.minio_client.get_download_url(recording.minio_object_path)
from datetime import datetime
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.db.models import WebexRecording
from app.db.repositories.base import BaseRepository
from app.db.schemas import WebexRecordingCreate, WebexRecordingUpdate


class RecordingRepository(BaseRepository[WebexRecording, WebexRecordingCreate, WebexRecordingUpdate]):
    """Repository for WebexRecording model."""

    def __init__(self):
        super().__init__(WebexRecording)

    def get_by_recording_id(self, db: Session, recording_id: str) -> Optional[WebexRecording]:
        """
        Get a recording by its Webex recording ID.
        
        Args:
            db: Database session
            recording_id: Webex recording ID
            
        Returns:
            WebexRecording or None if not found
        """
        return db.query(WebexRecording).filter(
            WebexRecording.recording_id == recording_id
        ).first()

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
        return db.query(WebexRecording).filter(
            WebexRecording.download_completed == False
        ).order_by(WebexRecording.creation_time.desc()).limit(limit).all()

    def get_recordings_by_date_range(
        self,
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        host_email: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[WebexRecording]:
        """
        Get recordings within a date range and optionally filtered by host.
        
        Args:
            db: Database session
            from_date: Start date for filtering
            to_date: End date for filtering
            host_email: Host email for filtering
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of recordings
        """
        query = db.query(WebexRecording)
        
        # Apply date range filter if provided
        if from_date or to_date:
            conditions = []
            if from_date:
                conditions.append(WebexRecording.creation_time >= from_date)
            if to_date:
                conditions.append(WebexRecording.creation_time <= to_date)
            
            query = query.filter(and_(*conditions))
        
        # Apply host email filter if provided
        if host_email:
            query = query.filter(WebexRecording.host_email == host_email)
        
        return query.order_by(WebexRecording.creation_time.desc()).offset(skip).limit(limit).all()

    def mark_as_downloaded(
        self,
        db: Session,
        recording_id: int,
        minio_bucket: str,
        minio_object_path: str
    ) -> WebexRecording:
        """
        Mark a recording as downloaded.
        
        Args:
            db: Database session
            recording_id: Database ID of the recording
            minio_bucket: MinIO bucket name
            minio_object_path: Path to the object in MinIO
            
        Returns:
            Updated recording
        """
        recording = self.get(db, recording_id)
        
        if recording:
            update_data = WebexRecordingUpdate(
                minio_bucket=minio_bucket,
                minio_object_path=minio_object_path,
                download_completed=True,
                download_time=datetime.utcnow()
            )
            
            return self.update(db, db_obj=recording, obj_in=update_data)
        
        return None
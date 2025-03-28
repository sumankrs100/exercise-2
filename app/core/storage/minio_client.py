import io
import logging
from datetime import datetime
from typing import Optional

from minio import Minio
from minio.error import S3Error

from app.config.settings import settings

logger = logging.getLogger(__name__)


class MinioException(Exception):
    """Exception raised for MinIO errors."""
    pass


class MinIOClient:
    """Client for interacting with MinIO storage."""

    def __init__(self):
        self.endpoint = settings.MINIO_ENDPOINT
        self.access_key = settings.MINIO_ACCESS_KEY
        self.secret_key = settings.MINIO_SECRET_KEY.get_secret_value()
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.secure = settings.MINIO_SECURE
        
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )
        
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Ensure that the configured bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                logger.info(f"Creating bucket: {self.bucket_name}")
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.debug(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket exists: {e}")
            raise MinioException(f"Error ensuring bucket exists: {e}")

    def upload_recording(
        self,
        recording_id: str,
        data: bytes,
        host_email: str,
        creation_time: datetime,
        format: str = "mp4"
    ) -> str:
        """
        Upload a recording to MinIO.
        
        Args:
            recording_id: Webex recording ID
            data: Recording data as bytes
            host_email: Email of the recording host
            creation_time: Time the recording was created
            format: Format of the recording (e.g., mp4)
            
        Returns:
            Path to the uploaded object in MinIO
        """
        # Create a path with a directory structure: /year/month/day/host_email/recording_id.format
        year = creation_time.strftime("%Y")
        month = creation_time.strftime("%m")
        day = creation_time.strftime("%d")
        
        # Sanitize host_email for use in object path
        safe_host_email = host_email.replace("@", "_at_").replace(".", "_")
        
        object_path = f"{year}/{month}/{day}/{safe_host_email}/{recording_id}.{format}"
        
        logger.info(f"Uploading recording {recording_id} to {self.bucket_name}/{object_path}")
        
        try:
            # Create a BytesIO object from the data
            data_bytes = io.BytesIO(data)
            
            # Upload the file to MinIO
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                data=data_bytes,
                length=len(data),
                content_type=f"video/{format}"
            )
            
            logger.info(f"Successfully uploaded recording {recording_id} to {self.bucket_name}/{object_path}")
            return object_path
        except S3Error as e:
            logger.error(f"Error uploading recording to MinIO: {e}")
            raise MinioException(f"Error uploading recording to MinIO: {e}")

    def get_download_url(self, object_path: str, expires_in_seconds: int = 3600) -> str:
        """
        Get a presigned URL for downloading a recording.
        
        Args:
            object_path: Path to the object in MinIO
            expires_in_seconds: Number of seconds until the URL expires
            
        Returns:
            Presigned URL for downloading the object
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_path,
                expires=expires_in_seconds
            )
            logger.debug(f"Generated presigned URL for {object_path}")
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise MinioException(f"Error generating presigned URL: {e}")

    def delete_recording(self, object_path: str) -> None:
        """
        Delete a recording from MinIO.
        
        Args:
            object_path: Path to the object in MinIO
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_path
            )
            logger.info(f"Deleted recording at {self.bucket_name}/{object_path}")
        except S3Error as e:
            logger.error(f"Error deleting recording from MinIO: {e}")
            raise MinioException(f"Error deleting recording from MinIO: {e}")
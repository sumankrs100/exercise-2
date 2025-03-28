import logging
from datetime import datetime
from typing import Dict, List, Optional

import httpx
from pydantic import ValidationError

from app.config.settings import settings
from app.core.webex.schemas import WebexRecordingResponse

logger = logging.getLogger(__name__)


class WebexAPIException(Exception):
    """Exception raised for Webex API errors."""
    pass


class WebexClient:
    """Client for interacting with the Webex API."""

    def __init__(self):
        self.base_url = "https://webexapis.com/v1"
        self.site_url = settings.WEBEX_SITE_URL
        self.api_key = settings.WEBEX_API_KEY.get_secret_value()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def get_recordings(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        host_email: Optional[str] = None,
        max_recordings: int = 100
    ) -> List[WebexRecordingResponse]:
        """
        Get recordings from the Webex API.
        
        Args:
            from_date: Filter recordings from this date
            to_date: Filter recordings to this date
            host_email: Filter recordings by host email
            max_recordings: Maximum number of recordings to retrieve
            
        Returns:
            List of WebexRecordingResponse objects
        """
        params = {
            "siteUrl": self.site_url,
            "max": max_recordings
        }
        
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        if host_email:
            params["hostEmail"] = host_email
        
        logger.info(f"Fetching recordings with params: {params}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/recordings",
                headers=self.headers,
                params=params
            )
            
            if response.status_code != 200:
                logger.error(f"Webex API error: {response.status_code} - {response.text}")
                raise WebexAPIException(
                    f"Error fetching recordings: {response.status_code} - {response.text}"
                )
            
            recordings = []
            for item in response.json().get("items", []):
                try:
                    recordings.append(self._parse_recording(item))
                except ValidationError as e:
                    logger.error(f"Error parsing recording: {e}")
            
            logger.info(f"Found {len(recordings)} recordings")
            return recordings

    async def get_recording_download_link(self, recording_id: str) -> str:
        """
        Get a temporary download link for a recording.
        
        Args:
            recording_id: ID of the recording
            
        Returns:
            Temporary download link for the recording
        """
        logger.info(f"Getting download link for recording: {recording_id}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/recordings/{recording_id}/download",
                headers=self.headers,
                follow_redirects=False
            )
            
            if response.status_code not in (302, 307):
                logger.error(f"Webex API error: {response.status_code} - {response.text}")
                raise WebexAPIException(
                    f"Error getting download link: {response.status_code} - {response.text}"
                )
            
            download_url = response.headers.get("Location")
            if not download_url:
                raise WebexAPIException("No download URL found in response")
            
            logger.info(f"Got download link for recording: {recording_id}")
            return download_url

    def _parse_recording(self, item: Dict) -> WebexRecordingResponse:
        """
        Parse a Webex recording API response.
        
        Args:
            item: Webex recording item
            
        Returns:
            WebexRecordingResponse object
        """
        creation_time = datetime.fromisoformat(item.get("createTime").replace("Z", "+00:00"))
        
        return WebexRecordingResponse(
            recording_id=item.get("id"),
            topic=item.get("topic", "Untitled Recording"),
            host_email=item.get("hostEmail"),
            creation_time=creation_time,
            duration=item.get("durationSeconds", 0),
            size_bytes=item.get("sizeBytes", 0),
            format=item.get("format", "mp4"),
            webex_download_url=f"{self.base_url}/recordings/{item.get('id')}/download",
        )

    async def download_recording(self, download_url: str) -> bytes:
        """
        Download a recording.
        
        Args:
            download_url: URL to download the recording from
            
        Returns:
            Recording data as bytes
        """
        logger.info(f"Downloading recording from: {download_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(download_url)
            
            if response.status_code != 200:
                logger.error(f"Error downloading recording: {response.status_code} - {response.text}")
                raise WebexAPIException(
                    f"Error downloading recording: {response.status_code} - {response.text}"
                )
            
            logger.info(f"Downloaded recording ({len(response.content)} bytes)")
            return response.content
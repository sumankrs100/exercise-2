#!/usr/bin/env python3
"""
MinIO File Uploader Module

This module provides a class to download files from URLs and upload them to a MinIO bucket.
MinIO credentials are read from environment variables.
"""

import os
import urllib.request
import tempfile
from typing import Optional, Union, Dict, Any
import logging
from urllib.parse import urlparse

# Import MinIO client
try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    raise ImportError("MinIO SDK not found. Install it using: pip install minio")


class MinioUploader:
    """
    Class for downloading files from URLs and uploading them to MinIO buckets.
    MinIO connection details are retrieved from environment variables.
    
    Required environment variables:
        - MINIO_ENDPOINT: MinIO server endpoint (e.g., 'minio.example.com:9000')
        - MINIO_ACCESS_KEY: MinIO access key
        - MINIO_SECRET_KEY: MinIO secret key
        - MINIO_SECURE: Whether to use HTTPS (True/False) - defaults to True if not set
    """

    def __init__(self, use_env_vars: bool = True, **kwargs):
        """
        Initialize MinioUploader with connection details.
        
        Args:
            use_env_vars: Whether to use environment variables for MinIO config.
                          If False, provide connection details in kwargs.
            kwargs: Optional connection parameters if not using environment variables:
                   - endpoint: MinIO server endpoint
                   - access_key: MinIO access key
                   - secret_key: MinIO secret key
                   - secure: Whether to use HTTPS (default: True)
        """
        self.logger = logging.getLogger(__name__)
        self._init_minio_client(use_env_vars, **kwargs)

    def _init_minio_client(self, use_env_vars: bool, **kwargs) -> None:
        """Initialize MinIO client with configuration."""
        if use_env_vars:
            # Get MinIO configuration from environment variables
            endpoint = os.environ.get('MINIO_ENDPOINT')
            access_key = os.environ.get('MINIO_ACCESS_KEY')
            secret_key = os.environ.get('MINIO_SECRET_KEY')
            secure_str = os.environ.get('MINIO_SECURE', 'True')
            secure = secure_str.lower() in ('true', 'yes', '1')
            
            # Check if required environment variables are set
            if not all([endpoint, access_key, secret_key]):
                raise ValueError(
                    "Required MinIO environment variables are not set. "
                    "Please set MINIO_ENDPOINT, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY."
                )
        else:
            # Get MinIO configuration from kwargs
            endpoint = kwargs.get('endpoint')
            access_key = kwargs.get('access_key')
            secret_key = kwargs.get('secret_key')
            secure = kwargs.get('secure', True)
            
            # Check if required parameters are provided
            if not all([endpoint, access_key, secret_key]):
                raise ValueError(
                    "Required MinIO connection parameters are not provided. "
                    "Please provide endpoint, access_key, and secret_key."
                )
        
        # Initialize MinIO client
        try:
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            self.logger.info(f"MinIO client initialized with endpoint: {endpoint}")
        except Exception as e:
            self.logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise

    def download_file(self, url: str, local_path: Optional[str] = None, verify_ssl: bool = True) -> str:
        """
        Download a file from a URL to a local path.
        
        Args:
            url: URL of the file to download
            local_path: Path where the file will be saved.
                        If None, a temporary file will be created.
            verify_ssl: Whether to verify SSL certificates (default: True).
                        Set to False to disable SSL verification.
        
        Returns:
            The path where the file was saved
        """
        try:
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid URL: {url}")
            
            # If no local path is provided, create a temporary file
            if local_path is None:
                # Extract filename from URL or use a random name
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"downloaded_file_{os.urandom(4).hex()}"
                
                # Create a temporary file
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, filename)
            
            self.logger.info(f"Downloading file from {url} to {local_path} (SSL verify: {verify_ssl})")
            
            # Create custom SSL context if needed
            if not verify_ssl:
                import ssl
                import urllib.request
                
                # Create a context that doesn't verify SSL certificates
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Download the file with custom SSL context
                with urllib.request.urlopen(url, context=ssl_context) as response:
                    with open(local_path, 'wb') as out_file:
                        out_file.write(response.read())
            else:
                # Use the standard method with SSL verification
                urllib.request.urlretrieve(url, local_path)
                
            self.logger.info(f"File downloaded successfully to {local_path}")
            
            return local_path
        except Exception as e:
            self.logger.error(f"Failed to download file from {url}: {str(e)}")
            raise

    def upload_to_minio(self, 
                        file_path: str, 
                        bucket_name: str, 
                        object_name: Optional[str] = None,
                        content_type: Optional[str] = None,
                        metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to a MinIO bucket.
        
        Args:
            file_path: Path to the local file to upload
            bucket_name: Name of the MinIO bucket
            object_name: Name of the object in the bucket. If None, the basename of file_path is used.
            content_type: Content type of the object. If None, it will be guessed.
            metadata: Optional metadata for the object
        
        Returns:
            Dictionary with upload details: 
            {'bucket': bucket_name, 'object_name': object_name, 'etag': etag, 'version_id': version_id}
        """
        try:
            # Check if the file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check if the bucket exists, create it if not
            if not self.client.bucket_exists(bucket_name):
                self.logger.info(f"Bucket {bucket_name} does not exist. Creating it.")
                self.client.make_bucket(bucket_name)
            
            # If object_name is not provided, use the basename of file_path
            if object_name is None:
                object_name = os.path.basename(file_path)
            
            # Get file size for logging
            file_size = os.path.getsize(file_path)
            
            self.logger.info(f"Uploading file {file_path} ({file_size} bytes) to MinIO bucket {bucket_name} as {object_name}")
            
            # Upload the file
            result = self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            
            upload_info = {
                'bucket': bucket_name,
                'object_name': object_name,
                'etag': result.etag,
                'version_id': result.version_id
            }
            
            self.logger.info(f"File uploaded successfully: {upload_info}")
            return upload_info
            
        except S3Error as e:
            self.logger.error(f"MinIO S3 error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to upload file to MinIO: {str(e)}")
            raise

    def download_and_upload(self, 
                           url: str, 
                           bucket_name: str, 
                           object_name: Optional[str] = None,
                           keep_local: bool = False,
                           content_type: Optional[str] = None,
                           metadata: Optional[Dict[str, str]] = None,
                           verify_ssl: bool = True) -> Dict[str, Any]:
        """
        Download a file from a URL and upload it to a MinIO bucket.
        
        Args:
            url: URL of the file to download
            bucket_name: Name of the MinIO bucket
            object_name: Name of the object in the bucket. If None, will be extracted from the URL.
            keep_local: Whether to keep the local file after upload (default: False)
            content_type: Content type of the object. If None, it will be guessed.
            metadata: Optional metadata for the object
            verify_ssl: Whether to verify SSL certificates for download (default: True).
                        Set to False to disable SSL verification.
        
        Returns:
            Dictionary with upload details
        """
        try:
            # Download the file
            local_path = self.download_file(url, verify_ssl=verify_ssl)
            
            # If object_name is not provided, extract it from the URL
            if object_name is None:
                object_name = os.path.basename(urlparse(url).path)
                # If URL doesn't have a filename, use the local filename
                if not object_name:
                    object_name = os.path.basename(local_path)
            
            # Upload the file to MinIO
            upload_info = self.upload_to_minio(
                file_path=local_path,
                bucket_name=bucket_name,
                object_name=object_name,
                content_type=content_type,
                metadata=metadata
            )
            
            # Remove the local file if keep_local is False
            if not keep_local and os.path.exists(local_path):
                os.remove(local_path)
                self.logger.info(f"Local file {local_path} deleted")
            
            return upload_info
        
        except Exception as e:
            self.logger.error(f"Failed to download and upload file: {str(e)}")
            raise


# Usage example (with doctest format)
if __name__ == "__main__":
    import doctest
    doctest.testmod()
    
    # Example usage:
    logging.basicConfig(level=logging.INFO)
    
    # You need to set these environment variables before running:
    # os.environ['MINIO_ENDPOINT'] = 'play.min.io:9000'
    # os.environ['MINIO_ACCESS_KEY'] = 'minioadmin'
    # os.environ['MINIO_SECRET_KEY'] = 'minioadmin'
    # os.environ['MINIO_SECURE'] = 'True'
    
    # Uncomment to test:
    # try:
    #     uploader = MinioUploader()
    #     
    #     # Example with SSL verification enabled (default)
    #     result1 = uploader.download_and_upload(
    #         url="https://www.example.com/sample.pdf",
    #         bucket_name="test-bucket",
    #         object_name="sample.pdf"
    #     )
    #     print(f"Upload result 1: {result1}")
    #     
    #     # Example with SSL verification disabled
    #     result2 = uploader.download_and_upload(
    #         url="https://self-signed-cert-site.example.com/sample.pdf",
    #         bucket_name="test-bucket",
    #         object_name="sample2.pdf",
    #         verify_ssl=False
    #     )
    #     print(f"Upload result 2: {result2}")
    # except Exception as e:
    #     print(f"Error: {e}")

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.db.connection import get_db

# Use API key authentication for secure endpoints
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)) -> str:
    """
    Validate the API key.
    
    Args:
        api_key: API key from request header
        
    Returns:
        Validated API key
    
    Raises:
        HTTPException: If API key is invalid
    """
    # In a real application, you would validate the API key against a database
    # or other secure storage. For simplicity, we're just checking against
    # the API key in the config.
    if api_key == settings.WEBEX_API_KEY.get_secret_value():
        return api_key
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "APIKey"},
    )


# Re-export get_db for convenience
__all__ = ["get_db", "get_api_key"]
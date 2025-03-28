import logging
import sys
from typing import Optional

from app.config.settings import settings

# Configure logging format
LOG_FORMAT = settings.LOG_FORMAT
LOG_LEVEL = getattr(logging, settings.LOG_LEVEL)


def setup_logging(name: Optional[str] = None) -> logging.Logger:
    """
    Set up a logger with the configured format and level.
    
    Args:
        name: Name of the logger (defaults to root logger if None)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    
    # Clear any existing handlers
    if logger.handlers:
        logger.handlers = []
    
    # Configure the logger
    logger.setLevel(LOG_LEVEL)
    
    # Create a formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Create a stream handler (for console output)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(stream_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger
    """
    return setup_logging(name)
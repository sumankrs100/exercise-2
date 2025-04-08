#!/usr/bin/env python3
"""
Main module that runs in an infinite loop and calls a function from another module.
Uses environment variables for configuration.
"""

import os
import time
import logging
from helper import process_data

# Get log level from environment variable or default to INFO
log_level_name = os.environ.get('APP_LOG_LEVEL', 'INFO')
log_level = getattr(logging, log_level_name.upper(), logging.INFO)

# Configure logging
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """
    Main function that runs in an infinite loop.
    """
    logger.info("Starting the application")
    
    try:
        while True:
            logger.info("Running process_data function")
            
            try:
                # Call the function from the other module
                result = process_data()
                logger.info(f"Process completed with result: {result}")
            except Exception as e:
                logger.error(f"Error during process execution: {e}")
            
            logger.info("Waiting for 60 seconds before next run")
            time.sleep(60)
    
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

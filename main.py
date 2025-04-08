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

async def main():
    """
    Main async function that runs in an infinite loop.
    """
    logger.info("Starting the application")
    logger.info(f"Prefect API URL: {os.environ.get('PREFECT_API_URL', 'Not set')}")
    
    try:
        while True:
            logger.info("Running process_data function")
            
            try:
                # Call the async function from the other module
                result = await process_data()
                logger.info(f"Process completed with result: {result}")
            except Exception as e:
                logger.error(f"Error during process execution: {e}")
            
            # Get sleep time from env variable or default to 60
            sleep_time = int(os.environ.get('PROCESS_INTERVAL_SECONDS', '60'))
            logger.info(f"Waiting for {sleep_time} seconds before next run")
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    exit(exit_code)

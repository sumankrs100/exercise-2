import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import recordings, scheduler
from app.config.settings import settings
from app.core.scheduler.batch_job import BatchJobScheduler
from app.utils.logging import setup_logging

# Set up logging
logger = setup_logging("app")

# Create the scheduler
job_scheduler = BatchJobScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    Args:
        app: FastAPI application
    """
    # Startup events
    logger.info("Starting application")
    
    # Start the scheduler
    scheduler_task = asyncio.create_task(job_scheduler.start())
    
    yield
    
    # Shutdown events
    logger.info("Shutting down application")
    
    # Stop the scheduler
    job_scheduler.stop()
    
    # Wait for the scheduler to stop
    try:
        await asyncio.wait_for(scheduler_task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Timeout waiting for scheduler to stop")


# Create the FastAPI application
app = FastAPI(
    title="Webex Recording Manager",
    description="API for managing Webex recordings",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler.
    
    Args:
        request: Request that caused the exception
        exc: Exception
        
    Returns:
        JSON response with error details
    """
    logger.error(f"Global exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Include routers
app.include_router(recordings.router, prefix="/api")
app.include_router(scheduler.router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": "Webex Recording Manager",
        "version": "1.0.0",
        "docs_url": "/docs"
    }
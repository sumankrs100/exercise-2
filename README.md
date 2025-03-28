# Webex Recording Manager

A FastAPI-based application for downloading and managing Webex recordings. This service fetches recordings from the Webex API, stores them in MinIO object storage, and maintains metadata in a PostgreSQL database.

## Features

- Download Webex recordings via API
- Store recordings in MinIO buckets
- Track recording metadata in PostgreSQL
- Schedule batch jobs for automatic synchronization
- Configurable via YAML and environment variables
- Integration with Prefect for workflow management
- Proper logging and monitoring

## Architecture

The application is built using modern design patterns:

- **Repository Pattern**: For database operations
- **Service Layer**: For business logic
- **Dependency Injection**: For loose coupling
- **Configuration Management**: Using both YAML and environment variables

## Project Structure

```
webex-recording-manager/
├── app/                      # Application code
│   ├── api/                  # API routes and dependencies
│   ├── config/               # Configuration settings
│   ├── core/                 # Core components (Webex, MinIO, scheduler)
│   ├── db/                   # Database models and repositories
│   ├── services/             # Business logic services
│   └── utils/                # Utilities (logging, etc.)
├── migrations/               # Database migrations
├── prefect/                  # Prefect flows and tasks
└── tests/                    # Test suite
```

## Prerequisites

- Python 3.10+
- PostgreSQL
- MinIO server
- Webex API credentials

## Environment Variables

The following environment variables are required:

```
# Database settings
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=webex_recordings

# MinIO settings
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
MINIO_BUCKET_NAME=webex-recordings
MINIO_SECURE=true

# Webex settings
WEBEX_SITE_URL=your_webex_site_url
WEBEX_API_KEY=your_webex_api_key

# Optional settings
BATCH_JOB_INTERVAL_MINUTES=60
LOG_LEVEL=INFO
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/webex-recording-manager.git
   cd webex-recording-manager
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create the database:
   ```
   psql -U postgres -c "CREATE DATABASE webex_recordings;"
   ```


## Running the Application

Start the FastAPI server:

```
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000 with documentation at http://localhost:8000/docs.

## API Endpoints

### Recordings API

- `GET /api/recordings/`: Get recordings with optional filters
- `GET /api/recordings/undownloaded`: Get recordings that haven't been downloaded yet
- `GET /api/recordings/{recording_id}`: Get a recording by ID
- `POST /api/recordings/fetch`: Fetch recordings from Webex API
- `POST /api/recordings/{recording_id}/download`: Download a recording
- `GET /api/recordings/{recording_id}/download-url`: Get a download URL for a recording

### Batch Jobs API

- `GET /api/jobs/`: Get all batch jobs
- `POST /api/jobs/`: Create a new batch job
- `GET /api/jobs/{job_id}`: Get a batch job by ID
- `PUT /api/jobs/{job_id}`: Update a batch job
- `POST /api/jobs/{job_id}/start`: Start a batch job
- `POST /api/jobs/{job_id}/pause`: Pause a batch job
- `POST /api/jobs/{job_id}/execute`: Execute a batch job immediately
- `GET /api/jobs/{job_id}/logs`: Get execution logs for a job

## Database Schema

The application uses the following database tables:

1. `webex_recordings`: Stores metadata about Webex recordings
2. `batch_jobs`: Stores batch job configurations
3. `job_execution_logs`: Stores logs of batch job executions

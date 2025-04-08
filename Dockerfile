# Use an official Python runtime as the base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY main.py .
COPY helper.py .
COPY start.sh .
COPY .env* ./

# Make the scripts executable
RUN chmod +x main.py helper.py start.sh

# Create directories for Prefect
RUN mkdir -p /app/prefect

# Use a non-root user for better security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PREFECT_HOME=/app/prefect

# Run the start script when the container launches
ENTRYPOINT ["/app/start.sh"]

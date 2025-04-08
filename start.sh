#!/bin/bash
set -e

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set Prefect config variable for URL
echo "Setting Prefect configuration..."
export PREFECT_API_URL=${PREFECT_API_URL:-"http://localhost:4200/api"}
echo "PREFECT_API_URL set to: $PREFECT_API_URL"

# Set any other Prefect configurations as needed
# export PREFECT_HOME=${PREFECT_HOME:-"/app/prefect"}

# Print confirmation message
echo "Starting application with configured environment..."

# Execute the Python script
exec python main.py

FROM python:3.9-slim

WORKDIR /

# Install dependencies
RUN pip install celery==5.2.7 flower==1.2.0 redis

# Command will be specified in docker-compose.yml

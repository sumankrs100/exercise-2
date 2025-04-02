FROM python:3.9-slim

WORKDIR /app

# Install dependencies
RUN pip install celery==5.2.7 flower==1.2.0

# For RabbitMQ support
RUN pip install "celery[rabbitmq]"

# Command will be specified in docker-compose.yml

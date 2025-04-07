from celery import Celery

# Configure Celery with Redis
app = Celery('tasks')
app.conf.broker_url = 'redis://redis:6379/0'
app.conf.result_backend = 'redis://redis:6379/0'

# Define a sample task
@app.task
def add(x, y):
    return x + y

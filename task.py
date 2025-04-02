from celery import Celery

# Configure Celery
app = Celery('tasks')
app.conf.broker_url = 'amqp://user:password@rabbitmq:5672/'
app.conf.result_backend = 'rpc://'

# Define a sample task
@app.task
def add(x, y):
    return x + y

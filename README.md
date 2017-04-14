# Flask-Celery for WJ

### Usage

    sudo apt-get install rabbitmq-server
    pip install celery
    celery -A wj.celery worker
    python wj.py

Then visit http://localhost:5000 for a demo

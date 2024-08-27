from app.core.config import settings
from worker.celery_app import app, is_backend_running, is_broker_running

if not is_backend_running():
    exit()
if not is_broker_running():
    exit()

app.conf.task_routes = {
    'tasks.healthcheck_task': {'queue': settings.WORKER_NAME},
}

from worker.tasks.healthcheck import healthcheck_task

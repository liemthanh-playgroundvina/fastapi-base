from redis import Redis
from celery import Celery
from app.core.config import settings


redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, password=settings.REDIS_PASS, db=settings.REDIS_DB)


celery_execute = Celery(broker=settings.RABBITMQ_BROKER, backend=settings.REDIS_BACKEND)

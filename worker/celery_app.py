from celery import Celery
from kombu import Queue, Connection
from kombu.exceptions import OperationalError
from redis import Redis
from redis.exceptions import ConnectionError
from app.core.config import settings

# App
app = Celery(settings.WORKER_NAME, broker=settings.RABBITMQ_BROKER, backend=settings.REDIS_BACKEND)
app.config_from_object({
    'task_acks_late': True,
    'worker_prefetch_multiplier': 1,
    'task_queues': [
        Queue(name=settings.WORKER_NAME),
    ],
    'result_expires': 60 * 60 * 48,
    'task_always_eager': False,
})

# Broker
def is_broker_running(retries: int = 3) -> bool:
    try:
        conn = Connection(settings.RABBITMQ_BROKER)
        conn.ensure_connection(max_retries=retries)
    except OperationalError as e:
        print("Failed to connect to RabbitMQ instance at %s", settings.RABBITMQ_BROKER)
        print(str(e))
        return False
    conn.close()
    return True

# Redis
def is_backend_running() -> bool:
    try:
        conn = Redis(
            host=settings.REDIS_HOST,
            port=int(settings.REDIS_PORT),
            db=int(settings.REDIS_DB),
            password=settings.REDIS_PASS
        )
        conn.client_list()  # Must perform an operation to check connection.
    except ConnectionError as e:
        print("Failed to connect to Redis instance at %s", settings.REDIS_BACKEND)
        print(repr(e))
        return False
    conn.close()
    return True
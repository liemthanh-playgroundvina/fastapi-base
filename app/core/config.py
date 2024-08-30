import os
from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Settings(BaseSettings):
    # App
    PROJECT_NAME = os.getenv('PROJECT_NAME', 'FASTAPI BASE')
    BASE_HOST = os.getenv("BASE_HOST", "0.0.0.0")
    BASE_PORT = os.getenv("BASE_PORT", 8000)
    SECRET_KEY = os.getenv('SECRET_KEY', '')
    API_PREFIX = os.getenv('API_PREFIX', '')
    BACKEND_CORS_ORIGINS = ['*']
    ACCESS_TOKEN_EXPIRE_SECONDS: int = (
        100 * 365 * 24 * 60 *60
    )  # Token expired after 100 years => no expired
    SECURITY_ALGORITHM = 'HS256'
    LOGGING_CONFIG_FILE = os.getenv("LOGGING_CONFIG_FILE", "logging.ini")
    LOGGING_APP_FILE = os.getenv("LOGGING_APP_FILE", "app.log")
    STATIC_URL = os.getenv("STATIC_URL", "static")

    # Streaming
    STREAM_DELAY=float(os.getenv("STREAM_DELAY", 0.1))
    RETRY_TIMEOUT=int(os.getenv("RETRY_TIMEOUT", 15000))

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    SUPERUSER_NAME = os.getenv("SUPERUSER_NAME", "admin")
    SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin")

    # Worker
    WORKER_NAME = os.getenv("WORKER_NAME", "worker")
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = os.getenv("REDIS_PORT", 6379)
    REDIS_PASS = os.getenv("REDIS_PASS", "")
    REDIS_DB = os.getenv("REDIS_DB", 0)
    REDIS_BACKEND = "redis://:{password}@{hostname}:{port}/{db}".format(
        hostname=REDIS_HOST, password=REDIS_PASS, port=REDIS_PORT, db=REDIS_DB
    )
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "127.0.0.1")
    RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", 5672)
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "")
    RABBITMQ_BROKER = "amqp://{user}:{pw}@{hostname}:{port}/{vhost}".format(
        user=RABBITMQ_USER,
        pw=RABBITMQ_PASS,
        hostname=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        vhost=RABBITMQ_VHOST,
    )
    QUEUE_TIMEOUT = int(os.getenv("QUEUE_TIMEOUT", 60*60))
    QUEUE_TIME_LIMIT = int(os.getenv("QUEUE_TIME_LIMIT", 5*60))
    WORKER_DIRECTORY = os.getenv("WORKER_DIRECTORY", "worker")
    WORKER_DIRECTORY = '{static}/{worker}'.format(
        static=STATIC_URL,
        worker=WORKER_DIRECTORY
    )

    # LLM
    LLM_URL = os.getenv("LLM_URL", "")
    EM_URL = os.getenv("EM_URL", "")
    VDB_URL = os.getenv("VDB_URL", "")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Google Search
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID", "")

    # Other


settings = Settings()

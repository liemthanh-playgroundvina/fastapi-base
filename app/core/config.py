import os
from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))

class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = 'FASTAPI BASE'
    BASE_HOST: str = "0.0.0.0"
    BASE_PORT: int = 8000
    SECRET_KEY: str
    API_PREFIX: str = ''
    BACKEND_CORS_ORIGINS: list[str] = ['*']
    ACCESS_TOKEN_EXPIRE_SECONDS: int = (
        100 * 365 * 24 * 60 * 60
    )  # Token expired after 100 years => no expired
    SECURITY_ALGORITHM: str = 'HS256'
    LOGGING_CONFIG_FILE: str = "logging.ini"
    LOGGING_APP_FILE: str = "app.log"
    STATIC_URL: str = "static"

    # Streaming
    STREAM_DELAY: float = 0.1
    RETRY_TIMEOUT: int = 15000

    # Database
    DATABASE_URL: str
    SUPERUSER_NAME: str = "admin"
    SUPERUSER_PASSWORD: str = "admin"

    # Worker
    WORKER_NAME: str = "worker"
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASS: str = ""
    REDIS_DB: int = 0
    @property
    def REDIS_BACKEND(self) -> str:
        return f"redis://:{self.REDIS_PASS}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    RABBITMQ_HOST: str = "127.0.0.1"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASS: str = "guest"
    RABBITMQ_VHOST: str = ""
    @property
    def RABBITMQ_BROKER(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    QUEUE_TIMEOUT: int = 60 * 60
    QUEUE_TIME_LIMIT: int = 5 * 60
    WORKER_DIRECTORY: str = "static/worker"

    # LLM
    LLM_URL: str
    EM_URL: str
    VDB_URL: str

    # OpenAI
    OPENAI_API_KEY: str

    # Google Search
    GOOGLE_API_KEY: str
    GOOGLE_CSE_ID: str

    class Config:
        env_file = os.path.join(BASE_DIR, '.env')


settings = Settings()

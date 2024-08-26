import os
from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Settings(BaseSettings):
    PROJECT_NAME = os.getenv('PROJECT_NAME', 'FASTAPI BASE')
    BASE_HOST = os.getenv("BASE_HOST", "0.0.0.0")
    BASE_PORT = os.getenv("BASE_PORT", 8000)
    SECRET_KEY = os.getenv('SECRET_KEY', '')
    API_PREFIX = os.getenv('API_PREFIX', '')
    BACKEND_CORS_ORIGINS = ['*']
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    ACCESS_TOKEN_EXPIRE_SECONDS: int = (
        60 * 60 * 24 * 365 * 100
    )  # Token expired after 100 years => no expired
    SECURITY_ALGORITHM = 'HS256'
    LOGGING_CONFIG_FILE = os.getenv("LOGGING_CONFIG_FILE", "logging.ini")
    STATIC_URL = os.getenv("STATIC_URL", "static")
    SUPERUSER_NAME = os.getenv("SUPERUSER_NAME", "admin")
    SUPERUSER_PASSWORD = os.getenv("SUPERUSER_PASSWORD", "admin")

settings = Settings()

from dotenv import load_dotenv
import os

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

load_dotenv('.env')

class Settings(BaseSettings):
    DB_URL: str = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/{os.getenv('POSTGRES_DB')}"
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY')
    JWT_ALGORITHM : str = os.getenv('JWT_ALGORITHM')
    JWT_EXPIRATION_TIME: str = os.getenv('JWT_TOKEN_EXPIRE_SECONDS')
    model_config = ConfigDict(
        extra="ignore", env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )
    MAIL_USERNAME : str = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD : str = os.getenv('MAIL_PASSWORD')
    MAIL_FROM : str = os.getenv('MAIL_FROM')
    MAIL_PORT : str = os.getenv('MAIL_PORT')
    MAIL_SERVER : str = os.getenv('MAIL_SERVER')
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    CLOUDINARY_CLOUD_NAME : str = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY : str = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET : str = os.getenv('CLOUDINARY_API_SECRET')

settings = Settings()
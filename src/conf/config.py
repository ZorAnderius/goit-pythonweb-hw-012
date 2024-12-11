"""
Application Configuration.

This module provides the configuration settings for the application, 
including database connection, JWT settings, email server configuration, 
and cloud storage credentials. It uses environment variables for secure 
and flexible setup.
"""

from dotenv import load_dotenv
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# Load environment variables from the .env file
load_dotenv('.env')

class Settings(BaseSettings):
    """
    Application settings derived from environment variables.

    This class loads environment variables using `pydantic` for validation
    and structured access. It includes settings for database connections, 
    JWT configuration, email service, cloud storage, and caching.

    Attributes:
        DB_URL (str): URL for connecting to the PostgreSQL database.
        JWT_SECRET_KEY (str): Secret key for signing JWT tokens.
        JWT_ALGORITHM (str): Algorithm used for signing JWT tokens.
        JWT_EXPIRATION_TIME (str): Token expiration time in seconds.
        MAIL_USERNAME (str): Email username for the SMTP server.
        MAIL_PASSWORD (str): Email password for the SMTP server.
        MAIL_FROM (str): Default sender email address.
        MAIL_PORT (str): Port for the SMTP server.
        MAIL_SERVER (str): SMTP server address.
        MAIL_FROM_NAME (str): Name for the default sender.
        MAIL_STARTTLS (bool): Indicates whether STARTTLS is enabled.
        MAIL_SSL_TLS (bool): Indicates whether SSL/TLS is enabled.
        USE_CREDENTIALS (bool): Indicates whether email credentials are used.
        VALIDATE_CERTS (bool): Indicates whether to validate SSL certificates.
        CLOUDINARY_CLOUD_NAME (str): Cloudinary cloud name.
        CLOUDINARY_API_KEY (str): API key for Cloudinary.
        CLOUDINARY_API_SECRET (str): API secret for Cloudinary.
        REDIS_HOST (str): Host for the Redis server.
        REDIS_PORT (int): Port for the Redis server.
    """

    DB_URL: str = f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@localhost:5432/{os.getenv('POSTGRES_DB')}"
    JWT_SECRET_KEY: str = os.getenv('JWT_SECRET_KEY', 'secret')
    JWT_ALGORITHM: str = os.getenv('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRATION_TIME: str = os.getenv('JWT_TOKEN_EXPIRE_SECONDS', '3600')
    MAIL_USERNAME: str = os.getenv('MAIL_USERNAME', 'some_example@email.com')
    MAIL_PASSWORD: str = os.getenv('MAIL_PASSWORD', '')
    MAIL_FROM: str = os.getenv('MAIL_FROM', 'some_example@email.com')
    MAIL_PORT: str = os.getenv('MAIL_PORT', '587')
    MAIL_SERVER: str = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_FROM_NAME: str = "Rest API Service"
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    CLOUDINARY_CLOUD_NAME: str = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY: str = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET: str = os.getenv('CLOUDINARY_API_SECRET', "")
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))

    # Configuration options for Pydantic BaseSettings
    model_config = ConfigDict(
        extra="ignore", 
        env_file=".env", 
        env_file_encoding="utf-8", 
        case_sensitive=True
    )

# Initialize the settings
settings = Settings()
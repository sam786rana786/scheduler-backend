# backend/app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
import os
from pathlib import Path

class Settings(BaseSettings):
    # Get environment from ENV variable, default to development
    ENV: str = os.getenv("ENV", "development")
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"

    # Email settings
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_FROM_NAME: str = "Schedule App"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:3000"
    
    # OAuth Credentials
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    
    # Stripe API
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            # Determine env file based on environment
            env = os.getenv("ENV", "development")
            env_file = f".env.{env}" if env != "development" else ".env"
            
            # Check if env file exists
            if not Path(env_file).exists():
                raise FileNotFoundError(f"Environment file {env_file} not found")
                
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

@lru_cache()
def get_settings():
    """Cache settings per environment"""
    env = os.getenv("ENV", "development")
    cache_key = f"settings_{env}"
    return Settings()
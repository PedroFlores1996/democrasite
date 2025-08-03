import os
from datetime import timedelta
from cryptography.fernet import Fernet

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Topic share code encryption key
    TOPIC_ENCRYPTION_KEY: str = os.getenv("TOPIC_ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./democrasite.db")
    DATABASE_CONNECT_ARGS: dict = {"check_same_thread": False}
    
    API_TITLE: str = "Democrasite API"
    API_VERSION: str = "1.0.0"

settings = Settings()
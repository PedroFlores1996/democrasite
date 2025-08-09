import os


class Settings:
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-secret-key-change-this-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database configuration - supports both SQLite and PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./democrasite.db")

    @property
    def DATABASE_CONNECT_ARGS(self) -> dict:
        """Return appropriate connection args based on database type"""
        if self.DATABASE_URL.startswith("sqlite"):
            return {"check_same_thread": False}
        else:
            # PostgreSQL doesn't need special connect args
            return {}

    API_TITLE: str = "Democrasite API"
    API_VERSION: str = "1.0.0"
    
    # Email configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@democrasite.com")
    FROM_NAME: str = os.getenv("FROM_NAME", "Democrasite")
    
    # Frontend URL for verification links
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8000")
    
    # Email verification
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24


settings = Settings()

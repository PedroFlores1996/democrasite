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


settings = Settings()

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
from typing import Optional, Any

class Settings(BaseSettings):
    PROJECT_NAME: str = "Task Tracker API"
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str
    
    REDIS_HOST: str
    REDIS_PORT: int

    COGNITO_USER_POOL_ID: str
    COGNITO_APP_CLIENT_ID: str
    COGNITO_CLIENT_SECRET: str
    COGNITO_REGION: str
    
    ENVIRONMENT: str = "development"
    BACKEND_CORS_ORIGINS: str = ""

    # FCM Configuration
    FCM_PROJECT_ID: Optional[str] = None
    FCM_CREDENTIALS_JSON: Optional[str] = None

    # Notification Settings
    NOTIFICATION_DUE_DATE_DAYS_BEFORE: int = 1  # Notify X days before due
    NOTIFICATION_STALE_TASK_DAYS: int = 7       # Notify if unchanged for X days
    NOTIFICATION_QUIET_HOURS_START: int = 22    # Don't send after 10 PM
    NOTIFICATION_QUIET_HOURS_END: int = 8       # Don't send before 8 AM

    @property
    def backend_cors_origins(self) -> list[str]:
        return [i.strip() for i in self.BACKEND_CORS_ORIGINS.split(",") if i.strip()]

    DATABASE_URL: Optional[str] = None

    model_config = ConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )

    def get_database_url(self):
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_redis_url(self):
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

settings = Settings()

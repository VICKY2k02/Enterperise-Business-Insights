from decimal import Decimal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    MONTHLY_REVENUE_TARGET: Decimal | None = None
    LOW_DAILY_SALES_THRESHOLD: Decimal | None = None

    @field_validator(
        "MONTHLY_REVENUE_TARGET",
        "LOW_DAILY_SALES_THRESHOLD",
        mode="before",
    )
    @classmethod
    def empty_threshold_to_none(cls, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
from enum import Enum
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    kproduction = "production"
    development = "development"
    staging = "staging"


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    ENVIRONMENT: Environment = Environment.development

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "deuxieme_main"

    JWT_SECRET: str = "change-me-in-dev-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24


envConfig = EnvConfig()


@lru_cache
def get_settings():
    return EnvConfig()


settings = get_settings()

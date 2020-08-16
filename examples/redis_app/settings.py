from functools import lru_cache

from pydantic import BaseSettings

__all__ = ("get_settings",)


class _Settings(BaseSettings):
    log_level: str = "INFO"
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    db_uri: str = "sqlite:///redis_app.db"


@lru_cache()
def get_settings() -> _Settings:
    return _Settings()  # Reads variables from environment

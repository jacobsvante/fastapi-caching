from functools import lru_cache

from pydantic import BaseSettings

__all__ = ("get_settings",)


class _Settings(BaseSettings):
    log_level: str = "INFO"
    db_uri: str = "sqlite:///inmem_app.db"


@lru_cache()
def get_settings() -> _Settings:
    return _Settings()  # Reads variables from environment

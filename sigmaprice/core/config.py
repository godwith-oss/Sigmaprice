"""Configuration management"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://sigmaprice:password@localhost:5432/sigmaprice"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


def get_database_url() -> str:
    return settings.DATABASE_URL


def get_redis_url() -> str:
    return settings.REDIS_URL


def get_secret_key() -> str:
    return settings.SECRET_KEY
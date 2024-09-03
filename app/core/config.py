# from pydantic import BaseSettings
import os, sys
from pydantic_settings import BaseSettings
from typing import AsyncGenerator
import asyncio
from icecream import ic
import aiomysql
from aiomysql import DictCursor
from dotenv import load_dotenv


class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    PROJECT_NAME: str = "Shift Scheduling System"
    SQLALCHEMY_DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    CELERY_BROKER_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SERVER_HOST: str
    SERVER_PORT: int

    class Config:
        env_file = ".env"

# Load environment variables
settings = Settings(
    DB_USER=os.getenv("DB_USER"),
    DB_PASS=os.getenv("DB_PASS"),
    DB_HOST=os.getenv("DB_HOST"),
    DB_PORT=int(os.getenv("DB_PORT")),
    DB_NAME=os.getenv("DB_NAME"),
    SERVER_HOST=os.getenv("SERVER_HOST"),
    SERVER_PORT=int(os.getenv("SERVER_PORT")),
    SQLALCHEMY_DATABASE_URL=f'mysql+aiomysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASS")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}?charset=utf8mb4',
    REDIS_HOST=os.getenv("REDIS_HOST"),
    REDIS_PORT=int(os.getenv("REDIS_PORT")),
    CELERY_BROKER_URL=f"redis://{os.getenv("REDIS_HOST")}:{os.getenv("REDIS_PORT")}/0",
    SECRET_KEY=os.getenv("SECRET_KEY")
)

# from pydantic import BaseSettings
import os, sys
from pydantic_settings import BaseSettings
# from typing import AsyncGenerator
# import asyncio
from icecream import ic
# import aiomysql
# from aiomysql import DictCursor
from os.path import join, dirname
from dotenv import dotenv_values
env_file = ".env"
dotenv_path = None
for root, dirs, files in os.walk(env_file):
    if env_file in files:
        dotenv_path = os.path.join(root, env_file)
local_env = dotenv_values(dotenv_path)
# local_env = dotenv_values(dotenv_path)

# #ic(local_env)
class Config:
    pass

    
#     DB_CONFIG = os.getenv(
#         "DB_CONFIG",
#         "mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}".format(
#             DB_USER=local_env['DB_USER'],
#             DB_PASS=local_env["DB_PASS"],
#             DB_HOST=local_env["DB_HOST"],
#             DB_NAME=local_env["DB_NAME"],
#         ),
#     )        
# settings = Config
# #ic(settings.DB_CONFIG)
class Settings(BaseSettings):
    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    PROJECT_NAME: str = "Shift Scheduling System"
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    CELERY_BROKER_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SERVER_HOST: str
    SERVER_PORT: int
# Load environment variables
settings = Settings(
    DB_USER=local_env["DB_USER"],
    DB_PASS=local_env["DB_PASS"],
    DB_HOST=local_env["DB_HOST"],
    DB_PORT=int(local_env["DB_PORT"]),
    DB_NAME=local_env["DB_NAME"],
    SERVER_HOST=local_env["SERVER_HOST"],
    SERVER_PORT=local_env["SERVER_PORT"],
    DATABASE_URL=f'mysql+aiomysql://{local_env["DB_USER"]}:{local_env["DB_PASS"]}@{local_env["DB_HOST"]}:{local_env["DB_PORT"]}/{local_env["DB_NAME"]}?charset=utf8mb4',
    REDIS_HOST=local_env["REDIS_HOST"],
    REDIS_PORT=local_env["REDIS_PORT"],
    CELERY_BROKER_URL=f"redis://{local_env["REDIS_HOST"]}:{local_env["REDIS_PORT"]}/0",
    SECRET_KEY=local_env["SECRET_KEY"]
)

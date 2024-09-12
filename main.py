from icecream import ic
import ssl
import logging
from app.app import app
import uvicorn
import sys  
import os
from os import getenv
from os.path import join, dirname
from dotenv import load_dotenv
from dotenv import dotenv_values
from fastapi import FastAPI

# import pwd
import json
import time
# import pytz
from tempfile import gettempdir


if __name__ == "__main__":
    # Load the .env file
    dotenv_path = join(dirname(__file__), '.env')
    # load_dotenv(dotenv_path)
    local_env = dotenv_values(dotenv_path)

    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"WORKER STARTING with pid {os.getpid()}")

    # Set default values and get environment variables
    REDIS_HOST = local_env['REDIS_HOST']
    REDIS_PORT = int(local_env['REDIS_PORT'])
    SECRET_KEY = local_env['SECRET_KEY']
    HOST = local_env['SERVER_HOST']
    PORT = int(local_env['SERVER_PORT'])
    ROOT_PATH = local_env['ROOT_PATH']
    # Check if required environment variables are set
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in the environment or .env file")

    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        # root_path=ROOT_PATH,
        reload=True, log_level="debug",
        workers=4, limit_max_requests=1024
    )
    server = uvicorn.Server(config)
    server.run()

    # Add this new route
    @app.get("/")
    async def root():
        return {"message": "Welcome to the API"}







# from fastapi import FastAPI #, Lifespan
# from app.api.routes import router as api_router
# from app.core.config import settings
# from app.db.database import engine, Base
# import asyncio

# app = FastAPI(title=settings.PROJECT_NAME)

# async def on_startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

# app.include_router(api_router, prefix="/api")

# @app.on_event("startup")
# async def on_startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

# app.include_router(api_router, prefix="/api")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
#     # uvicorn main:app --reload --lifespan on


# # alembic revision --autogenerate -m "Initial migration"
# # alembic upgrade head
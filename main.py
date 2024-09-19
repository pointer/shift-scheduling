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


def run_server():
    # Load the .env file
    dotenv_path = join(dirname(__file__), '.env')
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

@app.get("/")
async def root():
    return {"message": "Welcome to the API"}

if __name__ == "__main__":
    run_server()

# # alembic revision --autogenerate -m "Initial migration"
# # alembic upgrade head
from icecream import ic
import ssl
import logging
from app.app import app
import uvicorn
import sys
import os
from os import getenv
# import pwd
import json
import time
# import pytz
from tempfile import gettempdir

from dotenv import load_dotenv
from dotenv import dotenv_values

if __name__ == "__main__":
    # Load the .env file
    load_dotenv(".env")
 
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info(f"WORKER STARTING with pid {os.getpid()}")
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8000))
    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        # ssl_keyfile=ssl_key,
        # ssl_certfile=ssl_cert,
        # ssl_version=ssl.PROTOCOL_TLS,
        reload=True, log_level="debug",
        workers=4, limit_max_requests=1024
    )
    server = uvicorn.Server(config)
    server.run()





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
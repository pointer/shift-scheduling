import os
import ssl
from datetime import datetime, timedelta
from typing import Union, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, date
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi import HTTPException, Header
from fastapi_users.exceptions import UserAlreadyExists
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.router import ErrorCode
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import FastAPIUsers, password, schemas, BaseUserManager, IntegerIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
# from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
from app.api.routes import router as api_router
from app.core.config import settings
from app.db.database import sessionmanager
# from starlette.requests import Headers, Request
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
# from starlette.responses import Response

# from typing import
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
# from app.db import create_db_and_tables
from app.db.models import EmployeeCreate, ShiftCreate, ScheduleCreate
# from app.users import auth_backend, current_active_user, fastapi_users
import logging
from dotenv import load_dotenv
# from loguru import logger
# from main import ssl_cert, ssl_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # Initialize the database session manager
    await sessionmanager.init_db()
    yield
    await sessionmanager.close()

# @asynccontextmanager
# async def app_lifespan(app: FastAPI):
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#     yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=app_lifespan)
# app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# async def on_startup():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)

app.include_router(api_router) #, prefix="/api")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: str
    id: int
    is_active: bool
    role: str
    working_days: int


class RegisterResponse(BaseModel):
    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in sessionmanager.get_db():
        yield session


@app.middleware("http") #("https")
async def log_request(request: Request, call_next):
    # Log the request details
    logger.info(f"Received request: {request.method} {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")

    # For POST requests, log the body
    if request.method == "POST":
        body = await request.body()
        logger.info(f"Body: {body.decode()}")
        # req_body = [section async for section in request.body.__dict__['body_iterator']]
        # logging.info("BODY:", req_body)
        # logger.info(
        #     f"{request.method} request to {request.url} metadata\n"
        #     f"\tHeaders: {request.headers}\n"
        #     f"\tBody: {request.body()}\n"
        #     f"\tPath Params: {request.path_params}\n"
        #     f"\tQuery Params: {request.query_params}\n"
        #     f"\tCookies: {request.cookies}\n"
        # )
    response = await call_next(request)
    return response


# @app.get("/authenticated-route")
# async def authenticated_route(user: User = Depends(current_active_user)):
#     return {"message": f"Hello {user.email}!"}

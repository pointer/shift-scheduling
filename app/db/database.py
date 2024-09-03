from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from typing import AsyncGenerator
import asyncio
import os
# from asyncmy import connect
# from asyncmy.cursors import DictCursor
from icecream import ic
import aiomysql
from aiomysql import DictCursor
from dotenv import load_dotenv
engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

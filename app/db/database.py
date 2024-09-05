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
from contextlib import asynccontextmanager

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

Base = declarative_base()

@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

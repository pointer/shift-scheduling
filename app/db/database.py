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
import contextlib
from typing import AsyncIterator
from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    async_scoped_session
)
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Base

from asyncio import current_task

engine = create_async_engine(settings.DATABASE_URL, echo=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class DatabaseSessionManager:
    def __init__(self):
        self.engine = engine
        self.SessionLocal = async_session_maker

    async def init_db(self):
        # This method should be async
        async with self.engine.begin() as conn:
            # Add any initialization logic here if needed
            pass

    async def close(self):
        await self.engine.dispose()

    async def get_db(self):
        async with self.SessionLocal() as session:
            yield session

sessionmanager = DatabaseSessionManager()

# async def get_db() -> AsyncIterator[AsyncSession]:
#     session = sessionmanager.session()
#     if session is None:
#         raise Exception("DatabaseSessionManager is not initialized")
#     try:
#         # Setting the search path and yielding the session...
#         await session.execute(
#             text(f"SET search_path TO {SCHEMA}")
#         )
#         yield session
#     except Exception:
#         await session.rollback()
#         raise
#     finally:
#         # Closing the session after use...
#         await session.close()

@asynccontextmanager
async def get_db():
    async with sessionmanager.SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()




# class DatabaseSessionManager:
#     def __init__(self):
#         self._engine: AsyncEngine | None = None
#         self._sessionmaker: async_sessionmaker | None = None

#     def init(self, host: str):
#         self._engine = create_async_engine(host)
#         self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

#     async def close(self):
#         if self._engine is None:
#             raise Exception("DatabaseSessionManager is not initialized")
#         await self._engine.dispose()
#         self._engine = None
#         self._sessionmaker = None

#     @contextlib.asynccontextmanager
#     async def connect(self) -> AsyncIterator[AsyncConnection]:
#         if self._engine is None:
#             raise Exception("DatabaseSessionManager is not initialized")

#         async with self._engine.begin() as connection:
#             try:
#                 yield connection
#             except Exception:
#                 await connection.rollback()
#                 raise

#     @contextlib.asynccontextmanager
#     async def session(self) -> AsyncIterator[AsyncSession]:
#         if self._sessionmaker is None:
#             raise Exception("DatabaseSessionManager is not initialized")

#         session = self._sessionmaker()
#         try:
#             yield session
#         except Exception:
#             await session.rollback()
#             raise
#         finally:
#             await session.close()

#     async def create_all(self, connection: AsyncConnection):
#         await connection.run_sync(Base.metadata.create_all)

#     async def drop_all(self, connection: AsyncConnection):
#         await connection.run_sync(Base.metadata.drop_all)


# sessionmanager = DatabaseSessionManager()


# async def get_db():
#     async with sessionmanager.session() as session:
#         #ic(session)
#         yield session

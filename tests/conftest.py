import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.database import Base, get_db
from app import app
from httpx import AsyncClient
import uuid
import os
import warnings
from pydantic import PydanticDeprecatedSince20

warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Set USE_REDIS environment variable to False for testing
os.environ['USE_REDIS'] = 'False'

# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
async def db_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def unique_id():
    return str(uuid.uuid4())

@pytest.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield session
        await session.close()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

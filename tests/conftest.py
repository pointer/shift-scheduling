import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.db.database import Base, get_db
from app.app import app
from httpx import AsyncClient
import uuid
import os
import warnings
from pydantic import PydanticDeprecatedSince20
from app.core.config import settings
import jwt

warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")

# Set USE_REDIS environment variable to False for testing
os.environ['USE_REDIS'] = 'False'

# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()

@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine(event_loop):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        connect_args={"loop": event_loop}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="function")
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
async def client(test_session):
    async def override_get_db():
        try:
            yield test_session
        finally:
            await test_session.close()

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def unique_id():
    return str(uuid.uuid4())

@pytest.fixture
def auth_headers():
    # Create a mock token
    token = jwt.encode({"sub": "test@example.com"}, settings.SECRET_KEY, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
async def authenticated_client(client, auth_headers):
    client.headers.update(auth_headers)
    return client

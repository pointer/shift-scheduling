import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.core.config import settings
from app.db.models import EmployeeCategory, WorkCenter, Employee, Shift, Schedule, ScheduleAssignment

@pytest.fixture(scope="session")
def engine():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URL, echo=True)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
async def db_session(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def sample_data(db_session):
    # Create sample data for testing
    category = EmployeeCategory(name="Test Category", level=1, hourly_rate=10.0)
    work_center = WorkCenter(name="Test Work Center", demand={"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}})
    employee = Employee(name="Test Employee", category_id=1, off_day_preferences={"Monday": 1}, shift_preferences=[1, 2, 3], work_center_preferences=[1])
    
    db_session.add_all([category, work_center, employee])
    await db_session.commit()
    
    return {"category": category, "work_center": work_center, "employee": employee}

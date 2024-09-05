import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import EmployeeCategory, WorkCenter, Employee, Shift, Schedule, ScheduleAssignment
from app.db.database import get_db


@pytest.fixture(autouse=True)
async def cleanup(db_session):
    yield
    await db_session.rollback()


@pytest.mark.asyncio
async def test_employee_category(db_session: AsyncSession):
    category = EmployeeCategory(name="Test Category")
    db_session.add(category)
    await db_session.commit()

    result = await db_session.get(EmployeeCategory, category.id)
    assert result.name == "Test Category"
    assert result.level == 1
    assert result.hourly_rate == 10.0

@pytest.mark.asyncio
async def test_work_center(db_session: AsyncSession):
    work_center = WorkCenter(name="Test Work Center", demand={"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}})
    db_session.add(work_center)
    await db_session.commit()
    
    result = await db_session.get(WorkCenter, work_center.id)
    assert result.name == "Test Work Center"
    assert result.demand == {"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}}

@pytest.mark.asyncio
async def test_employee(db_session: AsyncSession):
    category = EmployeeCategory(name="Test Category", level=1, hourly_rate=10.0)
    db_session.add(category)
    await db_session.commit()
    
    employee = Employee(name="Test Employee", category_id=category.id, off_day_preferences={"Monday": 1},
                        shift_preferences=[1, 2, 3], work_center_preferences=[1], delta=0.5)
    db_session.add(employee)
    await db_session.commit()
    
    result = await db_session.get(Employee, employee.id)
    assert result.name == "Test Employee"
    assert result.category_id == category.id
    assert result.off_day_preferences == {"Monday": 1}
    assert result.shift_preferences == [1, 2, 3]
    assert result.work_center_preferences == [1]
    assert result.delta == 0.5

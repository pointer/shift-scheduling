import pytest
from app.db import models as db_models

@pytest.mark.asyncio
async def test_employee_category(test_session):
    category = db_models.EmployeeCategory(name="Test Category", level=1, hourly_rate=15.0)
    test_session.add(category)
    await test_session.flush()

    result = await test_session.get(db_models.EmployeeCategory, category.id)
    assert result.name == "Test Category"

@pytest.mark.asyncio
async def test_work_center(test_session):
    work_center = db_models.WorkCenter(name="Test Work Center", demand={"weekday": {"1": [1, 1, 1]}})
    test_session.add(work_center)
    await test_session.flush()

    result = await test_session.get(db_models.WorkCenter, work_center.id)
    assert result.name == "Test Work Center"

@pytest.mark.asyncio
async def test_employee(test_session):
    # Create an EmployeeCategory first
    category = db_models.EmployeeCategory(name="Test Category", level=1, hourly_rate=15.0)
    test_session.add(category)
    await test_session.flush()

    # Now create an Employee
    employee = db_models.Employee(
        name="John Doe",
        category_id=category.id,
        off_day_preferences={"Monday": 1, "Tuesday": 2},
        shift_preferences=[1, 2],
        work_center_preferences=[1, 2],
        delta=0.5
    )
    test_session.add(employee)
    await test_session.flush()

    assert employee.id is not None
    assert employee.name == "John Doe"
    assert employee.category_id == category.id

    await test_session.rollback()  # Roll back the transaction after the test

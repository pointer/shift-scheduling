import pytest
from app.db.models import EmployeeCategory, Employee, WorkCenter
from sqlalchemy.exc import IntegrityError

@pytest.mark.asyncio
async def test_employee_category(test_session):
    category = EmployeeCategory(name="Test Category", level=1, hourly_rate=10.0)
    test_session.add(category)
    await test_session.commit()
    
    assert category.id is not None
    assert category.name == "Test Category"
    assert category.level == 1
    assert category.hourly_rate == 10.0

@pytest.mark.asyncio
async def test_work_center(test_session):
    work_center = WorkCenter(name="Test Work Center")
    test_session.add(work_center)
    await test_session.commit()
    
    assert work_center.id is not None
    assert work_center.name == "Test Work Center"

@pytest.mark.asyncio
async def test_employee(test_session, unique_id):
    # Use unique_id as a parameter, not pytest.unique_id
    employee_id = unique_id
    
    category = EmployeeCategory(name=f"Test Category {employee_id}", level=1, hourly_rate=10.0)
    test_session.add(category)
    await test_session.commit()

    employee = Employee(name="Test Employee", category=category)
    test_session.add(employee)
    await test_session.commit()

    assert employee.id is not None
    assert employee.name == "Test Employee"
    assert employee.category.name == f"Test Category {employee_id}"

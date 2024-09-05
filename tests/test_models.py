import pytest
from app.db.models import EmployeeCategory, WorkCenter, Employee, Shift, Schedule, ScheduleAssignment

@pytest.mark.asyncio
async def test_employee_category(db_session, sample_data):
    category = await db_session.get(EmployeeCategory, sample_data["category"].id)
    assert category.name == "Test Category"
    assert category.level == 1
    assert category.hourly_rate == 10.0

@pytest.mark.asyncio
async def test_work_center(db_session, sample_data):
    work_center = await db_session.get(WorkCenter, sample_data["work_center"].id)
    assert work_center.name == "Test Work Center"
    assert work_center.demand == {"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}}

@pytest.mark.asyncio
async def test_employee(db_session, sample_data):
    employee = await db_session.get(Employee, sample_data["employee"].id)
    assert employee.name == "Test Employee"
    assert employee.category_id == 1
    assert employee.off_day_preferences == {"Monday": 1}
    assert employee.shift_preferences == [1, 2, 3]
    assert employee.work_center_preferences == [1]

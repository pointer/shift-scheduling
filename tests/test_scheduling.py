import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.scheduling.algorithm import generate_schedule
from app.db.models import Employee, WorkCenter, EmployeeCategory

@pytest.mark.asyncio
async def test_generate_schedule(db_session: AsyncSession):
    # Create sample data
    category = EmployeeCategory(name="Test Category", level=1, hourly_rate=10.0)
    db_session.add(category)
    await db_session.commit()

    employee = Employee(name="Test Employee", category_id=category.id, off_day_preferences={"Monday": 1},
                        shift_preferences=[1, 2, 3], work_center_preferences=[1], delta=0.5)
    db_session.add(employee)

    work_center = WorkCenter(name="Test Work Center", demand={"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}})
    db_session.add(work_center)
    await db_session.commit()

    start_date = datetime.now().date()
    end_date = start_date + timedelta(days=7)
    
    schedule, assignments = await generate_schedule(start_date, end_date)
    
    assert schedule is not None
    assert len(assignments) > 0
    
    # Check if the schedule covers the correct date range
    assert schedule.start_date == start_date
    assert schedule.end_date == end_date
    
    # Check if assignments are within the schedule's date range
    for assignment in assignments:
        assert start_date <= assignment.shift.start_time.date() <= end_date

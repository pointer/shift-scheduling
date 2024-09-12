import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import EmployeeCategory, Employee, WorkCenter
from app.scheduling.scheduler import generate_schedule

@pytest.mark.asyncio
async def test_generate_schedule(test_session: AsyncSession):
    async with test_session.begin():
        # Create sample data
        category = EmployeeCategory(name="Test Category", level=1, hourly_rate=10.0)
        test_session.add(category)
        await test_session.flush()

        employee = Employee(name="Test Employee", category_id=category.id, off_day_preferences={"Monday": 1},
                            shift_preferences=[1, 2, 3], work_center_preferences=[1], delta=0.5)
        test_session.add(employee)

        work_center = WorkCenter(name="Test Work Center", demand={"weekday": {"1": [1, 1, 1]}, "weekend": {"1": [1, 1, 1]}})
        test_session.add(work_center)
        await test_session.flush()

        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        
        schedule, assignments = await generate_schedule(test_session, start_date, end_date)
        
        assert schedule is not None
        assert len(assignments) > 0
        
        # Check if the schedule covers the correct date range
        assert schedule.start_date == start_date
        assert schedule.end_date == end_date
        
        # Refresh assignments to ensure all related objects are loaded
        for assignment in assignments:
            await test_session.refresh(assignment, ['shift'])
            assert assignment.shift is not None, "Assignment should have a related shift"
            assert start_date <= assignment.shift.start_time.date() <= end_date

    # The transaction will be automatically rolled back after the test

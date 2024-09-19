import os, sys, traceback
import pytest
import asyncio
from datetime import datetime, timedelta
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select   
from app.app import app  # Change this line
from app.db.database import get_db, Base
from app.db.models import EmployeeResponse, EmployeeCategory, WorkCenter, Employee, Schedule, GeneratedSchedule
from app.scheduling.algorithm import generate_schedule
from icecream import ic
from sqlalchemy.exc import IntegrityError
import logging

os.environ['USE_REDIS'] = 'False'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_end_to_end(test_session: AsyncSession, client: AsyncClient):
    app.dependency_overrides[get_db] = lambda: test_session

    try:
        # Generate schedule
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=7)
        logger.debug(f"Generating schedule from {start_date} to {end_date}")
        
        try:
            schedule, assignments = await generate_schedule(test_session, start_date, end_date)
            logger.debug(f"Generated schedule: {schedule}")
            logger.debug(f"Generated assignments: {assignments}")
        except Exception as e:
            logger.exception("Error in generate_schedule")
            raise

        # Print debug information
        for assignment in assignments:
            employee = assignment.shift.employee
            work_center = assignment.shift.work_center
            logger.debug(f"Employee {employee.id} (preferences: {employee.work_center_preferences}) assigned to work center {work_center.id}")

        # Verify the generated schedule
        assert schedule is not None
        assert len(assignments) > 0

        # Check if the schedule is persisted in the database
        db_schedule = await test_session.get(Schedule, schedule.id)
        assert db_schedule is not None
        assert db_schedule.start_date == start_date
        assert db_schedule.end_date == end_date

        generated_schedules = (await test_session.execute(
            select(GeneratedSchedule).where(GeneratedSchedule.schedule_id == schedule.id)
        )).scalars().all()
        
        assert len(generated_schedules) == len(assignments)

        # Verify schedule constraints
        for assignment in assignments:
            employee = assignment.shift.employee
            work_center = assignment.shift.work_center
            
            # Check if the employee is assigned to a preferred work center
            assert work_center.id in employee.work_center_preferences, f"Employee {employee.id} assigned to non-preferred work center {work_center.id}. Preferences: {employee.work_center_preferences}"
            
            # Check if the employee is not working more than 5 days in a week
            employee_shifts = [a for a in assignments if a.shift.employee_id == employee.id]
            assert len(employee_shifts) <= 5
            
            # Check if the employee is not working consecutive shifts
            employee_shift_dates = [a.shift.start_time.date() for a in employee_shifts]
            for i in range(len(employee_shift_dates) - 1):
                assert (employee_shift_dates[i+1] - employee_shift_dates[i]).days >= 1

        await test_session.commit()

        # API calls after transaction is committed
        # Verify the API endpoints
        response = await client.get("/employees")
        assert response.status_code == 200
        employees_data = response.json()
        assert len(employees_data) > 0

        response = await client.get("/work-centers")
        assert response.status_code == 200
        work_centers_data = response.json()
        assert len(work_centers_data) > 0

        response = await client.get(f"/schedules/{schedule.id}")
        assert response.status_code == 200
        schedule_data = response.json()
        assert isinstance(schedule_data, dict)  # Ensure we got a valid JSON response
        assert schedule_data.get("start_date") == start_date.isoformat()
        assert schedule_data.get("end_date") == end_date.isoformat()

        response = await client.get(f"/schedules/{schedule.id}/assignments")
        assert response.status_code == 200
        assignments_data = response.json()
        assert len(assignments_data) == len(assignments)

        print("End-to-end test completed successfully!")

    except Exception as e:
        logger.exception("Unexpected error in test_end_to_end")
        raise
    finally:
        # Clear the dependency override
        app.dependency_overrides.clear()
        await test_session.close()

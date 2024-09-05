import pytest
from datetime import datetime, timedelta
from app.scheduling.algorithm import generate_schedule

@pytest.mark.asyncio
async def test_generate_schedule(db_session, sample_data):
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
        
    # Check if assignments respect employee preferences
    employee = sample_data["employee"]
    for assignment in assignments:
        if assignment.shift.employee_id == employee.id:
            # Check if the assigned shift is in the employee's preferences
            shift_index = (assignment.shift.start_time.hour - 6) // 8
            assert shift_index + 1 in employee.shift_preferences
            
            # Check if the assigned work center is in the employee's preferences
            assert assignment.shift.work_center_id in employee.work_center_preferences

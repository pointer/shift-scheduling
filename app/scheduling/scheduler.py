from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import date, datetime, timedelta
from app.db.models import Schedule, ScheduleAssignment, Shift, Employee, WorkCenter

async def generate_schedule(db_session: AsyncSession, start_date: date, end_date: date):
    # Create a new schedule
    schedule = Schedule(start_date=start_date, end_date=end_date)
    db_session.add(schedule)
    await db_session.flush()

    # Fetch existing employees and work centers with eager loading
    employees = (await db_session.execute(
        select(Employee).options(
            selectinload(Employee.category),
            selectinload(Employee.shifts)
        )
    )).scalars().all()
    work_centers = (await db_session.execute(select(WorkCenter))).scalars().all()

    if not employees or not work_centers:
        raise ValueError("No employees or work centers found in the database")

    assignments = []
    current_date = start_date
    while current_date <= end_date:
        for hour in range(8, 20, 8):  # 8am, 4pm shifts
            shift_start = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour)
            shift_end = shift_start + timedelta(hours=8)
            
            shift = Shift(
                start_time=shift_start,
                end_time=shift_end,
                employee_id=employees[0].id,
                work_center_id=work_centers[0].id
            )
            db_session.add(shift)
            await db_session.flush()

            assignment = ScheduleAssignment(schedule_id=schedule.id, shift_id=shift.id)
            db_session.add(assignment)
            assignments.append(assignment)

        current_date += timedelta(days=1)

    await db_session.flush()
    return schedule, assignments
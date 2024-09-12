from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from app.db.models import (
    EmployeeCreate, ShiftCreate, ScheduleCreate, ScheduleAssignmentCreate,
    EmployeeCategoryCreate, EmployeeCategoryResponse, WorkCenterCreate, WorkCenterResponse,
    Employee, EmployeeResponse, Tasks, TaskCreate, TaskUpdate, TaskResponse,
    EmployeeCategory, WorkCenter  # Add these two imports
)
from app.db.database import get_db
from app.db import models as db_models
from worker import generate_schedule_task
from app.core.security import get_current_user
from app.core.cache import redis_client, USE_REDIS
import json
from sqlalchemy import select, text
from datetime import datetime
import os
from typing import List
import random

router = APIRouter()

# @router.post("/employees", response_model=db_models.Employee)
# @router.post("/employees", response_model=db_models.EmployeeResponse)
# async def create_employee(employee: db_models.EmployeeCreate, db: AsyncSession = Depends(get_db)):
#     db_employee = db_models.Employee(**employee.model_dump())
#     db.add(db_employee)
#     await db.commit()
#     await db.refresh(db_employee)
#     return db_employee

@router.get("/")
async def root():
    return {"message": "Hello World"}

@router.get('/favicon.ico')
async def favicon():
    return {"message": "Hello World"}
    # file_name = "favicon.ico"
    # dotenv_path = join(dirname(__file__), '.env')
    # file_path = os.path.join(app.root_path, "static", file_name)
    # return FileResponse(path=file_path, headers={"Content-Disposition": "attachment; filename=" + file_name})

@router.post("/employees", response_model=db_models.EmployeeResponse)
async def create_employee(employee: db_models.EmployeeCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    async with db as session:
        db_employee = db_models.Employee(**employee.model_dump())
        session.add(db_employee)
        await session.commit()
        await session.refresh(db_employee)
        return db_models.EmployeeResponse.model_validate(db_employee)

@router.get("/employees/{employee_id}", response_model=db_models.EmployeeResponse)
async def get_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    async with db as session:
        employee = await session.get(db_models.Employee, employee_id)
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        return db_models.EmployeeResponse.model_validate(employee)

    # if USE_REDIS and redis_client:
    #     cache_key = f"employee:{employee_id}"
    #     cached_employee = redis_client.get(cache_key)
    #     if cached_employee:
    #         return json.loads(cached_employee)
    
    # result = await db.execute(select(db_models.Employee).filter_by(id=employee_id))
    # employee = result.scalar_one_or_none()
    # if employee is None:
    #     raise HTTPException(status_code=404, detail="Employee not found")
    
    # employee_data = db_models.EmployeeResponse.from_orm(employee)
    # if USE_REDIS and redis_client:
    #     redis_client.set(cache_key, employee_data.json(), ex=3600)
    # return employee_data


@router.post("/schedules")
async def create_schedule(schedule: ScheduleCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_schedule = db_models.Schedule(**schedule.model_dump())
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule

@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: int, db: AsyncSession = Depends(get_db)):
    
    schedule = await db_models.Schedule.get(db, schedule_id)
    return schedule
    # async with db:
    #     schedule = db.query(db_models.Schedule).filter(db_models.Schedule.id == schedule_id).first()
    #     if schedule is None:
    #         raise HTTPException(status_code=404, detail="Schedule not found")
    #     return schedule

@router.post("/schedule-assignments")
async def create_schedule_assignment(assignment: ScheduleAssignmentCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_assignment = db_models.ScheduleAssignment(**assignment.model_dump())
    db.add(db_assignment)
    await db.commit()
    await db.refresh(db_assignment)
    return db_assignment

@router.get("/schedules/{schedule_id}/assignments")
async def get_schedule_assignments(schedule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(db_models.ScheduleAssignment).filter_by(schedule_id=schedule_id))
    assignments = result.scalars().all()
    return assignments

@router.post("/employee-categories", response_model=EmployeeCategoryResponse)
async def create_employee_category(category: EmployeeCategoryCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_category = db_models.EmployeeCategory(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return EmployeeCategoryResponse.model_validate(db_category)

@router.post("/work-centers", response_model=WorkCenterResponse)
async def create_work_center(work_center: WorkCenterCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_work_center = db_models.WorkCenter(**work_center.model_dump())
    db.add(db_work_center)
    await db.commit()
    await db.refresh(db_work_center)
    return WorkCenterResponse.model_validate(db_work_center)

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_task = Tasks(**task.model_dump())
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Tasks, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tasks))
    tasks = result.scalars().all()
    return tasks

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_task = await db.get(Tasks, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = task.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_task = await db.get(Tasks, task_id)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(db_task)
    await db.commit()
    return {"ok": True}

@router.post("/tasks/generate-fake", response_model=List[TaskResponse])
async def create_fake_tasks(
    num_tasks: int = Query(10, description="Number of fake tasks to generate"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    fake_tasks = generate_fake_tasks(num_tasks)
    db_tasks = []
    for task in fake_tasks:
        db_task = Tasks(**task.model_dump())
        db.add(db_task)
        db_tasks.append(db_task)
    
    await db.commit()
    for task in db_tasks:
        await db.refresh(task)
    
    return db_tasks

@router.post("/generate-fake-data")
async def generate_fake_data(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
    num_categories: int = Query(5, description="Number of employee categories to generate"),
    num_work_centers: int = Query(3, description="Number of work centers to generate"),
    num_employees: int = Query(20, description="Number of employees to generate")
):
    # Generate fake employee categories
    categories_sql = """
    INSERT INTO employee_categories (name, level, hourly_rate)
    VALUES (:name, :level, :hourly_rate)
    """
    categories = [
        {"name": f"Category {i}", "level": random.randint(1, 5), "hourly_rate": round(random.uniform(10, 50), 2)}
        for i in range(1, num_categories + 1)
    ]
    await db.execute(text(categories_sql), categories)

    # Generate fake work centers
    work_centers_sql = """
    INSERT INTO work_centers (name, demand)
    VALUES (:name, :demand)
    """
    work_centers = [
        {
            "name": f"Work Center {i}",
            "demand": json.dumps({
                "weekday": {str(k): [random.randint(1, 5) for _ in range(3)] for k in range(1, 6)},
                "weekend": {str(k): [random.randint(1, 3) for _ in range(3)] for k in range(1, 6)}
            })
        }
        for i in range(1, num_work_centers + 1)
    ]
    await db.execute(text(work_centers_sql), work_centers)

    # Generate fake employees
    employees_sql = """
    INSERT INTO employees (name, category_id, off_day_preferences, shift_preferences, work_center_preferences, delta)
    VALUES (:name, :category_id, :off_day_preferences, :shift_preferences, :work_center_preferences, :delta)
    """
    employees = [
        {
            "name": f"Employee {i}",
            "category_id": random.randint(1, num_categories),
            "off_day_preferences": json.dumps({day: random.randint(1, 7) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']}),
            "shift_preferences": json.dumps([random.randint(1, 3) for _ in range(3)]),
            "work_center_preferences": json.dumps([random.randint(1, num_work_centers) for _ in range(random.randint(1, num_work_centers))]),
            "delta": round(random.uniform(0, 1), 2)
        }
        for i in range(1, num_employees + 1)
    ]
    await db.execute(text(employees_sql), employees)

    await db.commit()

    return {
        "message": "Fake data generated successfully",
        "categories_created": len(categories),
        "work_centers_created": len(work_centers),
        "employees_created": len(employees)
    }

@router.get("/employee-categories", response_model=List[EmployeeCategoryResponse])
async def get_employee_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmployeeCategory))
    categories = result.scalars().all()
    return [EmployeeCategoryResponse.model_validate(category) for category in categories]

@router.get("/work-centers", response_model=List[WorkCenterResponse])
async def get_work_centers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WorkCenter))
    work_centers = result.scalars().all()
    return [WorkCenterResponse.model_validate(work_center) for work_center in work_centers]

@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee))
    employees = result.scalars().all()
    return [EmployeeResponse.model_validate(employee) for employee in employees]

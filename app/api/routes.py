from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.models import EmployeeCreate, ShiftCreate, ScheduleCreate, ScheduleAssignmentCreate, EmployeeCategoryCreate, WorkCenterCreate
from app.db.database import get_db
from app.db import models as db_models
from worker import generate_schedule_task
from app.core.security import get_current_user
from app.core.cache import redis_client
import json

router = APIRouter()

@router.post("/employees")
async def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_employee = db_models.Employee(
        name=employee.name,
        category_id=employee.category_id,
        off_day_preferences=employee.off_day_preferences,
        shift_preferences=employee.shift_preferences,
        work_center_preferences=employee.work_center_preferences
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/employees/{employee_id}")
async def get_employee(employee_id: int, db: Session = Depends(get_db)):
    cache_key = f"employee:{employee_id}"
    cached_employee = redis_client.get(cache_key)
    if cached_employee:
        return json.loads(cached_employee)
    
    employee = db.query(db_models.Employee).filter(db_models.Employee.id == employee_id).first()
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    redis_client.setex(cache_key, 3600, json.dumps(employee.__dict__))
    return employee

@router.post("/schedules")
async def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_schedule = db_models.Schedule(**schedule.dict())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    return db_schedule

@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    schedule = db.query(db_models.Schedule).filter(db_models.Schedule.id == schedule_id).first()
    if schedule is None:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.post("/schedule-assignments")
async def create_schedule_assignment(assignment: ScheduleAssignmentCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_assignment = db_models.ScheduleAssignment(**assignment.dict())
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.get("/schedules/{schedule_id}/assignments")
async def get_schedule_assignments(schedule_id: int, db: Session = Depends(get_db)):
    assignments = db.query(db_models.ScheduleAssignment).filter(db_models.ScheduleAssignment.schedule_id == schedule_id).all()
    return assignments

@router.post("/employee-categories")
async def create_employee_category(category: EmployeeCategoryCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_category = db_models.EmployeeCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.post("/work-centers")
async def create_work_center(work_center: WorkCenterCreate, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    db_work_center = db_models.WorkCenter(**work_center.dict())
    db.add(db_work_center)
    db.commit()
    db.refresh(db_work_center)
    return db_work_center

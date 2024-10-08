from __future__ import annotations

import asyncio
import datetime
from typing import List
from typing import Optional
from sqlalchemy import JSON, Float, Integer, String, Date, DateTime, Enum
from sqlalchemy import ForeignKey, Column
from sqlalchemy import func
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, NoResultFound
from app.core.cache import redis_client, USE_REDIS
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any
from uuid import uuid4
from typing import Optional  
# from sqlmodel import Field, SQLModel  
from enum import Enum as PyEnum  
from datetime import datetime, timezone  
# from app.db.database import Base
import logging
logging.basicConfig()    
logging.getLogger("sqlalchemy.engine").setLevel(logging.DEBUG)
from app.core.config import settings


class Base(AsyncAttrs, DeclarativeBase):
    pass


class EmployeeCategory(Base):
    __tablename__ = "employee_categories"

    # id = Column(Integer, primary_key=True, index=True)
    id: Mapped[int] = mapped_column(primary_key=True, index=True)   
    name = Column(String(100), unique=True, index=True)  # Specify length for VARCHAR
    level = Column(Integer)  # Add this line
    hourly_rate = Column(Float)  # Add this line

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        category = cls(**kwargs)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

class WorkCenter(Base):
    __tablename__ = "work_centers"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)   
    # id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)  # Specify length for VARCHAR
    demand = Column(JSON)  # Add this line

class Employee(Base):
    __tablename__ = "employees"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)   
    # id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)  # Specify length for VARCHAR
    category_id = Column(Integer, ForeignKey("employee_categories.id"))
    off_day_preferences = Column(JSON)
    shift_preferences = Column(JSON)
    work_center_preferences = Column(JSON)
    delta = Column(Float)

    category = relationship("EmployeeCategory", lazy="selectin")
    shifts = relationship("Shift", back_populates="employee", lazy="selectin")

class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)   
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    employee_id: Mapped[int] = mapped_column(Integer, ForeignKey("employees.id"))
    work_center_id: Mapped[int] = mapped_column(Integer, ForeignKey("work_centers.id"))
    
    employee = relationship("Employee", back_populates="shifts", lazy="selectin")
    work_center = relationship("WorkCenter", lazy="selectin")
    assignment = relationship("ScheduleAssignment", back_populates="shift", uselist=False, lazy="selectin")

class ScheduleStatus(str, PyEnum):  
    DRAFT = "draft"  
    PUBLISHED = "published"  
    ARCHIVED = "archived"  

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    assignments = relationship("ScheduleAssignment", back_populates="schedule", lazy="selectin")

class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.id"), nullable=False)

    schedule = relationship("Schedule", back_populates="assignments", lazy="selectin")
    shift = relationship("Shift", back_populates="assignment", lazy="selectin")

class EmployeeCategoryCreate(BaseModel):
    name: str   
    level: int
    hourly_rate: float

class EmployeeCategoryResponse(BaseModel):
    id: int
    name: str
    level: int
    hourly_rate: float

    model_config = ConfigDict(from_attributes=True)

class WorkCenterCreate(BaseModel):
    name: str
    demand: Dict[str, Dict[str, List[int]]]

class EmployeeCreate(BaseModel):
    name: str
    category_id: int
    off_day_preferences: Dict[str, int]
    shift_preferences: List[int]
    work_center_preferences: List[int]
    delta: float

class ShiftCreate(BaseModel):
    start_time: str
    end_time: str
    employee_id: int
    work_center_id: int

class ScheduleCreate(BaseModel):
    start_date: str
    end_date: str

class ScheduleAssignmentCreate(BaseModel):
    schedule_id: int
    shift_id: int
    
class EmployeeResponse(BaseModel):
    id: int
    name: str
    category_id: int
    off_day_preferences: Dict[str, int]
    shift_preferences: List[int]
    work_center_preferences: List[int]
    delta: float

    class Config:
        orm_mode = True
  
# Uncomment and update the User model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # Specify length
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)  # Specify length

    @classmethod
    async def create(cls, db: AsyncSession, **kwargs):
        user = cls(**kwargs)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def get(cls, db: AsyncSession, id: str):
        try:
            user = await db.get(cls, id)
        except NoResultFound:
            return None
        return user

    @classmethod
    async def get_all(cls, db: AsyncSession):
        return (await db.execute(select(cls))).scalars().all()

class TaskStatus(PyEnum):
    NOT_STARTED = "not_started"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Tasks(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # Specify length
    # id = Column(Integer, primary_key=True, index=True)
    # title = Column(String(100), index=True)
    # description = Column(String)
    description: Mapped[str] = mapped_column(String(255), unique=False, nullable=False) 
    # status = Column(String)  # Add this line
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.NOT_STARTED)
   
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Add other fields as needed

# Add this function at the end of the file
async def create_tables():
    engine = create_async_engine(settings.DATABASE_URL,)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from pydantic import BaseModel, ConfigDict

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.NOT_STARTED

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None

class TaskResponse(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
  

# Add this import if it's not already present
from typing import Dict, List

class WorkCenterResponse(BaseModel):
    id: int
    name: str
    demand: Dict[str, Dict[str, List[int]]]

    class Config:
        orm_mode = True
  
    
class GeneratedSchedule(Base):
    __tablename__ = "generated_schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    work_center_id = Column(Integer, ForeignKey("work_centers.id"), nullable=False)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, nullable=False)

    schedule = relationship("Schedule", back_populates="generated_assignments")
    employee = relationship("Employee")
    work_center = relationship("WorkCenter")

Schedule.generated_assignments = relationship("GeneratedSchedule", back_populates="schedule")
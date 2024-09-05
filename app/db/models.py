from sqlalchemy import Column, Integer, String, Boolean, Date, Numeric, ForeignKey, DateTime, Enum, JSON, Float
from sqlalchemy.orm import relationship, Mapped
from .database import Base
from pydantic import BaseModel
from typing import List, Dict, Any

class EmployeeCategory(Base):
    __tablename__ = "employee_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    level = Column(Integer)  # Higher level means higher category
    hourly_rate = Column(Numeric(10, 2))

class WorkCenter(Base):
    __tablename__ = "work_centers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    demand: Mapped[Dict[str, Any]] = Column(JSON)

class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    name: Mapped[str] = Column(String(255), index=True)
    category_id: Mapped[int] = Column(Integer, ForeignKey("employee_categories.id"))
    shifts: Mapped[List["Shift"]] = relationship("Shift", back_populates="employee")
    
    category: Mapped["EmployeeCategory"] = relationship("EmployeeCategory")
    
    # New fields for preferences
    off_day_preferences: Mapped[Dict[str, int]] = Column(JSON)
    shift_preferences: Mapped[List[int]] = Column(JSON)
    work_center_preferences: Mapped[List[int]] = Column(JSON)
    assignments: Mapped[Dict[str, Any]] = Column(JSON)
    delta: Mapped[float] = Column(Float)

class EmployeeCreate(BaseModel):
    name: str
    category_id: int
    off_day_preferences: Dict[str, int]
    shift_preferences: List[int]
    work_center_preferences: List[int]
    delta: float

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    work_center_id = Column(Integer, ForeignKey("work_centers.id"))
    
    employee = relationship("Employee", back_populates="shifts")
    work_center = relationship("WorkCenter")

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Enum('draft', 'published', 'archived'), default='draft')

class ScheduleAssignment(Base):
    __tablename__ = "schedule_assignments"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))
    shift_id = Column(Integer, ForeignKey("shifts.id"))

    schedule = relationship("Schedule")
    shift = relationship("Shift")

class EmployeeCategoryCreate(BaseModel):
    name: str
    level: int
    hourly_rate: float

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
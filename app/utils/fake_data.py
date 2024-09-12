from faker import Faker
from app.db.models import TaskCreate, TaskStatus, EmployeeCategory, Employee, WorkCenter
from typing import List
import random

fake = Faker()

def generate_fake_tasks(num_tasks: int = 10) -> List[TaskCreate]:
    tasks = []
    for _ in range(num_tasks):
        task = TaskCreate(
            title=fake.sentence(nb_words=4),
            description=fake.paragraph(),
            status=random.choice(list(TaskStatus))
        )
        tasks.append(task)
    return tasks

def generate_fake_employee_categories(num_categories: int = 5) -> List[EmployeeCategory]:
    categories = []
    for _ in range(num_categories):
        category = EmployeeCategory(
            name=fake.job(),
            level=random.randint(1, 5),
            hourly_rate=round(random.uniform(10, 50), 2)
        )
        categories.append(category)
    return categories

def generate_fake_work_centers(num_centers: int = 7) -> List[WorkCenter]:
    centers = []
    for _ in range(num_centers):
        center = WorkCenter(
            name=fake.company(),
            demand={
                "weekday": {str(k): [random.randint(1, 5) for _ in range(3)] for k in range(1, 6)},
                "weekend": {str(k): [random.randint(1, 3) for _ in range(3)] for k in range(1, 6)}
            }
        )
        centers.append(center)
    return centers

def generate_fake_employees(categories: List[EmployeeCategory], work_centers: List[WorkCenter], num_employees: int = 20) -> List[Employee]:
    employees = []
    for _ in range(num_employees):
        employee = Employee(
            name=fake.name(),
            category_id=random.choice(categories).id,
            off_day_preferences={day: random.randint(1, 7) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
            shift_preferences=[random.randint(1, 3) for _ in range(3)],
            work_center_preferences=[center.id for center in random.sample(work_centers, k=random.randint(1, len(work_centers)))],
            delta=round(random.uniform(0, 1), 2)
        )
        employees.append(employee)
    return employees

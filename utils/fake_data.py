from faker import Faker
from app.db.models import TaskCreate, TaskStatus
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

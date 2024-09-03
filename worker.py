from celery import Celery
from app.core.config import settings
from app.scheduling.algorithm import generate_schedule

celery = Celery('tasks', broker=settings.CELERY_BROKER_URL)

@celery.task
def generate_schedule_task(start_date, end_date):
    return generate_schedule(start_date, end_date)

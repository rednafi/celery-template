import time

from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task
def add(x, y):
    result = x + y
    logging.info(f"ADD result: {result}")
    time.sleep(2)
    return result


@shared_task
def sub(a, b):
    result = a - b
    logging.info(f"SUB result: {result}")
    time.sleep(2)
    return result

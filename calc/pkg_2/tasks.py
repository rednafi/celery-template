import time

from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task
def mul(a, b):
    result = a * b
    logging.info(f"MUL result: {result}")
    time.sleep(2)
    return result


@shared_task
def div(a, b):
    result = a / b
    logging.info(f"DIV result: {result}")
    time.sleep(2)
    return result

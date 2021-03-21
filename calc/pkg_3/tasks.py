from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task(acks_late=True)
def modulo(x, y):
    try:
        result = x % y
        logging.info(f"Modulo result: {result}")

    except ZeroDivisionError as exc:
        logging.error("Modulo error")
        raise

from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task
def add(x, y):
    result = x + y
    logging.info(f"ADD result: {result}")
    return result


@shared_task
def sub(a, b):
    result = a - b
    logging.info(f"SUB result: {result}")
    return result


@shared_task
def mul(a, b):
    result = a * b
    logging.info(f"MUL result: {result}")
    return result


@shared_task
def div(a, b):
    result = a / b
    logging.info(f"DIV result: {result}")
    return result


@shared_task(acks_late=True)
def modulo(x, y):
    try:
        result = x % y
        logging.info(f"MODULO result: {result}")

    except ZeroDivisionError as exc:
        logging.error("Modulo error")
        raise

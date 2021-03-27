import httpx
from celery import shared_task
from celery.utils.log import get_task_logger

logging = get_task_logger(__name__)


@shared_task
def get_data(url):
    with httpx.Client() as client:
        response = client.get(url)
        logging.info(f"HTTP GET status: {response.status_code}")
        return response.json()


@shared_task
def post_data(url, payload):
    with httpx.Client() as client:
        response = client.post(url, data=payload)
        logging.info(f"HTTP POST status: {response.status_code}")
        return response.json()


@shared_task
def put_data(url, payload):
    with httpx.Client() as client:
        response = client.put(url, data=payload)
        logging.info(f"HTTP PUT status: {response.status_code}")
        return response.json()


@shared_task
def delete_data(url, params):
    with httpx.Client() as client:
        response = client.delete(url, params=params)
        logging.info(f"HTTP DELETE status: {response.status_code}")
        return response.json()

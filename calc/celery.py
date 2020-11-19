from enum import Enum

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger
from kombu import Queue

app = Celery("calc")

# app.autodiscover_tasks()
app.conf.update(
    {
        "broker_url": "redis://localhost:6379/0",
        "result_backend": "redis://localhost:6379/1",
        "task_queues": (
            Queue("default"),
            Queue("q1"),
        ),
        "task_default_queue": "default",
        "task_routes": {
            "calc.pkg_1.tasks.add": {"queue": "default"},
            "calc.pkg_1.tasks.sub": {"queue": "default"},
            "calc.pkg_2.tasks.mul": {"queue": "q1"},
            "calc.pkg_2.tasks.div": {"queue": "q1"},
        },
        "imports": (
            "calc.pkg_1.tasks",
            "calc.pkg_2.tasks",
        ),
    }
)


class LogColor(str, Enum):
    START_CYAN = "\033[92m"
    END_WHITE = "\033[0m"


@after_setup_task_logger.connect
def setup_task_logger(logger, *args, **kwargs):
    for handler in logger.handlers:
        handler.setFormatter(
            TaskFormatter(
                LogColor.START_CYAN
                + """
📗 Async Task Log
==================

TIMESTAMP   : %(asctime)s
Task ID     : %(task_id)s
TASK NAME   : %(task_name)s
LOG MSG     : %(name)s - %(levelname)s - %(message)s
"""
                + LogColor.END_WHITE
            )
        )


# For development: You can use this to run the tasks instantly, without workers
#app.conf.update(TASK_ALWAYS_EAGER=True)

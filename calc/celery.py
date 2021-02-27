from dataclasses import dataclass
from enum import Enum

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger
from kombu import Exchange, Queue

from calc.settings import config

app = Celery("calc")



# Setting up Broker URL and Result Backend.
app.conf.broker_url = config.CELERY_BROKER_URL
app.conf.result_backend = config.CELERY_RESULT_BACKEND

# Declaring AMQP exchanges.
exchange_alpha = Exchange("alpha", type="direct")
exchange_beta = Exchange("beta", type="direct")

# Declaring AMQP Queues and binding them with the Exchanges.
queue_default = Queue("default", exchange_alpha, routing_key="alpha.default")
queue_another = Queue("another", exchange_beta, routing_key="beta.another")

# Injecting task queue config to Celery config.
app.conf.task_queues = (queue_default, queue_another)

# Declaring default exchange and queue config.
app.conf.task_default_queue = "default"
app.conf.task_default_exchange = "alpha"
app.conf.task_default_routing_key = "default"

# Importing the task modules.
app.conf.imports = ("calc.pkg_1.tasks", "calc.pkg_2.tasks")


@dataclass(frozen=True)
class TaskRouter:

    # Queue configs.
    queue_config_default = {
        "exchange": "alpha",
        "exchange_type": "direct",
        "routing_key": "alpha.default",
    }

    queue_config_another = {
        "exchange": "beta",
        "exchange_type": "direct",
        "routing_key": "beta.another",
    }

    # Tasks in queues
    default = (
        "calc.pkg_1.tasks.add",
        "calc.pkg_1.tasks.sub",
    )

    another = (
        "calc.pkg_2.tasks.mul",
        "calc.pkg_2.tasks.div",
    )

    def route(self, name):
        if name in self.default:
            return self.queue_config_default

        elif name in self.another:
            return self.queue_config_another


# Define a simple task router.
def route_task(name, args, kwargs, options, task=None, **kw):
    return TaskRouter().route(name)


# Registering the task routers.
app.conf.task_routes = (route_task,)


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
# app.conf.update(TASK_ALWAYS_EAGER=True)

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
queue_default = Queue(
    name="default",
    exchange=exchange_alpha,
    routing_key="alpha.default",
)
queue_another_0 = Queue(
    name="another_0",
    exchange=exchange_beta,
    routing_key="beta.another_0",
)
queue_another_1 = Queue(
    name="another_1",
    exchange=exchange_beta,
    routing_key="beta.another_1",
)
queue_another_2 = Queue(
    name="another_2",
    exchange=exchange_beta,
    routing_key="beta.another_2",
)


# Registering task queues into Celery config.
app.conf.task_queues = (
    queue_default,
    queue_another_0,
    queue_another_1,
    queue_another_2,
)

# Declaring default exchange and queue config. This is mostly useless because
# our clever TaskRouter will throw an exception when an orphan task without properly
# configured worker and queue appears.
app.conf.task_default_queue = "default"
app.conf.task_default_exchange = "alpha"
app.conf.task_default_routing_key = "alpha.default"

# Importing the task modules.
app.conf.imports = ("calc.pkg_1.tasks", "calc.pkg_2.tasks")


class RouterConfigError(Exception):
    """Custom exception to denote error in celery route configuration."""

    pass


class RouterMeta(type):
    @staticmethod
    def _is_dunder(name):
        """Returns True if a __dunder__ name, False otherwise."""

        return (
            len(name) > 4
            and name[:2] == name[-2:] == "__"
            and name[2] != "_"
            and name[-3] != "_"
        )

    def __new__(metacls, cls, bases, namespace):

        # Only attribute QUEUES_TO_TASKS is allowed inside the target Router class.
        allowed_attr = "QUEUES_TO_TASKS"

        # Filtering out the dunder methods so that we're dealing with only the
        # user-defined attributes.
        _namespace = {}
        for attr_name, attr_value in namespace.items():
            if not metacls._is_dunder(attr_name):
                _namespace[attr_name] = attr_value

        # Router class cannot be empty.
        if not _namespace:
            raise RouterConfigError("router config cannot be empty")

        # Raise error if Router class doesn't have the QUEUES_TO_TASKS attribute.
        if not allowed_attr in _namespace.keys():
            raise RouterConfigError(f"router config should contain {allowed_attr}")

        # Guardrails to make sure the config dicts in the Router class is consistent.
        if len(_namespace.keys()) > 1:
            raise RouterConfigError(
                f"{cls} should only contain attribute {allowed_attr}"
            )

        # Attribute QUEUES_TO_TASKS can only have dict value.
        if not isinstance(_namespace[allowed_attr], dict):
            raise RouterConfigError(f"{allowed_attr} value should be a dict")

        # Attribute QUEUES_TO_TASKS cannot be an empty dict.
        if not _namespace[allowed_attr]:
            raise RouterConfigError(f"{allowed_attr} value cannot be an empty dict")

        for k, v in _namespace[allowed_attr].items():
            # Keys of QUEUES_TO_TASKS can only be Queue objects.
            if not isinstance(k, Queue):
                raise RouterConfigError(f"{attr_name} keys should be of type {Queue}")

            # Values of QUEUES_TO_TASKS need to be tuple holding string objects.
            if not isinstance(v, tuple):
                raise RouterConfigError(f"{attr_name} value format is incorrect")

            # Elements inside the tuple can only be string objects.
            for elem in v:
                if not isinstance(elem, str):
                    raise RouterConfigError("task name need to be of type str")

        QUEUES_TO_TASKS = _namespace["QUEUES_TO_TASKS"]

        # Dynamic router method.
        def route(_, task_name):
            for queue, tasks in QUEUES_TO_TASKS.items():
                for task in tasks:
                    if not task == task_name:
                        continue

                    return {
                        "exchange": queue.exchange.name,
                        "exchange_type": queue.exchange.type,
                        "routing_key": queue.routing_key,
                    }

        namespace["route"] = route

        return super().__new__(metacls, cls, bases, namespace)


class Router(metaclass=RouterMeta):
    QUEUES_TO_TASKS = {
        queue_default: ("calc.pkg_1.tasks.add",),
        queue_another_0: ("calc.pkg_1.tasks.sub",),
        queue_another_1: ("calc.pkg_2.tasks.mul",),
        queue_another_2: ("calc.pkg_2.tasks.div",),
    }


# Define a simple task router.
def route_task(name, args, kwargs, options, task=None, **kw):
    return Router().route(name)


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


# For development: You can use this to run the tasks instantly, without workers.
# app.conf.update(TASK_ALWAYS_EAGER=True)

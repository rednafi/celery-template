from enum import Enum

from celery import Celery
from celery.app.log import TaskFormatter
from celery.signals import after_setup_task_logger
from kombu import Exchange, Queue

from app.settings import config


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
Task Log
==================

TIMESTAMP: %(asctime)s
Task ID  : %(task_id)s
TASK NAME: %(task_name)s
LOG LEVEL: %(levelname)s
LOG MSG  : %(message)s

"""
                + LogColor.END_WHITE
            )
        )


class ExchangeName(str, Enum):
    ALPHA = "alpha"
    BETA = "beta"


class ExchangeType(str, Enum):
    DIRECT = "direct"
    TOPIC = "topic"
    FANOUT = "fanout"


class QueueName(str, Enum):
    DEFAULT = "default"
    ANOTHER_1 = "another_1"
    ANOTHER_2 = "another_2"
    ANOTHER_3 = "another_3"


class RouteKeyName(str, Enum):
    """Routing key attributes have the same names as the queues."""

    DEFAULT = f"{ExchangeName.ALPHA}.{QueueName.DEFAULT}"
    ANOTHER_1 = f"{ExchangeName.BETA}.{QueueName.ANOTHER_1}"
    ANOTHER_2 = f"{ExchangeName.BETA}.{QueueName.ANOTHER_2}"
    ANOTHER_3 = f"{ExchangeName.BETA}.{QueueName.ANOTHER_3}"


app = Celery("calc")


# Setting up Broker URL and Result Backend.
app.conf.broker_url = config.CELERY_BROKER_URL
app.conf.result_backend = config.CELERY_RESULT_BACKEND

# Declaring default exchange and queue config. This exchange and queue will be used
# when a task has unspecified or ill-configured QUEUES_TO_TASKS relationship.
app.conf.task_default_exchange = ExchangeName.ALPHA
app.conf.task_default_exchange_type = ExchangeType.DIRECT
app.conf.task_default_queue = QueueName.DEFAULT
app.conf.task_default_routing_key = RouteKeyName.DEFAULT

# Declaring AMQP exchanges.
exchange_alpha = Exchange(ExchangeName.ALPHA, type=ExchangeType.DIRECT)
exchange_beta = Exchange(ExchangeName.BETA, type=ExchangeType.DIRECT)

# Declaring AMQP Queues and binding them with the Exchanges.
queue_default = Queue(
    QueueName.DEFAULT, exchange_alpha, routing_key=RouteKeyName.DEFAULT
)

queue_another_1 = Queue(
    QueueName.ANOTHER_1, exchange_beta, routing_key=RouteKeyName.ANOTHER_1
)
queue_another_2 = Queue(
    QueueName.ANOTHER_2, exchange_beta, routing_key=RouteKeyName.ANOTHER_2
)
queue_another_3 = Queue(
    QueueName.ANOTHER_3, exchange_beta, routing_key=RouteKeyName.ANOTHER_3
)


# Registering task queues into Celery config.
app.conf.task_queues = (
    queue_default,
    queue_another_1,
    queue_another_2,
    queue_another_3,
)


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


# Importing the task modules.
app.conf.imports = ("app.proc.tasks", "app.proc.tasks", "app.io.tasks")


class Router(metaclass=RouterMeta):
    QUEUES_TO_TASKS = {
        queue_default: ("app.proc.tasks.add", "app.proc.tasks.sub"),
        queue_another_1: ("app.proc.tasks.mul", "app.proc.tasks.div"),
        queue_another_2: ("app.proc.tasks.modulo",),
        queue_another_3: (
            "app.io.tasks.get_data",
            "app.io.tasks.post_data",
            "app.io.tasks.put_data",
            "app.io.tasks.delete_data",
        ),
    }


# Define a simple task router.
def route_task(name, args, kwargs, options, task=None, **kw):
    return Router().route(name)


# Registering the task routers.
app.conf.task_routes = (route_task,)


# For development: You can use this to run the tasks instantly, without workers.
# app.conf.update(TASK_ALWAYS_EAGER=True)

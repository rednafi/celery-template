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


class RouterConfigError(Exception):
    """Custom exception to denote error in celery route configuration."""

    pass


class RouterMeta(type):
    """Metaclass to make sure that the target TaskRouter class strictly
    follows this format—

    class TaskRouter(metaclass=RouterMeta):

        EXCHANGES = {
            "alpha": {
                "exchange": "alpha",
                "exchange_type": "direct",
                "routing_key": "alpha.default",
            },
            "beta": {
                "exchange": "beta",
                "exchange_type": "direct",
                "routing_key": "beta.another",
            },

        }

        EXCHANGES_TO_QUEUES = {"alpha": "default", "beta": "another"}

        QUEUES_TO_TASKS = {
            "default": (
                "root.pkg_1.tasks.task_1",
                "root.pkg_1.tasks.task_2",
            ),
            "another": (
                "root.pkg_2.tasks.task_1",
                "root.pkg_2.tasks.task_2",
            ),
        }

    """

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

        # Only these attributes are allowed in the classes that has RouteMeta
        allowed_attrs = ("EXCHANGES", "QUEUES_TO_EXCHANGES", "QUEUES_TO_TASKS")

        # Filtering out the dunder methods so that we're dealing with only the
        # user-defined attributes
        _namespace = {}
        for attr_name, attr_value in namespace.items():
            if not metacls._is_dunder(attr_name):
                _namespace[attr_name] = attr_value

        # TaskRouter class cannot be empty
        if not _namespace:
            raise RouterConfigError("router config cannot be empty")

        # Guardrails to make sure the config dicts in the target class is consistent
        if not tuple(_namespace.keys()) == allowed_attrs:
            raise RouterConfigError(f"{cls} should contain attributes {allowed_attrs}")

        for attr_name, attr_value in _namespace.items():
            if not isinstance(attr_value, dict):
                raise RouterConfigError(f"{attr_name} should be a dict")

            if not attr_value:
                raise RouterConfigError(f"{attr_name} cannot be an empty dict")

            if attr_name == "EXCHANGES":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise RouterConfigError(f"{attr_name} keys have to be strings")

                    if not isinstance(v, dict):
                        raise RouterConfigError(f"{attr_name} format is incorrect")

                    if tuple(v.keys()) != ("exchange", "exchange_type", "routing_key"):
                        raise RouterConfigError(f"{attr_name} format is incorrect")

            if attr_name == "QUEUES_TO_EXCHANGES":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise RouterConfigError(f"{attr_name} keys have to be strings")

                    if not isinstance(v, str):
                        raise RouterConfigError(
                            f"{attr_name} values have to be strings"
                        )

            if attr_name == "QUEUES_TO_TASKS":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise RouterConfigError(f"{attr_name} keys have to be strings")

                    if not isinstance(v, (tuple, list)):
                        raise RouterConfigError(f"{attr_name} format is incorrect")

        EXCHANGES = _namespace["EXCHANGES"]
        QUEUES_TO_EXCHANGES = _namespace["QUEUES_TO_EXCHANGES"]
        QUEUES_TO_TASKS = _namespace["QUEUES_TO_TASKS"]

        # Config dicts in the target class must have same length

        if not len(EXCHANGES) == len(set(QUEUES_TO_EXCHANGES.values())):
            raise RouterConfigError("inconsistent exchange count")

        if not len(QUEUES_TO_EXCHANGES) == len(QUEUES_TO_TASKS):
            raise RouterConfigError("queue mapping dicts must have same length")

        if set(EXCHANGES.keys()) != set(QUEUES_TO_EXCHANGES.values()):
            raise RouterConfigError("inconsistent exchange name")

        if set(QUEUES_TO_EXCHANGES.keys()) != set(QUEUES_TO_TASKS.keys()):
            raise RouterConfigError("inconsistent queue name")

        # Inject the route method into the target class
        def route(_, task_name):
            # Self is omitted here to save attribute search for efficiency gain
            for exchange, tasks in zip(
                QUEUES_TO_EXCHANGES.values(), QUEUES_TO_TASKS.values()
            ):

                for task in tasks:
                    if task_name == task:
                        ex_cnf = EXCHANGES.get(exchange)
                        return ex_cnf
                    else:
                        ex_cnf = None

            if ex_cnf is None:
                raise RouterConfigError(f"task {task_name} not found")

        namespace["route"] = route
        return super().__new__(metacls, cls, bases, namespace)


class TaskRouter(metaclass=RouterMeta):

    EXCHANGES = {
        "alpha": {
            "exchange": "alpha",
            "exchange_type": "direct",
            "routing_key": "alpha.default",
        },
        "beta": {
            "exchange": "beta",
            "exchange_type": "direct",
            "routing_key": "beta.another",
        },
    }

    QUEUES_TO_EXCHANGES = {"default": "alpha", "another": "beta"}

    QUEUES_TO_TASKS = {
        "default": (
            "calc.pkg_1.tasks.add",
            "calc.pkg_1.tasks.sub",
        ),
        "another": (
            "calc.pkg_2.tasks.mul",
            "calc.pkg_2.tasks.div",
        ),
    }


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

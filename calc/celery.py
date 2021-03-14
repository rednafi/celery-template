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
queue_another_0 = Queue("another_0", exchange_beta, routing_key="beta.another_0")
queue_another_1 = Queue("another_1", exchange_beta, routing_key="beta.another_1")
queue_another_2 = Queue("another_2", exchange_beta, routing_key="beta.another_2")

# Injecting task queue config to Celery config.
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
app.conf.task_default_routing_key = "default"

# Importing the task modules.
app.conf.imports = ("calc.pkg_1.tasks", "calc.pkg_2.tasks")


class RouterConfigError(Exception):
    """Custom exception to denote error in celery route configuration."""

    pass


class RouterMeta(type):
    """Metaclass to make sure that the target TaskRouter class strictly
    follows this format—

    EXCHANGES = {
        "alpha": {
            "exchange_type": "direct",
        },
        "beta": {
            "exchange_type": "direct",
        },
    }

    QUEUES_TO_EXCHANGES = {
        "default": "alpha",
        "another_0": "beta",
        "another_1": "beta",
        "another_2": "beta",
    }

    QUEUES_TO_TASKS = {
        "default": ("root.pkg_1.tasks.task_0",),
        "another_0": ("root.pkg_1.tasks.task_1",),
        "another_1": ("root.pkg_2.tasks.task_2",),
        "another_2": ("root.pkg_2.tasks.task_3",),
    }

    Returns
    -------
        .route(task_name="root.pkg_2.tasks.task_3")
        returns the corresponding Exchange configuration

        {
            "exchange_type": "direct",
            "exchange": "beta",
            "routing_key": "beta.another_2"
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

        # Only these attributes are allowed in the classes that has RouteMeta.
        allowed_attrs = ("EXCHANGES", "QUEUES_TO_EXCHANGES", "QUEUES_TO_TASKS")

        # Filtering out the dunder methods so that we're dealing with only the
        # user-defined attributes.
        _namespace = {}
        for attr_name, attr_value in namespace.items():
            if not metacls._is_dunder(attr_name):
                _namespace[attr_name] = attr_value

        # TaskRouter class cannot be empty.
        if not _namespace:
            raise RouterConfigError("router config cannot be empty")

        # Guardrails to make sure the config dicts in the target class is consistent.
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
                        raise RouterConfigError(f"{attr_name} keys should be strings")

                    if not isinstance(v, dict):
                        raise RouterConfigError(f"{attr_name} format is incorrect")

                    if not "exchange_type" in v.keys():
                        raise RouterConfigError(f"{attr_name} format is incorrect")

            if attr_name == "QUEUES_TO_EXCHANGES":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise RouterConfigError(f"{attr_name} keys should be strings")

                    if not isinstance(v, str):
                        raise RouterConfigError(f"{attr_name} values should be strings")

            if attr_name == "QUEUES_TO_TASKS":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise RouterConfigError(f"{attr_name} keys should be strings")

                    if not isinstance(v, (tuple, list)):
                        raise RouterConfigError(f"{attr_name} format is incorrect")

        EXCHANGES = _namespace["EXCHANGES"]
        QUEUES_TO_EXCHANGES = _namespace["QUEUES_TO_EXCHANGES"]
        QUEUES_TO_TASKS = _namespace["QUEUES_TO_TASKS"]

        # Config dicts in the target class must have same length.
        if not len(EXCHANGES) == len(set(QUEUES_TO_EXCHANGES.values())):
            raise RouterConfigError("inconsistent exchange count")

        if not len(QUEUES_TO_EXCHANGES) == len(QUEUES_TO_TASKS):
            raise RouterConfigError("inconsistent queue count")

        if set(EXCHANGES.keys()) != set(QUEUES_TO_EXCHANGES.values()):
            raise RouterConfigError("inconsistent exchange name")

        if set(QUEUES_TO_EXCHANGES.keys()) != set(QUEUES_TO_TASKS.keys()):
            raise RouterConfigError("inconsistent queue name")

        # Inject the route method into the target class.
        def route(_, task_name):
            # Self is omitted here to save attribute search for efficiency gain.
            for (queue, exchange), tasks in zip(
                QUEUES_TO_EXCHANGES.items(), QUEUES_TO_TASKS.values()
            ):

                for task in tasks:
                    if task_name == task:
                        ex_cnf = EXCHANGES.get(exchange)
                        if isinstance(ex_cnf, dict):
                            ex_cnf["exchange"] = exchange
                            ex_cnf["routing_key"] = f"{exchange}.{queue}"
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
            "exchange_type": "direct",
        },
        "beta": {
            "exchange_type": "direct",
        },
    }

    QUEUES_TO_EXCHANGES = {
        "default": "alpha",
        "another_0": "beta",
        "another_1": "beta",
        "another_2": "beta",
    }

    QUEUES_TO_TASKS = {
        "default": ("calc.pkg_1.tasks.add",),
        "another_0": ("calc.pkg_1.tasks.sub",),
        "another_1": ("calc.pkg_2.tasks.mul",),
        "another_2": ("calc.pkg_2.tasks.div",),
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


# For development: You can use this to run the tasks instantly, without workers.
# app.conf.update(TASK_ALWAYS_EAGER=True)

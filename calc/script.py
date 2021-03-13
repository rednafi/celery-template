class RouteMeta(type):
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
        allowed_attrs = ("EXCHANGES", "EXCHANGES_TO_QUEUES", "QUEUES_TO_TASKS")

        # Filtering out the dunder methods so that we're dealing with only the
        # user-defined attributes
        _namespace = {}
        for attr_name, attr_value in namespace.items():
            if not metacls._is_dunder(attr_name):
                _namespace[attr_name] = attr_value

        for attr_name, attr_value in _namespace.items():
            if not attr_name in allowed_attrs:
                raise Exception(
                    f"{cls} can only contain an attribute in {allowed_attrs}"
                )

            if not isinstance(attr_value, dict):
                raise Exception(f"{attr_name} should be a dict")

            if not attr_value:
                raise Exception(f"{attr_name} cannot be an empty dict")

            if attr_name == "EXCHANGES":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise Exception(f"{attr_name} keys have to be strings")

                    if not isinstance(v, dict):
                        raise Exception(f"{attr_name} format is incorrect")

                    if tuple(v.keys()) != ("exchange", "exchange_type", "routing_key"):
                        raise Exception(f"{attr_name} format is incorrect")

            if attr_name == "EXCHANGES_TO_QUEUES":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise Exception(f"{attr_name} keys have to be strings")

                    if not isinstance(v, str):
                        raise Exception(f"{attr_name} values have to be strings")

            if attr_name == "QUEUES_TO_TASKS":
                for k, v in attr_value.items():
                    if not isinstance(k, str):
                        raise Exception(f"{attr_name} keys have to be strings")

                    if not isinstance(v, (tuple, list)):
                        raise Exception(f"{attr_name} format is incorrect")

        # Making sure that the configuration in the target class is consistent
        for (e1, _), (e2, q1), (q2, _) in zip(
            namespace["EXCHANGES"].items(),
            namespace["EXCHANGES_TO_QUEUES"].items(),
            namespace["QUEUES_TO_TASKS"].items(),
        ):
            if e1 != e2:
                raise Exception("inconsistent exchange name")

            if q1 != q2:
                raise Exception("inconsistent queue name")

        # Inject the route method into the target class
        def route(self, task_name):
            for (exchange, _), (_, tasks) in zip(
                self.EXCHANGES_TO_QUEUES.items(), self.QUEUES_TO_TASKS.items()
            ):
                for task in tasks:
                    if task_name == task:
                        return self.EXCHANGES[exchange]
                    else:
                        raise Exception(f"{task_name} not found")

        namespace["route"] = route

        return super().__new__(metacls, cls, bases, namespace)


class TaskRouter(metaclass=RouteMeta):

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
            "calc.pkg_1.tasks.add",
            "calc.pkg_1.tasks.sub",
        ),
        "another": (
            "calc.pkg_2.tasks.mul",
            "calc.pkg_2.tasks.div",
        ),
    }


tr = TaskRouter()

print("\n", tr.route("calc.pkg_1.tasks.add"))

from celery import chain

from calc.pkg_1 import tasks


def add_sub(a, b):
    """Sequentially executes the add and sub tasks."""

    task_chain = chain(
        # task 1: add
        tasks.add.si(a, b),
        # task 2: sub [ dependent on the success of task 1]
        tasks.sub.si(a, b),
    )

    # Execute task chain in default queue
    result = task_chain.apply_async()
    print(result.get())

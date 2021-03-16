from celery import chain

from calc.pkg_2 import tasks


def mul_div(a, b):
    """Sequentially executes the mul and div tasks."""

    task_chain = chain(
        # task 1: mul
        tasks.mul.si(a, b),
        # task 2: div [ dependent on the success of task 1]
        tasks.div.si(a, b),
    )

    # Execute task chain in default queue
    result = task_chain.apply_async()
    print(result.get())

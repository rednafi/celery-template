import time
from random import randint

from celery import chain, group

from app.io import tasks as io_tasks
from app.proc import tasks as proc_tasks


def add_sub(a, b):
    """Sequentially executes the add and sub tasks."""

    task_chain = chain(
        # task 1: add
        proc_tasks.add.si(a, b),
        # task 2: sub [ dependent on the success of task 1]
        proc_tasks.sub.si(a, b),
    )

    # Execute task chain in default queue
    result = task_chain.apply_async()
    print(result.get())


def mul_div(a, b):
    """Sequentially executes the mul and div tasks."""

    task_chain = chain(
        # task 1: mul
        proc_tasks.mul.si(a, b),
        # task 2: div [ dependent on the success of task 1]
        proc_tasks.div.si(a, b),
    )

    # Execute task chain in default queue
    result = task_chain.apply_async()
    print(result.get())


def get_post_put_delete(
    get_url,
    post_url,
    post_payload,
    put_url,
    put_payload,
    delete_url,
    delete_params,
):
    """Parallelly executes the get_data, post_data, put_data and delete_data tasks."""

    task_group = group(
        io_tasks.get_data.si(get_url),
        io_tasks.post_data.si(post_url, post_payload),
        io_tasks.put_data.si(put_url, put_payload),
        io_tasks.delete_data.si(delete_url, delete_params),
    )

    result = task_group.apply_async()
    print(result.get())


while True:

    res_1 = add_sub(randint(1, 100), randint(101, 200))
    time.sleep(1)

    res_2 = mul_div(randint(1000, 2000), randint(3000, 4000))
    time.sleep(1)

    get_url = "https://httpbin.org/get"
    post_url = "https://httpbin.org/post"
    post_payload = {"first_name": "Red", "last_name": "Nafi"}
    put_url = "https://httpbin.org/put"
    put_payload = {"age": 26, "height": "179 cm"}
    delete_url = "https://httpbin.org/delete"
    delete_params = {"key1": "value1", "key2": "value2"}

    res_3 = get_post_put_delete(
        get_url,
        post_url,
        post_payload,
        put_url,
        put_payload,
        delete_url,
        delete_params,
    )
    time.sleep(1)

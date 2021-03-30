<div align="center">
   <h1>Celery Template</h1>
</div>


![celery_template](https://user-images.githubusercontent.com/30027932/112998087-843eef80-918f-11eb-9415-7dd3ad1211fa.png)



## Description

This template demonstrates a workflow for asynchronous task execution using Python's [Celery](https://docs.celeryproject.org/en/stable/) framework. It uses [Rabbitmq](https://www.rabbitmq.com/) as the broker and result backend.

The template primarily focuses on—

* Explicit **task routing** that conforms to [AMQP](https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol).

* Dynamic configuration to register tasks


### Task Organization

```
app                     # Application root
├── io/                 # Package containing I/O bound tasks
│   ├── __init__.py
│   └── tasks.py        # Module containing Celery tasks
├── proc/               # Package containing CPU bound tasks
│   ├── __init.__.py
│   └── tasks.py        # Module containing Celery tasks
├── __init__.py
├── settings.py         # Setting module that assimilates .env vars
├── celery.py           # Celery config
└── main.py             # Primary task entrypoint

2 directories, 8 files
```

* The root directory `app` houses two packages containing the Celery tasks. The first package `io` contains all the I/O bound tasks while the second package `proc` has all the CPU bound tasks. We define the async tasks in the `tasks.py` modules of the respective folders.

* Module `io/tasks.py` holds 4 I/O bound tasks—`data_get()`, `data_post()`, `data_put()`, and `data_delete()` that performs HTTP **GET**, **POST**, **PUT**, and **DELETE** actions respectively to incur I/O bound load.

* Similarly, module `proc/tasks.py` holds 4 CPU bound tasks—`add()`, `sub()`, `mul()`, and `div()` that performs **addition**, **subtraction**, **multiplication** and **division** actions respectively to incur CPU bound load.

* In the `settings.py` file, we collect the environment variables and consolidate them in a way that they can be easily accessible from the celery config and the task modules.

* Module `celery.py` is where the AMQP exchanges, queues, and task routing logic are defined.

* We call the async tasks in the `main.py` file where the tasks are continuously called with 1-second intervals between each incurrence.

### Task Routing and Load Distribution

In the module `celery.py`, we define two exchanges—**alpha** and **beta**. The producer `main.py` calls the async tasks and publishes the messages to the exchanges. Exchange **alpha** is bound to the **default** queue and exchange **beta** is bound to **another_1**, **another_2**, and **another_3** queues. This implies that any message written to exchange **alpha** will directly go to the **default** queue while messages that are written to exchange **beta** will go to any of the **another_1**, **another_2** or **another_3** queues—depending on their respective routing keys.

CPU bound tasks `proc.tasks.add` and `proc.tasks.sub` are chained together—which means, they will execute sequentially one after another. Task `proc.tasks.mul` and task `proc.tasks.div` are also chained similarly. On the contrary, all the I/O bound tasks execute concurrently without any dependencies between them.

All the CPU-bound tasks run on a Fork pool-based worker named **celery1** that is bound to **default**, **another_1**, and **another_2** queues. The I/O bound tasks run on a Gevent based worker named **celery2**.

## Installation

* Make sure you've **docker** and **docker-compose** installed on your system.
* Clone this repo and head over to the project's root folder.
* Create a virtual environment and run:
    ```
    pip install -r requirements.txt
    ```

## Run

### On Linux

If you're running a Debian-based distro and Gnome terminal, then you're in luck.

* Open a terminal and `cd` to **celery-template** folder
* Make sure your virtual environment is active
* Run:

    ```
    make run_app
    ```

## On Mac or If you're not using Gnome Terminal

* Run the following commands in different terminal windows sequentially:

    * Start a worker process named `celery_1` and register the `default` queue to that:

        ```bash
        celery -A app worker -Q default,another_1 -l INFO -n celery1@%h --concurrency=2
        ```

    * Start another worker process named `celery_2` and register `another_1`, `another_2`, and `another_3` queues to the `celery2` worker:

        ```bash
        celery -A app --pool=gevent worker -Q another_2 -l INFO -n celery_2@%h --concurrency=2
        ```

    * Start the task monitoring tool:

        ```bash
        celery flower -A calc --address=127.0.0.1 --port=5555
        ```

    * Start the application:

        ```bash
        python -m calc.main
        ```

## Monitoring

* To monitor the broker you can go to `http://localhost:15672` on your browser.
* You can also monitor your tasks using **celery-flower** by going to `http://localhost:5555`.

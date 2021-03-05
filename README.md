# Celery Template

## Description

This template demonstrates a workflow for asynchronous task execution using Python's [Celery](https://docs.celeryproject.org/en/stable/) framework. It uses [Rabbitmq](https://www.rabbitmq.com/) as the broker and result backend.

The template primarily focuses on **task routing** that conforms to [AMQP](https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol)—and basic **task chaining** where tasks can be dependent on other tasks and need to be executed in order.


## Organization

```
calc                    # Application root
├── __init__.py         # Celery app instance is imported here
├── celery.py           # Celery configs live here
├── main.py             # Chained tasks are called from here
├── pkg_1
│   ├── __init.__.py
│   ├── tasks.py        # Async task `add` and `sub` are defined here
│   └── chains.py       # Task `add` and `sub` are chained here
├── pkg_2
│   ├── __init__.py
│   ├── tasks.py        # Async task `mul` and `div` are defined here
│   └── chains.py       # Tasks `mul` and `div` are chained here
└── settings.py

2 directories, 10 files
```

Here, the main application's name is **calc** that works in the following way:

* The app supports 4 methods:
    * addition: `calc.pkg_1.tasks.add`
    * subtraction: `calc.pkg_1.tasks.sub`
    * multiplication: `calc.pkg_2.tasks.mul`
    * division: `calc.pkg_2.tasks.div`

* Task `add` and `sub` are chained together in `calc.pkg_1.chains.add_sub` function and task `mul` and `div` are chained together in `calc.pkg_2.chains.mul_div` function.

* The `add_sub` task is executed using Celery's `default` queue and the `mul_div` task is executed in the `q1` queue.

* Tasks are logged via a custom logger and they are explicitly routed in the `celery.py` file.

## Installation

* Make sure you've **docker** and **docker-compose** installed on your system.
* Clone this repo and head over to the project's root folder.
* Create a virtual environment and run:
    ```
    pip install -r requirements.txt
    ```

## Run

### On Linux

If you're running a Debian based distro and Gnome terminal, then you're in luck.

* Open a terminal and `cd` to **celery-template** folder
* Make sure your virtual environment is active
* Run:

    ```
    make run_app
    ```

## On Mac or If you're not using Gnome Terminal

* Run the following commands in different terminal windows sequentially:

    * Spawn the **default** queue and assign it to the **alpha** worker:

        ```bash
        celery -A calc worker -Q default -n alpha --loglevel=INFO --concurrency=1
        ```

    * Spawn the **another** queue and assign it to the **beta** worker:

        ```bash
        celery -A calc worker -Q another -n beta --loglevel=INFO --concurrency=1
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

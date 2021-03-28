<div align="center">
   <h1>Celery Template</h1>
</div>



![MQ Diagram](https://user-images.githubusercontent.com/30027932/111075718-88260d00-8513-11eb-985e-d2bbae3a048d.png)


## Description

This template demonstrates a workflow for asynchronous task execution using Python's [Celery](https://docs.celeryproject.org/en/stable/) framework. It uses [Rabbitmq](https://www.rabbitmq.com/) as the broker and result backend.

The template primarily focuses on—

* Explicit **task routing** that conforms to [AMQP](https://en.wikipedia.org/wiki/Advanced_Message_Queuing_Protocol).

* Dynamic configuration to register tasks


## Organization

```
app                     # Application root
├── io/                 # Package containing I/O oriented tasks
│   ├── __init__.py
│   └── tasks.py        # Module containing Celery tasks
├── proc/               # Package containing Process oriented tasks
│   ├── __init.__.py
│   └── tasks.py        # Module containing Celery tasks
├── __init__.py
├── settings.py         # Setting module that assimilates .env vars
├── celery.py           # Celery config
└── main.py             # Primary task entrypoint

2 directories, 8 files
```

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
        celery -A app worker -Q default -l INFO -n celery1@%h --concurrency=1
        ```

    * Start another worker process named `celery_2` and register `another_1`, `another_2` and `another_3` queues to the `celery2` worker:

        ```bash
        celery -A app worker -Q another_1,another_2,another_3 -l INFO -n \
        celery2@%h --concurrency=1
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

#!/bin/bash

# Run the rabbitmq server.
docker-compose up -d

# Spawn the default queue
q_default="celery -A calc worker -Q default -n alpha --loglevel=INFO --concurrency=1"

# Spawn q1
q_another="celery -A calc worker -Q another -n beta --loglevel=INFO --concurrency=1"

# Spawn flower
flower="celery flower -A calc --address=127.0.0.1 --port=5555"

# Run main task
calc="python -m calc.main"

# Start all project's runners
# the ;SHELL command keeps and holds the tabs open
gnome-terminal --tab --title="Q-Default" -- bash -ic "$q_default;$SHELL"

gnome-terminal --tab --title="Q-Another" -- bash -ic "$q_another;$SHELL"

until timeout 10s celery -A calc inspect ping; do
>&2 echo "Celery workers not available"
done

echo 'Starting flower'
gnome-terminal --tab --title="Flower" -- bash -ic "$flower;$SHELL"

gnome-terminal --tab --title="Calc" -- bash -ic "$calc;$SHELL"

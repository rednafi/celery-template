#!/bin/bash

# Run the rabbitmq server.
docker-compose up -d

# Spawn the alpha worker
a_worker="celery -A calc worker -Q default -l INFO -n alpha@%h --concurrency=1"

# Spawn the beta worker
b_worker="celery -A calc worker -Q another_0,another_1,another_2 \
-l INFO -n beta@%h --concurrency=1"

# Spawn flower
flower="celery flower -A calc --address=127.0.0.1 --port=5555"

# Run main app
calc="python -m calc.main"

# Start all project's runners
# the ;SHELL command keeps and holds the tabs open
gnome-terminal --tab --title="Q-Default" -- bash -ic "$a_worker;$SHELL"

gnome-terminal --tab --title="Q-Another_0 Another_1 Another_2" -- bash -ic "$b_worker;$SHELL"

until timeout 10s celery -A calc inspect ping; do
>&2 echo "Celery workers not available"
done

echo 'Starting flower'
gnome-terminal --tab --title="Flower" -- bash -ic "$flower;$SHELL"

gnome-terminal --tab --title="Calc" -- bash -ic "$calc;$SHELL"

#!/bin/bash

# Run the rabbitmq server.
docker-compose up -d

# Spawn the alpha worker
a_worker="celery -A app worker -Q default -l INFO -n celery1@%h --concurrency=1"

# Spawn the beta worker
b_worker="celery -A app worker -Q another_1,another_2,another_3 \
-l INFO -n celery2@%h --concurrency=1"

# Spawn flower
flower="celery flower -A app --address=127.0.0.1 --port=5555"

# Run main app
app="python -m app.main"

# Start all project's runners
# the ;SHELL command keeps and holds the tabs open
gnome-terminal --tab --title="Q-Default" -- bash -ic "$a_worker;$SHELL"

gnome-terminal --tab --title="Q-Another_1 Another_2 Another_3" -- bash -ic "$b_worker;$SHELL"

until timeout 10s celery -A app inspect ping; do
>&2 echo "Celery workers not available"
done

echo 'Starting flower'
gnome-terminal --tab --title="Flower" -- bash -ic "$flower;$SHELL"

gnome-terminal --tab --title="App" -- bash -ic "$app;$SHELL"

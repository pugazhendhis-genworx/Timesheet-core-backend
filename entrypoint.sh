#!/bin/sh

echo "Starting Celery in background..."
celery "$@" &

echo "Starting health server on port 8080..."
python -m http.server 8080
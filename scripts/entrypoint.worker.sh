#!/bin/bash

celery -A worker.router worker -Q "${WORKER_NAME}" --loglevel=info --pool=eventlet --concurrency=5 -E --logfile=logs/celery.log

tail -f /dev/null

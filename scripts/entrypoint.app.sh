#!/bin/bash

uvicorn app.main:app --host "${BASE_HOST}" --port "${BASE_PORT}" &

python scripts/create_super_user.py

wait

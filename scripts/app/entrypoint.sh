#!/bin/bash

uvicorn app.main:app --host "${BASE_HOST}" --port "${BASE_PORT}" &

python scripts/create_super_user.py

python scripts/add_llm.py

wait

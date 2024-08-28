#!/bin/bash

python3 /app/scripts/config.py

python3 -m llama_cpp.server --config_file /app/scripts/config.json

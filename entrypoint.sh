#!/bin/bash

if [ -z "$CONFIG_LOCATION" ]; then
    CONFIG_LOCATION="/data/config.json"
fi

python -m src -f "${CONFIG_LOCATION}" -m "db"
python -m src -f "${CONFIG_LOCATION}" -m "full"

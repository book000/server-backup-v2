#!/bin/sh

if [ -z "${CONFIG_LOCATION}" ]; then
    CONFIG_LOCATION="/data/config.json"
fi

status=0
python -m src -f "${CONFIG_LOCATION}" -m "db" || status=$?
python -m src -f "${CONFIG_LOCATION}" -m "full" || {
    full_status=$?
    if [ "${status}" -eq 0 ]; then
        status=${full_status}
    fi
}
exit "${status}"

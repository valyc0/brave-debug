#!/bin/bash
set -ex
MAXIMIZED=""
if [ "${START_MAXIMIZED}" == "true" ] ; then
    MAXIMIZED="--start-maximized"
fi

ARGS=""
if [ -n "${CHROME_ARGS}" ]; then
    ARGS="${CHROME_ARGS}"
fi

if [ -n "${LAUNCH_URL}" ]; then
    URL="${LAUNCH_URL}"
else
    URL=""
fi

# Enable remote debugging for Brave browser
exec /usr/bin/brave-browser \
    ${URL} \
    --no-sandbox \
    --disable-dev-shm-usage \
    --remote-debugging-address=${REMOTE_DEBUGGING_ADDRESS} \
    --remote-debugging-port=${REMOTE_DEBUGGING_PORT} \
    ${MAXIMIZED} \
    ${ARGS}

#!/bin/bash

# Stop and remove any existing brave-debug containers
docker stop brave-debug 2>/dev/null
docker rm brave-debug 2>/dev/null

# Start the brave-debug container with authentication disabled and network=host
docker run -d --name brave-debug \
  --network=host \
  --shm-size=512m \
  -e KASM_PORT=6901 \
  -e VNC_PW=password \
  -e KASM_VNC_PW=password \
  -e DISABLE_AUTHENTICATION=1 \
  -e ENABLE_REMOTE_DEBUGGING=true \
  -e REMOTE_DEBUGGING_PORT=9222 \
  -e REMOTE_DEBUGGING_ADDRESS=0.0.0.0 \
  -e CHROME_ARGS="--no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222" \
  brave-debug

echo "Container brave-debug started with network=host."
echo "Access via: http://localhost:6901"
echo "Remote debugging available at: http://localhost:9222/json"
echo ""
echo "NOTE: If you have connection issues, verify that no local services are using the same ports."
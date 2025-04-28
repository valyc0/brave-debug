#!/bin/bash

echo "Creating directory structure for Brave debug container..."
mkdir -p brave-install-scripts

# Check if the original Kasm Brave install scripts exist
if [ -d "/workspace/db-ready/workspaces-images/src/ubuntu/install/brave" ]; then
  echo "Copying Brave installation scripts..."
  cp -r /workspace/db-ready/workspaces-images/src/ubuntu/install/brave/* brave-install-scripts/
else
  echo "WARNING: Original Brave installation scripts not found."
  echo "Creating minimal installation script..."
  cat > brave-install-scripts/install_brave.sh << 'EOF'
#!/bin/bash
set -ex

apt-get update
apt-get install -y curl gnupg

# Add Brave browser repository
curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64] https://brave-browser-apt-release.s3.brave.com/ stable main" | tee /etc/apt/sources.list.d/brave-browser-release.list

# Install Brave browser
apt-get update
apt-get install -y brave-browser

# Create default browser profile
mkdir -p $HOME/.config/brave
EOF
  chmod +x brave-install-scripts/install_brave.sh
fi

# Create custom startup script for Brave with debugging
cat > custom_startup.sh << 'EOF'
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
EOF
chmod +x custom_startup.sh

echo "Building Brave debug container..."
docker build -t brave-debug .

echo "Build complete! You can now run the container using ./start-brave-debug.sh"
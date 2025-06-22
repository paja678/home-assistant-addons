#!/usr/bin/env bash

# Read configuration from Home Assistant
CONFIG_PATH="/data/options.json"

if [ -f "$CONFIG_PATH" ]; then
    # Parse JSON config using jq (available in HA base images)
    TCP_PORT=$(jq -r '.tcp_port // 3030' "$CONFIG_PATH")
    WEB_PORT=$(jq -r '.web_port // 3031' "$CONFIG_PATH")
else
    # Fallback for development/testing
    TCP_PORT=${TCP_PORT:-3030}
    WEB_PORT=${WEB_PORT:-3031}
fi

echo "Starting Teltonika Server with TCP port: $TCP_PORT, Web port: $WEB_PORT"
python3 main.py --tcp-port "$TCP_PORT" --web-port "$WEB_PORT"

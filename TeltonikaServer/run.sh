#!/usr/bin/env bash

# Read configuration from Home Assistant
CONFIG_PATH="/data/options.json"

# Function to parse JSON using Python fallback
parse_config() {
    local key=$1
    local default=$2
    local config_file=$3
    
    if command -v jq >/dev/null 2>&1; then
        # Use jq if available
        jq -r ".$key // $default" "$config_file"
    else
        # Python fallback
        python3 -c "
import json, sys
try:
    with open('$config_file', 'r') as f:
        config = json.load(f)
    print(config.get('$key', $default))
except:
    print($default)
"
    fi
}

if [ -f "$CONFIG_PATH" ]; then
    # Parse JSON config
    TCP_PORT=$(parse_config "tcp_port" 3030 "$CONFIG_PATH")
    WEB_PORT=$(parse_config "web_port" 3031 "$CONFIG_PATH")
else
    # Fallback for development/testing
    TCP_PORT=${TCP_PORT:-3030}
    WEB_PORT=${WEB_PORT:-3031}
fi

echo "Starting Teltonika Server with TCP port: $TCP_PORT, Web port: $WEB_PORT"
python3 main.py --tcp-port "$TCP_PORT" --web-port "$WEB_PORT"

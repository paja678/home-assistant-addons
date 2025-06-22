#!/usr/bin/env bash

# Read configuration from Home Assistant
CONFIG_PATH="${CONFIG_PATH:-/data/options.json}"

if [ -f "$CONFIG_PATH" ]; then
    echo "Reading config from $CONFIG_PATH"
    
    # Try jq first, then Python fallback
    if command -v jq >/dev/null 2>&1; then
        echo "Using jq for JSON parsing"
        TCP_PORT=$(jq -r '.tcp_port // 3030' "$CONFIG_PATH")
        WEB_PORT=$(jq -r '.web_port // 3031' "$CONFIG_PATH")
    else
        echo "Using Python fallback for JSON parsing"
        # Create a temporary Python script for parsing
        cat > /tmp/parse_config.py << 'EOF'
import json
import sys

try:
    with open(sys.argv[1], 'r') as f:
        config = json.load(f)
    tcp_port = config.get('tcp_port', 3030)
    web_port = config.get('web_port', 3031)
    print(f"{tcp_port} {web_port}")
except Exception as e:
    print("3030 3031")
EOF
        
        # Parse config and read both values
        PORTS=$(python3 /tmp/parse_config.py "$CONFIG_PATH")
        TCP_PORT=$(echo $PORTS | cut -d' ' -f1)
        WEB_PORT=$(echo $PORTS | cut -d' ' -f2)
        rm -f /tmp/parse_config.py
    fi
else
    echo "Config file not found, using environment variables or defaults"
    TCP_PORT=${TCP_PORT:-3030}
    WEB_PORT=${WEB_PORT:-3031}
fi

echo "Starting Teltonika Server with TCP port: $TCP_PORT, Web port: $WEB_PORT"
python3 main.py --tcp-port "$TCP_PORT" --web-port "$WEB_PORT"

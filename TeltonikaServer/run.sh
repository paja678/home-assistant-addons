#!/usr/bin/with-contenv bashio

# Set default config path
CONFIG_PATH="${CONFIG_PATH:-/data/options.json}"

echo "=== Teltonika Server Startup ==="
echo "Config path: $CONFIG_PATH"
echo "Working directory: $(pwd)"
echo "Available files: $(ls -la)"

# Initialize variables with defaults
TCP_PORT=3030
WEB_PORT=3031

# Try to read configuration
if [ -f "$CONFIG_PATH" ]; then
    echo "Config file found, attempting to parse..."
    
    # Try jq first (should be available in HA base images)
    if command -v jq >/dev/null 2>&1; then
        echo "Using jq for JSON parsing"
        TCP_PORT=$(jq -r '.tcp_port // 3030' "$CONFIG_PATH" 2>/dev/null || echo "3030")
        WEB_PORT=$(jq -r '.web_port // 3031' "$CONFIG_PATH" 2>/dev/null || echo "3031")
    else
        echo "jq not available, trying Python parsing..."
        # Simple Python one-liner approach
        TCP_PORT=$(python3 -c "
import json
try:
    with open('$CONFIG_PATH') as f:
        config = json.load(f)
    print(config.get('tcp_port', 3030))
except:
    print(3030)
" 2>/dev/null || echo "3030")
        
        WEB_PORT=$(python3 -c "
import json
try:
    with open('$CONFIG_PATH') as f:
        config = json.load(f)
    print(config.get('web_port', 3031))
except:
    print(3031)
" 2>/dev/null || echo "3031")
    fi
    
    echo "Parsed config - TCP: $TCP_PORT, Web: $WEB_PORT"
else
    echo "Config file not found at $CONFIG_PATH"
    echo "Using environment variables or defaults"
    TCP_PORT=${TCP_PORT:-3030}
    WEB_PORT=${WEB_PORT:-3031}
fi

# Validate ports are numeric
if ! [[ "$TCP_PORT" =~ ^[0-9]+$ ]]; then
    echo "Warning: TCP_PORT '$TCP_PORT' is not numeric, using default 3030"
    TCP_PORT=3030
fi

if ! [[ "$WEB_PORT" =~ ^[0-9]+$ ]]; then
    echo "Warning: WEB_PORT '$WEB_PORT' is not numeric, using default 3031"
    WEB_PORT=3031
fi

echo "=== Starting Teltonika Server ==="
echo "TCP port: $TCP_PORT"
echo "Web port: $WEB_PORT"
echo "================================="

exec python3 main.py --tcp-port "$TCP_PORT" --web-port "$WEB_PORT"

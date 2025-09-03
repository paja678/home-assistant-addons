#!/bin/bash

# Set default config path
CONFIG_PATH="${CONFIG_PATH:-/data/options.json}"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "=== Teltonika Server Startup - $TIMESTAMP ==="

# Initialize variables with defaults
TCP_PORT=3030
WEB_PORT=3031

# Try to read configuration
if [ -f "$CONFIG_PATH" ]; then
    # Try jq first (should be available in HA base images)
    if command -v jq >/dev/null 2>&1; then
        TCP_PORT=$(jq -r '.tcp_port // 3030' "$CONFIG_PATH" 2>/dev/null || echo "3030")
        WEB_PORT=$(jq -r '.web_port // 3031' "$CONFIG_PATH" 2>/dev/null || echo "3031")
    else
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
else
    TCP_PORT=${TCP_PORT:-3030}
    WEB_PORT=${WEB_PORT:-3031}
fi

# Validate ports are numeric
if ! [[ "$TCP_PORT" =~ ^[0-9]+$ ]]; then
    TCP_PORT=3030
fi

if ! [[ "$WEB_PORT" =~ ^[0-9]+$ ]]; then
    WEB_PORT=3031
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
echo "[$TIMESTAMP] Starting Teltonika Server (TCP: $TCP_PORT, Web: $WEB_PORT)"

# Debug info
echo "DEBUG: Python version:"
python3 --version

echo "DEBUG: Current directory:"
pwd

echo "DEBUG: Files in current directory:"
ls -la

echo "DEBUG: Checking if main.py exists:"
if [ -f "main.py" ]; then
    echo "  main.py found"
else
    echo "  main.py NOT found!"
fi

echo "DEBUG: Python path and modules:"
python3 -c "import sys; print('Python path:', sys.path)"

echo "DEBUG: Running import test first..."
python3 -u test_imports.py
TEST_EXIT=$?
echo "DEBUG: Import test exit code: $TEST_EXIT"

if [ $TEST_EXIT -ne 0 ]; then
    echo "ERROR: Import test failed, aborting!"
    exit 1
fi

echo "DEBUG: About to execute Python script..."
echo "Command: python3 -u main.py --tcp-port $TCP_PORT --web-port $WEB_PORT"

# Použij python3 s -u pro unbuffered output
python3 -u main.py --tcp-port "$TCP_PORT" --web-port "$WEB_PORT"

# Zachyť exit code
EXIT_CODE=$?
echo "DEBUG: Python script exited with code: $EXIT_CODE"

if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR: Python script failed!"
    exit $EXIT_CODE
fi

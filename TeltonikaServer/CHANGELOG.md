# Changelog

## 0.3.6

### 🐛 Bug Fixes
- **Directory Access**: Fixed persistent logging by changing from `/config/` to `/share/` directory for better Docker container compatibility
- **Mount Point**: Resolved directory creation issues in Home Assistant add-on environment

## 0.3.5

### 🐛 Bug Fixes  
- **Directory Creation**: Added detailed debug logging for config directory creation
- **Permission Testing**: Added write permission tests for `/config/teltonika_logs/`
- **Timing Fix**: Fixed global variable timing issue in directory creation

## 0.3.4

### 🐛 Bug Fixes
- **Config Directory**: Fixed timing issue where log_to_config was not set before directory creation
- **Multiple Fallbacks**: Added directory creation at multiple points (startup, first log, first IMEI)

## 0.3.3

### 🔧 Improvements
- **Simplified Web Interface**: Removed navigation tabs, showing only logs (IMEI Registry accessible via file system)
- **Cleaner UI**: Streamlined interface focused on log viewing
- **Reduced Complexity**: Removed unnecessary URL routing and navigation elements

## 0.3.2

### 🔧 Improvements
- **Startup Logs**: Cleaned up verbose debugging output in startup script
- **Log Readability**: Reduced unnecessary debug information during add-on startup

## 0.3.1

### 🐛 Bug Fixes
- **Docker Build**: Fixed missing Python modules (teltonika_protocol.py, imei_registry.py) in Docker image
- **Module Import**: Resolved ModuleNotFoundError that prevented add-on startup

## 0.3.0

### 🚀 New Features
- **Proper Teltonika AVL Protocol**: IMEI handshake authentication with correct accept/reject responses
- **Codec8 & Codec8 Extended Support**: Full AVL data parsing with GPS coordinates, speed, altitude, satellites, I/O data
- **IMEI Registry**: Automatic device tracking with connection history and statistics
- **IMEI-Based Security**: Device filtering by IMEI (replaces IP filtering for better mobile device support)
- **Persistent Logging**: Log rotation with timestamps, stored in `/config/teltonika_logs/` (survives add-on updates)
- **Enhanced Web Interface**: Dual-tab interface with Logs and IMEI Registry views
- **Custom Icon Support**: Add-on now displays custom icon in Home Assistant

### 🔧 Improvements
- **Multi-Log Support**: Web interface displays data from all log files
- **Better Protocol Compliance**: Server responses follow Teltonika specifications
- **Real-time Device Monitoring**: Track device activity and connection patterns
- **Professional Log Format**: Human-readable GPS data with IMEI identification

### 🐛 Bug Fixes
- **Web Server Stability**: Fixed BrokenPipeError when clients disconnect unexpectedly
- **Connection Handling**: Improved TCP server reliability for concurrent connections

### ⚠️ Breaking Changes
- **Configuration**: `allowed_ips` parameter changed to `allowed_imeis`
- **Security Model**: Filtering now occurs after IMEI handshake instead of IP-based blocking

## 0.2.8

- Basic updates and improvements

## 0.1.0

- First stable public release

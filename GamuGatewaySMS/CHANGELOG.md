# Changelog

All notable changes to this project will be documented in this file.

## [1.1.3] - 2025-01-19

### Changed
- **Swagger UI on Root** - Moved Swagger UI directly to root path (/) for optimal Ingress compatibility
- **Removed Custom HTML** - Eliminated custom welcome page that was causing conflicts
- **Simplified Routing** - Clean, minimal setup with just Swagger UI and API endpoints

### Fixed
- **Final Ingress Solution** - Swagger UI now works perfectly through Home Assistant "Open Web UI" button

## [1.1.2] - 2025-01-19

### Added
- **Swagger UI Restored** - Re-enabled professional Swagger API documentation at `/docs/` path
- **Improved Navigation** - Added direct link to Swagger API docs from main page

### Changed
- **Better Web UI** - Now combines custom welcome page with full Swagger documentation
- **Swagger Path** - Moved Swagger UI to `/docs/` to avoid Ingress routing conflicts
- **Removed API Prefix** - Simplified routing by removing prefix parameter

### Fixed
- **Best of Both Worlds** - Users get both a friendly welcome page AND professional API documentation

## [1.1.1] - 2025-01-19

### Fixed
- **Web UI Ingress Routing** - Completely fixed the blank page issue when accessing through Home Assistant's "Open Web UI" button
- **Route Priority** - Root route now properly defined before Flask-RESTX initialization to ensure correct handling
- **HTML Response Headers** - Added proper Content-Type headers with UTF-8 charset
- **Removed Conflicting Routes** - Removed catch-all handler that was conflicting with API endpoints

### Changed
- Simplified routing logic by defining root handler early in application initialization
- Removed target="_blank" from internal navigation buttons for better Ingress compatibility
- Consolidated HTML generation into the root route handler

## [1.1.0] - 2025-01-19

### Added
- **SMS Monitoring Toggle** - New configuration option to enable/disable automatic SMS detection  
- **Configurable Check Interval** - Adjust SMS monitoring frequency (30-300 seconds)
- **Enhanced SMS Storage** - SMS messages stored in HA database with full history
- **SMS Sensor Attributes** - Date, Number, Text, Timestamp available as sensor attributes

### Changed
- SMS monitoring is now optional with default enabled
- SMS check interval configurable (default: 60 seconds)
- Improved logging with monitoring status display
- Better error handling for SMS monitoring thread

### Fixed
- SMS monitoring now respects configuration settings
- Proper dependency checking between MQTT and SMS monitoring

## [1.0.9] - 2025-01-19

### Added
- **Automatic SMS Detection** - Background monitoring for incoming SMS messages
- **Real-time SMS Notifications** - New SMS automatically published to MQTT (every 60s check)
- **SMS Monitoring Thread** - Independent background process for SMS detection

### Fixed
- **Ingress Web UI** - Fixed "Open Web UI" button in Home Assistant by moving Swagger to root path
- **Web Interface Access** - Swagger UI now properly accessible via HA Ingress

### Changed
- Swagger UI moved from `/docs/` to `/` for better Ingress compatibility
- SMS monitoring runs every 60 seconds when MQTT is enabled
- Improved SMS detection with proper error handling

## [1.0.8] - 2025-01-19

### Added
- **Initial MQTT State Publishing** - Publish sensor states immediately on startup
- **Retained MQTT Messages** - Values persist across Home Assistant restarts
- **Enhanced MQTT Logging** - Detailed logs when values are published to MQTT
- **Better Web UI Routing** - Improved Flask route handling for Swagger UI

### Fixed
- **MQTT Discovery** - Sensors now appear in HA immediately after add-on startup
- **Web UI Access** - Better routing for Ingress and direct access

### Changed
- MQTT messages now use `retain=True` for persistence
- Improved startup sequence with 2-second MQTT connection wait
- Enhanced logging format for better debugging

## [1.0.7] - 2025-01-19

### Added
- **Custom Icon** - Professional 1024x1024 SMS Gateway icon
- Visual identity for add-on in Home Assistant store

### Fixed
- Icon properly copied to Docker container

## [1.0.6] - 2025-01-19

### Fixed
- **Critical fix**: `mqtt_publisher.py` now properly copied to Docker container
- Resolved `ModuleNotFoundError: No module named 'mqtt_publisher'`

## [1.0.5] - 2025-01-19

### Added
- **MQTT Bridge** - Optional MQTT integration with Home Assistant auto-discovery
- **3 Automatic Sensors**: GSM Signal Strength, Network Info, Last SMS Received
- **Periodic Status Updates** - Every 5 minutes to MQTT
- **Real-time SMS Notifications** - Instant MQTT publish on SMS receipt
- **Multi-language Configuration** - EN/CS translations for MQTT options

### Fixed
- **Root Route Fix** - Fixed "Not Found" error when opening Web UI
- Added redirect from `/` to `/docs/` for better user experience

### Changed
- Enhanced startup messages with MQTT status information
- Improved icon from `mdi:message-text` to `mdi:cellphone-message`

## [1.0.4] - 2025-01-19

### Added
- **Swagger UI Documentation** - Professional API documentation at `/docs/`
- Interactive API testing interface
- Organized endpoints in namespaces (SMS operations vs Status)
- Detailed API models with examples
- Better error handling and validation
- Clean startup messages without Flask warnings

### Changed
- Migrated from Flask-RESTful to Flask-RESTX for Swagger support
- Improved API structure with proper namespacing
- Enhanced logging and professional output messages

## [1.0.3] - 2025-01-19

### Fixed
- Suppressed Flask development server warning
- Added clean, professional startup messages with emojis
- Improved logging configuration

## [1.0.2] - 2025-01-19

### Fixed
- Added privileged access and udev support for GSM modem communication
- Improved device mapping with proper permissions
- Enhanced error reporting with available devices list

## [1.0.1] - 2025-01-19

### Fixed  
- Docker build issues with PEP 668 externally-managed-environment
- Added --break-system-packages flag for pip install
- Fixed Dockerfile warnings

## [1.0.0] - 2025-01-19

### Added
- Initial release of SMS Gammu Gateway Home Assistant Add-on
- REST API for sending and receiving SMS messages
- Support for USB GSM modems with AT commands (SIM800L, Huawei E1750, etc.)
- Basic authentication for SMS endpoints
- Public endpoints for signal strength, network info, and modem reset
- Multi-architecture support (amd64, i386, aarch64, armv7, armhf)
- Home Assistant integration examples
- Configurable device path, PIN, port, and authentication
- Based on pajikos/sms-gammu-gateway with Apache License 2.0
- Tested with SIM800L module

### Features
- Send SMS via POST /sms
- Retrieve all SMS via GET /sms
- Get specific SMS by ID via GET /sms/{id}
- Delete SMS by ID via DELETE /sms/{id}
- Get and delete first SMS via GET /getsms
- Check signal quality via GET /signal
- Get network information via GET /network
- Reset modem via GET /reset
- HTTP Basic Authentication for protected endpoints
- Configurable through Home Assistant UI
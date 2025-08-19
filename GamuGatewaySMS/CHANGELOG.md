# Changelog

All notable changes to this project will be documented in this file.

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
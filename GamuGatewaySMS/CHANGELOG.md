# Changelog

All notable changes to this project will be documented in this file.

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
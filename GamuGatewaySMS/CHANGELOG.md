# Changelog

All notable changes to this project will be documented in this file.

## [1.2.4] - 2025-01-19

### Fixed
- **Critical UI/Backend Sync** - Text fields now properly synchronize between Home Assistant UI and backend state
- **Retained Message Handling** - Both clearing and initialization now use `retain=True` to override cached values
- **State Topic Subscription** - Backend now subscribes to state topics to read current HA values on startup
- **Bidirectional Sync** - Reads HA state on connect AND forces empty state with proper timing

### Changed
- **Enhanced MQTT Sync** - Added subscription to both command and state topics for full synchronization
- **Timing Improvements** - Added delays to ensure proper HA discovery processing before state sync
- **Better Logging** - Clear indicators when fields are synced vs. forced to empty state

### Technical Details
- Subscribe to `/state` topics in addition to `/set` topics
- Use `retain=True` for all state publications to override cached values
- Added proper timing sequence: discovery → wait → force empty → wait → sync

## [1.2.3] - 2025-01-19

### Fixed
- **Text Field Clearing** - Both phone number and message fields now clear reliably after sending
- **Field Validation** - Better handling of empty fields with detailed logging for debugging
- **UI Synchronization** - Improved clearing of both internal state and UI fields

### Changed
- **SMSC Configuration Removed** - No longer needed since REST API logic works without it
- **Enhanced Logging** - SMS logs now show full message text instead of truncated version
- **Better Error Messages** - Field validation shows exact current values for debugging

### Removed
- SMSC Number configuration field (no longer needed)
- SMSC fallback mechanism (simplified to use Location 1 like REST API)

## [1.2.2] - 2025-01-19

### Fixed
- **MQTT/Button SMS Logic** - Now uses same SMSC handling as REST API for consistency
- **SMSC Location Method** - MQTT sending now uses `{'Location': 1}` when no SMSC configured (same as REST API)
- **Simplified SMSC Resolution** - Removed complex fallback that was different from REST API behavior

### Changed
- MQTT Publisher now uses identical SMSC logic as REST API endpoints
- Consistent SMS sending behavior across both REST API and MQTT/Button interfaces
- Simplified logging for SMSC source identification

## [1.2.1] - 2025-01-19

### Added
- **SMSC Configuration** - New optional "SMSC Number" field in addon configuration
- **Smart SMSC Priority** - Uses configured SMSC → SIM SMSC → fallback (in that order)
- **Multi-language Support** - Added SMSC field to both Czech and English translations

### How to fix Code 69 error:
1. Go to addon Configuration
2. Add your operator's SMSC number in "SMSC Number" field:
   - T-Mobile CZ: `+420603052000`
   - Vodafone CZ: `+420724000000`
   - O2 CZ: `+420602909090`
3. Restart addon
4. Try sending SMS again

### Technical Details:
- Added `smsc_number` to config schema and options
- Enhanced SMSC resolution logic in MQTT publisher
- Improved logging for SMSC source identification

## [1.2.0] - 2025-01-19

### Fixed
- **Field Synchronization** - Both phone number and message now clear after sending to prevent confusion
- **SMSC Auto-Detection** - Automatic SMS center number detection with fallback
- **Gammu Error Code 69** - Better handling of SMSC number issues
- **State Consistency** - UI and internal state now always match

### Changed
- **Breaking Change**: Both text fields now clear after SMS send (was keeping phone number)
- **Smart SMSC Handling**: Tries to get SMSC from SIM, falls back to location 1 if failed
- **Better Error Messages**: Added specific error for SMSC configuration issues

### Technical Improvements:
- Added `GetSMSC()` call before sending to resolve Code 69 errors
- Enhanced error handling for SMSC-related failures
- Improved field clearing logic for consistency

## [1.1.9] - 2025-01-19

### Fixed
- **Empty Fields on Startup** - Text fields now start empty instead of showing "unknown"
- **Smart Field Clearing** - Only message text clears after send, phone number stays for convenience
- **Better Error Messages** - User-friendly SMS error messages instead of raw gammu codes
- **Gammu Error Code 27** - Now shows "check SIM card, network signal or device connection"

### Improved User Experience:
- Phone number persists between messages (convenient for multiple messages to same recipient)
- Clear error feedback when SMS fails
- Clean initial state without confusing "unknown" values

### Technical Details:
- Added `_publish_empty_text_fields()` for proper initialization
- Enhanced error handling with specific gammu error code interpretation
- Improved field clearing logic to keep phone number

## [1.1.8] - 2025-01-19

### Added
- **Text Input Fields** - Phone Number and Message Text fields directly in SMS Gateway device
- **Smart Button Functionality** - Send SMS button now uses values from text input fields  
- **Auto-clear Fields** - Text fields automatically clear after successful SMS send
- **Field Validation** - Shows error if trying to send without filling required fields
- **Professional UI** - Complete SMS sending interface in one device

### New User Interface:
```
┌─ SMS Gateway Device ─────────┐
│ 📱 Phone Number: [+420...  ] │
│ 💬 Message Text: [Hello...  ] │  
│ 🔘 [Send SMS]                │
│ 📊 Status: success           │
│ 📊 Signal: 85%               │
│ 🌐 Network: T-Mobile          │
└──────────────────────────────┘
```

### How it works:
1. Fill in Phone Number (e.g., +420123456789)
2. Fill in Message Text (max 160 chars)
3. Click "Send SMS" button  
4. Fields automatically clear after successful send
5. Status shows result (success/error/missing_fields)

### Changed
- Button now sends actual SMS instead of just showing notification
- Enhanced MQTT discovery with text input entities
- Improved error handling and user feedback

## [1.1.7] - 2025-01-19

### Added
- **SMS Send Button** - New button entity in Home Assistant device for easy SMS sending
- **SMS Send Status Sensor** - Shows status of SMS sending operations (success/error/button_pressed)
- **Home Assistant Service** - Native `send_sms` service with phone number and message fields
- **Enhanced MQTT Discovery** - Button and status sensor automatically appear in HA device

### New Features in Home Assistant UI:
- **Button Entity**: "Send SMS" button in device (shows notification when pressed)
- **Status Sensor**: "SMS Send Status" shows last operation result
- **Service Call**: Use `send_sms` service in automations with `number` and `message` fields

### Usage:
```yaml
# In automations or scripts
service: send_sms
data:
  number: "+420123456789"
  message: "Alert: Door opened!"
```

### Changed
- MQTT discovery now creates 5 entities: Signal, Network, Last SMS, Send Status, Send Button
- Enhanced logging for MQTT button interactions

## [1.1.5] - 2025-01-19

### Added
- **MQTT SMS Sending** - Send SMS messages via MQTT topic subscription
- **Command Topic** - Subscribe to `homeassistant/sensor/sms_gateway/send` for SMS commands
- **Status Feedback** - Publish SMS send status to `homeassistant/sensor/sms_gateway/send_status`
- **JSON Command Format** - Simple JSON payload: `{"number": "+420123456789", "text": "Hello!"}`

### Usage
Send SMS via MQTT:
```bash
# Via MQTT Explorer or mosquitto_pub
mosquitto_pub -h localhost -t "homeassistant/sensor/sms_gateway/send" -m '{"number": "+420123456789", "text": "Test from MQTT"}'

# Via Home Assistant automation
service: mqtt.publish
data:
  topic: "homeassistant/sensor/sms_gateway/send"
  payload: '{"number": "+420123456789", "text": "Alert message"}'
```

### Changed
- MQTT Publisher now handles both publishing sensors AND receiving SMS commands
- Gammu machine properly shared between REST API and MQTT functionality

## [1.1.4] - 2025-01-19

### Added
- **Jednoduchá statusová stránka** - Nová přívětivá HTML stránka pro Home Assistant Ingress
- **Externí Swagger odkaz** - Tlačítko pro otevření plné API dokumentace v nové záložce (port 5000)
- **Český interface** - Lokalizované texty pro lepší uživatelský zážitek

### Changed
- **Swagger UI přesunut na /docs/** - Plnohodnotná dokumentace dostupná přes přímý přístup
- **Optimalizované řešení** - Ingress zobrazuje jednoduchý status, Swagger zůstává funkční na portu 5000
- **Lepší design** - Moderní, čistý vzhled statusové stránky

### Fixed
- **Definitivní řešení Web UI** - Kombinace jednoduché stránky pro Ingress + plný Swagger přes port
- **Žádné více prázdné stránky** - Garantovaně funkční rozhraní v obou případech

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
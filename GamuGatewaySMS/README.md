# SMS Gammu Gateway Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

REST API SMS Gateway using python-gammu for USB GSM modems (SIM800L, Huawei, etc.)

## About

This add-on provides a REST API SMS Gateway that interfaces with gammu to send and receive SMS messages through USB GSM modems. It supports standard AT commands, which are used by most USB GSM modems including SIM800L.

Based on the excellent work from [pajikos/sms-gammu-gateway](https://github.com/pajikos/sms-gammu-gateway) (Apache License 2.0).

## Features

- **Send SMS**: Send SMS messages via REST API
- **Receive SMS**: Retrieve SMS messages from SIM/device memory  
- **Signal Monitoring**: Check signal strength and quality
- **Network Info**: Get current network details
- **Modem Reset**: Reset modem functionality
- **Multi-architecture Support**: Works on various Home Assistant installations
- **SIM800L Support**: Tested and working with SIM800L modules

## Prerequisites

- USB GSM modem supporting AT commands (SIM800L, Huawei E1750, etc.)
- Modem must appear as `/dev/ttyUSB*` device in Home Assistant host
- SIM card with SMS capability

## Installation

1. Navigate to your Home Assistant Supervisor
2. Go to Add-on Store  
3. Add this repository URL: `https://github.com/pavelve/home-assistant-addons`
4. Find "SMS Gammu Gateway" in the add-on list
5. Click Install

## Configuration

### Add-on Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `device_path` | `/dev/ttyUSB0` | Path to your GSM modem device |
| `pin` | `""` | SIM card PIN (leave empty if no PIN required) |
| `port` | `5000` | Port for the SMS Gateway API |
| `ssl` | `false` | Enable HTTPS (requires SSL certificates) |
| `username` | `admin` | Username for API authentication |
| `password` | `password` | Password for API authentication |

### Example Configuration

```yaml
device_path: "/dev/ttyUSB0"
pin: "1234"
port: 5000
ssl: false
username: "admin"
password: "your_secure_password"
```

## API Endpoints

### Protected Endpoints (require authentication)

#### Send SMS
```bash
POST /sms
Content-Type: application/json
Authorization: Basic <base64(username:password)>

{
  "text": "Hello, how are you?",
  "number": "+420xxxxxxxxx"
}
```

#### Get All SMS
```bash
GET /sms
Authorization: Basic <base64(username:password)>
```

#### Get Specific SMS
```bash
GET /sms/{id}
Authorization: Basic <base64(username:password)>
```

#### Delete SMS
```bash
DELETE /sms/{id}
Authorization: Basic <base64(username:password)>
```

#### Get and Delete First SMS
```bash
GET /getsms
Authorization: Basic <base64(username:password)>
```

### Public Endpoints

#### Signal Strength
```bash
GET /signal
```

#### Network Information
```bash
GET /network
```

#### Reset Modem
```bash
GET /reset
```

## Home Assistant Integration

### SMS Notification Service

Add to your `configuration.yaml`:

```yaml
notify:
  - name: SMS Gateway
    platform: rest
    resource: http://homeassistant.local:5000/sms
    method: POST_JSON
    authentication: basic
    username: admin
    password: your_password
    target_param_name: number
    message_param_name: text
```

### Signal Strength Sensor

```yaml
sensor:
  - platform: rest
    resource: http://homeassistant.local:5000/signal
    name: GSM Signal Strength
    scan_interval: 30
    value_template: '{{ value_json.SignalPercent }}'
    unit_of_measurement: '%'
```

### Automation Example

```yaml
automation:
  - alias: Send SMS Alert
    trigger:
      platform: state
      entity_id: binary_sensor.door_sensor
      state: 'on'
    action:
      service: notify.sms_gateway
      data:
        message: 'Door opened!'
        target: '+420123456789'
```

## Troubleshooting

### Device Not Found
- Check if your GSM modem is connected and recognized
- Use `lsusb` or `dmesg | grep tty` to find available devices
- Some modems may require `usb-modeswitch` to switch from storage to modem mode

### PIN Issues
- Ensure PIN is correct in configuration
- Leave PIN empty if SIM doesn't require one
- Check SIM card is not locked

### Connection Issues
- Verify device path in configuration matches actual device
- Check if SIM800L has sufficient power supply
- Ensure antenna is connected for SIM800L modules

## Support

For issues and questions, use GitHub Issues in the [repository](https://github.com/pavelve/home-assistant-addons).

## License

Based on [sms-gammu-gateway](https://github.com/pajikos/sms-gammu-gateway) by pajikos, licensed under Apache License 2.0.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
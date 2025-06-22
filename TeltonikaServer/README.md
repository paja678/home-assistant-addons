# Teltonika Server Add-on

![Supports aarch64 Architecture][aarch64-shield]
![Supports amd64 Architecture][amd64-shield]
![Supports armhf Architecture][armhf-shield]
![Supports armv7 Architecture][armv7-shield]
![Supports i386 Architecture][i386-shield]

Server for receiving data from Teltonika GPS devices using AVL protocol and logging to file with web interface.

## Features

- **TCP Server**: Receives AVL data from Teltonika GPS devices
- **Web Interface**: Displays logs in real-time with auto-refresh
- **Configurable Ports**: Independent TCP and web port settings
- **Persistent Logs**: Data stored in `/data/tcp_data.log`
- **Multi-threading**: Supports multiple concurrent connections

## Configuration

### TCP Port
Port for receiving AVL data from Teltonika GPS devices (default: 3030)

### Web Port  
Port for accessing the web interface for log viewing (default: 3031)

## Usage

1. Install the add-on from this repository
2. Configure ports as needed
3. Start the add-on
4. Open the web interface via Ingress or direct access on configured port
5. Configure your Teltonika devices to send data to the TCP port

## Data Access

- **Web Interface**: Available through Home Assistant Ingress
- **Log File**: `/addon_configs/[addon-slug]/tcp_data.log`
- **Log Format**: `[YYYY-MM-DD HH:MM:SS] (IP:port): message`

## Support

For issues and questions, use GitHub Issues in the [repository](https://github.com/pavelve/home-assistant-addons).

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
#!/usr/bin/env python3
"""
Teltonika Server - hlavní entry point
Spouští jak TCP server pro přijím dat, tak webový server pro zobrazování logů
"""

import argparse
import threading
from tcp_server import start_tcp_server, ensure_data_dir
from web_server import start_web_server

def main():
    parser = argparse.ArgumentParser(description='Teltonika Server for HA Addon')
    parser.add_argument('--tcp-port', type=int, default=3030, help='TCP port to listen on')
    parser.add_argument('--web-port', type=int, default=3031, help='Web server port for logs')
    args = parser.parse_args()
    
    # Vytvoř /data složku pokud neexistuje
    ensure_data_dir()
    
    # Spusť TCP server v samostatném threadu
    tcp_thread = threading.Thread(target=start_tcp_server, args=('0.0.0.0', args.tcp_port))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # Spusť web server v hlavním threadu
    try:
        start_web_server(host='0.0.0.0', port=args.web_port)
    except KeyboardInterrupt:
        print("Shutting down all servers...")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Teltonika Server - hlavní entry point
Spouští jak TCP server pro přijím dat, tak webový server pro zobrazování logů
"""

import argparse
import threading
import json
import os

print("DEBUG: Importing tcp_server module...")
try:
    from tcp_server import start_tcp_server, ensure_data_dir
    print("DEBUG: tcp_server imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import tcp_server: {e}")
    raise

print("DEBUG: Importing web_server module...")
try:
    from web_server import start_web_server
    print("DEBUG: web_server imported successfully")
except ImportError as e:
    print(f"ERROR: Failed to import web_server: {e}")
    raise

def load_ha_config():
    """Načte konfiguraci z Home Assistant add-onu"""
    # Pro vývoj použij lokální složku, pro produkci /data
    config_path = '/data/options.json' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data/options.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Chyba při čtení konfigurace HA: {e}")
    return {}

def main():
    parser = argparse.ArgumentParser(description='Teltonika Server for HA Addon')
    parser.add_argument('--tcp-port', type=int, default=3030, help='TCP port to listen on')
    parser.add_argument('--web-port', type=int, default=3031, help='Web server port for logs')
    args = parser.parse_args()
    
    # Načti konfiguraci z HA add-onu
    ha_config = load_ha_config()
    print(f"DEBUG: Loaded HA config: {ha_config}")
    
    # Použij porty z konfigurace pokud jsou dostupné
    tcp_port = ha_config.get('tcp_port', args.tcp_port)
    web_port = ha_config.get('web_port', args.web_port)
    allowed_imeis = ha_config.get('allowed_imeis', [])
    log_to_config = ha_config.get('log_to_config', False)
    
    print(f"DEBUG: log_to_config = {log_to_config}")
    print(f"DEBUG: allowed_imeis = {allowed_imeis}")
    
    # Pokud je seznam prázdný, žádné filtrování
    if not allowed_imeis:
        allowed_imeis = None
    
    # Nastavíme globální proměnnou před voláním ensure_data_dir
    import tcp_server
    print(f"DEBUG: Setting tcp_server.log_to_config to {log_to_config}")
    tcp_server.log_to_config = log_to_config
    print(f"DEBUG: tcp_server.log_to_config is now {tcp_server.log_to_config}")
    
    # Vytvoř složky
    print("DEBUG: Calling ensure_data_dir()...")
    ensure_data_dir()
    print("DEBUG: ensure_data_dir() completed")
    
    # Spusť TCP server v samostatném threadu
    tcp_thread = threading.Thread(target=start_tcp_server, args=('0.0.0.0', tcp_port, allowed_imeis, log_to_config))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    print("✅ TCP server started successfully")
    
    # Spusť web server v hlavním threadu
    print("✅ Starting web server...")
    try:
        start_web_server(host='0.0.0.0', port=web_port)
        print("✅ All servers started successfully and running!")
    except KeyboardInterrupt:
        print("Shutting down all servers...")

if __name__ == "__main__":
    try:
        print("DEBUG: main.py started")
        main()
    except Exception as e:
        print(f"FATAL ERROR in main(): {e}")
        import traceback
        traceback.print_exc()
        exit(1)
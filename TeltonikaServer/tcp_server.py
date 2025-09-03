import socket
import threading
import os
import glob
import binascii
from datetime import datetime
from teltonika_protocol import parse_imei, parse_avl_packet, format_record_for_log
from imei_registry import IMEIRegistry

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
CONFIG_DIR = '/share' if os.path.exists('/share') or os.environ.get('HA_ADDON') else './config'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

# Globální proměnné pro log rotaci a IMEI registry
current_log_file = None
log_to_config = False
imei_registry = None

def ensure_data_dir():
    """Vytvoří data složku pokud neexistuje"""
    print(f"DEBUG: ensure_data_dir() called")
    print(f"DEBUG: DATA_DIR = {DATA_DIR}")
    print(f"DEBUG: CONFIG_DIR = {CONFIG_DIR}")
    print(f"DEBUG: log_to_config = {log_to_config}")
    print(f"DEBUG: HA_ADDON env = {os.environ.get('HA_ADDON')}")
    print(f"DEBUG: /share exists = {os.path.exists('/share')}")
    print(f"DEBUG: /data exists = {os.path.exists('/data')}")
    print(f"DEBUG: /config exists = {os.path.exists('/config')}")
    
    print(f"Creating data directory: {DATA_DIR}")
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"✅ Successfully created/verified: {DATA_DIR}")
    except Exception as e:
        print(f"❌ Failed to create {DATA_DIR}: {e}")
    
    print(f"log_to_config setting: {log_to_config}")
    if log_to_config:
        config_log_dir = os.path.join(CONFIG_DIR, 'teltonika_logs')
        print(f"Attempting to create config log directory: {config_log_dir}")
        try:
            os.makedirs(config_log_dir, exist_ok=True)
            print(f"✅ Successfully created/verified config log dir: {config_log_dir}")
            
            # Test write permissions
            test_file = os.path.join(config_log_dir, 'test_write.tmp')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"✅ Write permissions OK in: {config_log_dir}")
            except Exception as e:
                print(f"❌ Write permission test failed in {config_log_dir}: {e}")
                
        except Exception as e:
            print(f"❌ Failed to create config log directory {config_log_dir}: {e}")
            print(f"   CONFIG_DIR exists: {os.path.exists(CONFIG_DIR)}")
            print(f"   CONFIG_DIR permissions: {oct(os.stat(CONFIG_DIR).st_mode) if os.path.exists(CONFIG_DIR) else 'N/A'}")
    else:
        print("Config logging disabled, using /data/ only")

def get_imei_registry():
    """Vrátí IMEI registry instanci"""
    global imei_registry
    if imei_registry is None:
        registry_dir = os.path.join(CONFIG_DIR, 'teltonika_logs') if log_to_config else DATA_DIR
        # Zajistíme, že složka existuje
        os.makedirs(registry_dir, exist_ok=True)
        registry_path = os.path.join(registry_dir, 'imei_registry.json')
        imei_registry = IMEIRegistry(registry_path)
    return imei_registry

def get_log_file():
    """Vrátí cestu k aktuálnímu log souboru"""
    global current_log_file
    
    if log_to_config:
        # Ukládej do /config/teltonika_logs/ s datem a časem
        if not current_log_file:
            log_dir = os.path.join(CONFIG_DIR, 'teltonika_logs')
            # Zajistíme, že složka existuje
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'teltonika_{timestamp}.log'
            current_log_file = os.path.join(log_dir, filename)
        return current_log_file
    else:
        # Standardní log do /data/
        return LOG_FILE

def get_all_log_files():
    """Vrátí seznam všech log souborů seřazených podle data"""
    if log_to_config:
        log_dir = os.path.join(CONFIG_DIR, 'teltonika_logs')
        if os.path.exists(log_dir):
            pattern = os.path.join(log_dir, 'teltonika_*.log')
            files = glob.glob(pattern)
            return sorted(files, reverse=True)  # Nejnovější první
    
    # Pro standardní log vrať jen aktuální soubor
    if os.path.exists(LOG_FILE):
        return [LOG_FILE]
    return []

def handle_client(client_socket, client_address, allowed_imeis=None):
    """Zpracuje komunikaci s jednotlivým klientem podle Teltonika AVL protokolu"""
    print(f"Teltonika connection from {client_address}")
    client_imei = None
    
    with client_socket:
        while True:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break

                # Log raw data pro debugging
                hex_data = binascii.hexlify(data).decode('utf-8').upper()
                print(f"Raw data from {client_address}: {hex_data}")

                # Pokud ještě nemáme IMEI, pokus se ho parsovat
                if client_imei is None:
                    imei = parse_imei(data)
                    if imei:
                        client_imei = imei
                        client_ip = client_address[0]
                        
                        # Zkontroluj, zda je IMEI povoleno
                        registry = get_imei_registry()
                        if not registry.is_imei_allowed(client_imei, allowed_imeis or []):
                            print(f"IMEI {client_imei} not in allowed list - connection refused")
                            client_socket.sendall(b"\x00")  # Reject
                            break
                        
                        # Zaregistruj IMEI v registru
                        is_new_device = registry.register_imei_connection(client_imei, client_ip)
                        
                        print(f"IMEI authenticated: {client_imei} {'(NEW DEVICE)' if is_new_device else ''}")
                        
                        # Odpověz na IMEI handshake - 0x01 = accept
                        client_socket.sendall(b"\x01")
                        
                        # Zaloguj IMEI
                        try:
                            log_file = get_log_file()
                            with open(log_file, 'a', encoding='utf-8') as f:
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                status = "NEW DEVICE" if is_new_device else "KNOWN DEVICE"
                                f.write(f"[{timestamp}] IMEI: {client_imei} connected from {client_address} ({status})\n")
                        except Exception as e:
                            print(f"Chyba při zápisu IMEI do logu: {e}")
                        
                        continue
                    else:
                        print(f"Invalid IMEI handshake from {client_address}")
                        client_socket.sendall(b"\x00")  # Reject
                        break

                # Parsuj AVL data packet
                records, record_count, codec_type = parse_avl_packet(data)
                
                if records and record_count > 0:
                    print(f"Received {record_count} AVL records ({codec_type}) from IMEI {client_imei}")
                    
                    # Zaregistruj záznamy v IMEI registru
                    if client_imei:
                        registry = get_imei_registry()
                        registry.register_avl_records(client_imei, record_count)
                    
                    # Zaloguj parsed data
                    try:
                        log_file = get_log_file()
                        with open(log_file, 'a', encoding='utf-8') as f:
                            for record in records:
                                log_entry = format_record_for_log(record, client_imei or "unknown")
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                f.write(f"[{timestamp}] {log_entry}\n")
                    except Exception as e:
                        print(f"Chyba při zápisu AVL dat do logu: {e}")
                    
                    # Odpověz s počtem zpracovaných záznamů (4 bytes, big endian)
                    response = record_count.to_bytes(4, 'big')
                    client_socket.sendall(response)
                    print(f"Sent ACK for {record_count} records")
                    
                else:
                    print(f"Failed to parse AVL packet from {client_address}")
                    # Zaloguj raw data pokud parsing selhal
                    try:
                        log_file = get_log_file()
                        with open(log_file, 'a', encoding='utf-8') as f:
                            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            f.write(f"[{timestamp}] RAW DATA from {client_address} (IMEI: {client_imei or 'unknown'}): {hex_data}\n")
                    except Exception as e:
                        print(f"Chyba při zápisu raw dat do logu: {e}")
                    
                    # Odpověz s 0 záznamy
                    client_socket.sendall(b"\x00\x00\x00\x00")
                    
            except Exception as e:
                print(f"Chyba při zpracování dat od {client_address}: {e}")
                break

def start_tcp_server(host='0.0.0.0', port=3030, allowed_imeis=None, config_logging=False):
    """Spustí TCP server pro příjem dat od Teltonika zařízení"""
    global log_to_config
    log_to_config = config_logging
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    
    log_location = "/config/teltonika_logs/" if log_to_config else "/data/"
    if allowed_imeis:
        print(f"TCP server listening on {host}:{port} with IMEI filter: {allowed_imeis}")
        print(f"Logs saved to: {log_location}")
    else:
        print(f"TCP server listening on {host}:{port} (all IMEIs allowed)")
        print(f"Logs saved to: {log_location}")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, allowed_imeis))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("TCP server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    ensure_data_dir()
    start_tcp_server()
import socket
import threading
import os
from datetime import datetime

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

def ensure_data_dir():
    """Vytvoří data složku pokud neexistuje"""
    os.makedirs(DATA_DIR, exist_ok=True)

def handle_client(client_socket, client_address):
    """Zpracuje komunikaci s jednotlivým klientem"""
    print(f"Connection from {client_address}")
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            text = data.decode('utf-8').strip()
            print(f"Received from {client_address}: {text}")

            try:
                with open(LOG_FILE, 'a', encoding='utf-8') as f:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{timestamp}] {client_address}: {text}\n")
            except Exception as e:
                print(f"Chyba při zápisu do logu: {e}")

            client_socket.sendall(b"OK\n")

def start_tcp_server(host='0.0.0.0', port=3030):
    """Spustí TCP server pro příjem dat od Teltonika zařízení"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"TCP server listening on {host}:{port}")

    try:
        while True:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("TCP server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    ensure_data_dir()
    start_tcp_server()
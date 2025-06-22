import socket
import threading
import argparse
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

def ensure_data_dir():
    """Vytvoří data složku pokud neexistuje"""
    os.makedirs(DATA_DIR, exist_ok=True)

class LogHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Zobrazit posledních 100 řádků
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    log_content = ''.join(recent_lines)
            else:
                log_content = "Log soubor zatím neexistuje."
        except Exception as e:
            log_content = f"Chyba při čtení logu: {e}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Teltonika Server Log</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: monospace; margin: 20px; background: #f0f0f0; }}
        .header {{ background: #333; color: white; padding: 10px; margin-bottom: 20px; }}
        .log {{ background: white; padding: 15px; border: 1px solid #ccc; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Teltonika Server Log</h1>
        <p>Automatické obnovení každých 5 sekund | Posledních 100 řádků</p>
        <p>Aktualizováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="log">{log_content}</div>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))

def handle_client(client_socket, client_address):
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

def tcp_server(host='0.0.0.0', port=3030):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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

def web_server(host='0.0.0.0', port=8099):
    """HTTP server pro zobrazování logů"""
    server = HTTPServer((host, port), LogHandler)
    print(f"Web server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Web server shutting down...")
    finally:
        server.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Teltonika Server for HA Addon')
    parser.add_argument('--port', type=int, default=3030, help='TCP port to listen on')
    parser.add_argument('--web-port', type=int, default=8099, help='Web server port for logs')
    args = parser.parse_args()
    
    # Vytvoř /data složku pokud neexistuje
    ensure_data_dir()
    
    # Spusť TCP server v samostatném threadu
    tcp_thread = threading.Thread(target=tcp_server, args=('0.0.0.0', args.port))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # Spusť web server v hlavním threadu
    try:
        web_server(port=args.web_port)
    except KeyboardInterrupt:
        print("Shutting down all servers...")

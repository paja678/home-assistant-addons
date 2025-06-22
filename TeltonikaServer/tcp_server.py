import socket
import threading
import argparse
import os

LOG_FILE = '/data/tcp_data.log'

def handle_client(client_socket, client_address):
    print(f"Connection from {client_address}")
    with client_socket:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break

            text = data.decode('utf-8').strip()
            print(f"Received from {client_address}: {text}")

            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"{client_address}: {text}\n")

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
        print("Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Teltonika Server for HA Addon')
    parser.add_argument('--port', type=int, default=3030, help='TCP port to listen on')
    args = parser.parse_args()
    tcp_server(port=args.port)

#!/usr/bin/env python3
import threading
import time
import socket
import subprocess
from tcp_server import tcp_server, web_server, ensure_data_dir

def test_tcp_client():
    """Test TCP server"""
    time.sleep(2)  # Počkej až se servery spustí
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("127.0.0.1", 3030))
            test_message = "Test data from client"
            s.sendall(test_message.encode('utf-8'))
            response = s.recv(1024)
            print(f"TCP Test: Poslano '{test_message}', odpověď: {response.decode()}")
    except Exception as e:
        print(f"TCP Test chyba: {e}")

def test_web_client():
    """Test web server"""
    time.sleep(3)  # Počkej až se TCP test dokončí
    
    try:
        result = subprocess.run(['curl', '-s', 'http://127.0.0.1:8099'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("Web Test: Server odpovídá správně")
            print("Web obsah obsahuje log data:", "Test data from client" in result.stdout)
        else:
            print(f"Web Test chyba: curl exit code {result.returncode}")
    except Exception as e:
        print(f"Web Test chyba: {e}")

if __name__ == "__main__":
    ensure_data_dir()
    
    # Spusť servery
    tcp_thread = threading.Thread(target=tcp_server, args=('127.0.0.1', 3030))
    tcp_thread.daemon = True
    tcp_thread.start()
    
    web_thread = threading.Thread(target=web_server, args=('127.0.0.1', 8099))
    web_thread.daemon = True
    web_thread.start()
    
    # Spusť testy
    test_tcp_thread = threading.Thread(target=test_tcp_client)
    test_tcp_thread.start()
    
    test_web_thread = threading.Thread(target=test_web_client)
    test_web_thread.start()
    
    # Počkej na dokončení testů
    test_tcp_thread.join()
    test_web_thread.join()
    
    print("Testy dokončeny. Servery běží na pozadí.")
    print("TCP server: http://127.0.0.1:3030")
    print("Web server: http://127.0.0.1:8099")
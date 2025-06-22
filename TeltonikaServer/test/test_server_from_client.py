import socket

imei = b'352094089112345'
data = b'\x00\x00\x00\x00\x00\x00\x00\x00\x01'

payload = len(imei).to_bytes(2, 'big') + imei + data

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("0.0.0.0", 3031))
    s.sendall(payload)
    response = s.recv(16)
    print("ACK:", response.hex())

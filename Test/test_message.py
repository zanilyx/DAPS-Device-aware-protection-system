import socket

TARGET_IP = "10.2.1.170"  # friend's IP
PORT = 5000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    msg = input("> ")
    sock.sendto(msg.encode(), (TARGET_IP, PORT))
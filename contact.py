import socket

# sock = socket()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "1.1.1.1"
UDP_PORT = 53
add = (UDP_IP, UDP_PORT)

packet = b'\x1d\x82\x01 \x00\x01\x00\x00\x00\x00\x00\x01\x06google\x03com\x00\x00\x01\x00\x01\x00\x00)\x04\xd0\x00\x00\x00\x00\x00\x0c\x00\n\x00\x08~b~&\xb1\n\xbb\t'
addr = sock.sendto(packet, (UDP_IP, UDP_PORT))

# addr.recvfrom(1024)

data, addr = sock.recvfrom(1024)
print(f"Received response: {data} from {addr}")

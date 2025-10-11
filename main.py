import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "127.0.0.1"
UDP_PORT = 1234
add = (UDP_IP, UDP_PORT)
sock.bind(add)
print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}")

num = 12
a = num.to_bytes(2,byteorder="big")
print(a)

while True:
        data, addr = sock.recvfrom(1024)
        print(data)

        idd = int.from_bytes(data[0:2], byteorder='big')
        flags = int.from_bytes(data[2:4], byteorder='big')
        QDCOUNT = int.from_bytes(data[4:6], byteorder='big')
        ANCOUNT = int.from_bytes(data[6:8], byteorder='big')
        NSCOUNT = int.from_bytes(data[8:10], byteorder='big')
        ARCOUNT = int.from_bytes(data[10:12], byteorder='big')
        print(f"id :{id} \n flags:{flags} \n QDCOUNT:{QDCOUNT} \n ANCOUNT:{ANCOUNT} \n NSCOUNT:{NSCOUNT} \n ARCOUNT:{ARCOUNT}")

        i = 12
        label = []

        while data[i] != 0:
        	point = data[i]
        	i += 1
        	label.append(data[i:i+point].decode())
        	i = i + point	
        print(label)

        qtype  = int.from_bytes(data[i:i+2], byteorder='big')
        qclass = int.from_bytes(data[i+2:i+4], byteorder='big')

        print("QTYPE:", qtype)
        print("QCLASS:", qclass)

        id_bytes = data[0:2]
        flags = b'\x81\x80'  # standard response, QR=1, AA=1, no error
        qdcount = data[4:6]
        ancount = b'\x00\x01'  # one answer
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'

        header = id_bytes + flags + qdcount + ancount + nscount + arcount

        question_bytes = data[12:i+1+4]

        answer = b'\xc0\x0c'        # pointer to QNAME (offset 12)
        answer += question_bytes[-4:-2]   # QTYPE
        answer += question_bytes[-2:]     # QCLASS
        num = 400
        answer += num.to_bytes(4,byteorder="big")
        answer += (4).to_bytes(2, byteorder="big") # RDLENGTH = 4 bytes       # RDLENGTH = 4 bytes
        ip = "102.112.43.42"
        answer += socket.inet_aton(ip)

        print(header+question_bytes+answer)
        sock.sendto(header+question_bytes+answer,addr)
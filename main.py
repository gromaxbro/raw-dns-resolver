import socket


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "127.0.0.1"
UDP_PORT = 1234
add = (UDP_IP, UDP_PORT)
sock.bind(add)
print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}")

num = 12
i = 12

def read_data(data):
        # Field   Size (bits)     Description
        # ID         16              A unique identifier assigned by the client. Used to match responses to queries.
        # Flags      16              Contains control bits (see below).
        # QDCOUNT    16              Number of entries in the Question section.
        # ANCOUNT    16              Number of resource records in the Answer section.
        # NSCOUNT    16              Number of name server (Authority) records.
        # ARCOUNT    16              Number of additional records

        idd = int.from_bytes(data[0:2], byteorder='big')
        flags = int.from_bytes(data[2:4], byteorder='big')
        QDCOUNT = int.from_bytes(data[4:6], byteorder='big')
        ANCOUNT = int.from_bytes(data[6:8], byteorder='big')
        NSCOUNT = int.from_bytes(data[8:10], byteorder='big')
        ARCOUNT = int.from_bytes(data[10:12], byteorder='big')
        print(f"id :{idd} \n flags:{flags} \n QDCOUNT:{QDCOUNT} \n ANCOUNT:{ANCOUNT} \n NSCOUNT:{NSCOUNT} \n ARCOUNT:{ARCOUNT}")
        return {idd,flags,QDCOUNT,ANCOUNT,NSCOUNT,ARCOUNT}

def read_question(data):
        global i

        # QNAME   The queried domain name, encoded as labels (e.g., www.google.com → 3www6google3com0).
        # QTYPE   Type of record requested (e.g., 1 = A, 28 = AAAA, 15 = MX).
        # QCLASS  Usually 1 for Internet (IN).
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

#         QTYPE   Meaning Notes
# 1       A       IPv4 address
# 28      AAAA    IPv6 address
# 5       CNAME   Canonical name / alias
# 15      MX      Mail exchange server
# 2       NS      Authoritative name server
# 12      PTR     Reverse DNS lookup
# 16      TXT     Arbitrary text
# 33      SRV     Service location (used in SIP, XMPP, etc.)

def make_header(data):
        id_bytes = data[0:2]
        flags = b'\x81\x80'  # standard response, QR=1, AA=1, no error
        qdcount = data[4:6]
        ancount = b'\x00\x01'  # one answer
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'
        header = id_bytes + flags + qdcount + ancount + nscount + arcount
        return header

def make_answer(data):
        question_bytes = data[12:i+1+4]
        answer = b'\xc0\x0c'        # pointer to QNAME (offset 12)
        answer += question_bytes[-4:-2]   # QTYPE
        answer += question_bytes[-2:]     # QCLASS
        num = 400
        answer += num.to_bytes(4,byteorder="big")
        answer += (4).to_bytes(2, byteorder="big") # RDLENGTH = 4 bytes       # RDLENGTH = 4 bytes
        ip = "102.112.43.42"
        answer += socket.inet_aton(ip)

        return question_bytes+answer
while True:
        i = 12
        data, addr = sock.recvfrom(1024)
        print("******************\n",data,"\n***********************")

        read = read_data(data)   
        question = read_question(data)

        header = make_header(data)
        answer = make_answer(data)
        print("******************\n")
        print(f"Answer hex:{header+answer}")
        print("******************\n")
        sock.sendto(header+answer,addr)
import socket
import json
import time


with open("cache.json", "r") as f:
    cache = json.load(f)

def get_cache(cache, domain, qtype):
    records = cache.get(domain, {}).get(qtype, [])
    if records:
        return records
    else:
        return 0
    


def add_cache(cache, domain, qtype, value, ttl=3600):
    current_time = time.time()
    if domain not in cache:
        cache[domain] = {}
    if qtype not in cache[domain]:
        cache[domain][qtype] = []
    cache[domain][qtype].append({"value": value, "ttl": ttl, "timestamp": current_time})

    with open("cache.json", "w") as f:
        json.dump(cache, f, indent=4)

rec = get_cache(cache,"example.com","A")

# add_cache(cache,"google.com","A","34.456.0.138")
# add_cache(cache,"google.com","A","233.220.75.245")


print(cache)


sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "127.0.0.1"
UDP_PORT = 53
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
        types = {1:"A",28:"AAAA",5:"CNAME",15:"MX"}

        qtype  = int.from_bytes(data[i+2:i+3], byteorder='big')
        qclass = int.from_bytes(data[i+3:i+5], byteorder='big')
        print("QTYPE:", qtype)
        print("QCLASS:", qclass)
        ab = ".".join(label)
        print(ab)
        rec = get_cache(cache,ab,types[qtype])
        print(rec)

        return [rec,qtype,qclass]
        # print
        #         QTYPE   Meaning Notes
        # 1       A       IPv4 address
        # 28      AAAA    IPv6 address
        # 5       CNAME   Canonical name / alias
        # 15      MX      Mail exchange server
        # 2       NS      Authoritative name server
        # 12      PTR     Reverse DNS lookup
        # 16      TXT     Arbitrary text
        # 33      SRV     Service location (used in SIP, XMPP, etc.)

def make_header(data,q_len):
        # r = len(rec[0])
        id_bytes = data[0:2]
        flags = b'\x81\x80'  # standard response, QR=1, AA=1, no error
        qdcount = data[4:6]
        # ancount = b'\x00\x01'  # one answer
        ancount = (q_len).to_bytes(2,byteorder="big")
        nscount = b'\x00\x00'
        arcount = b'\x00\x00'
        header = id_bytes + flags + qdcount + ancount + nscount + arcount
        return header

def make_answer(data,rec=0):
        question_bytes = data[12:i+5]
        if rec == 0:
            return question_bytes
        
        answer = b''
        for m in rec[0]:
            answer += b'\xc0\x0c'        # pointer to QNAME (offset 12)
            answer += rec[1].to_bytes(2, byteorder="big")   # QTYPE
            answer += rec[2].to_bytes(2, byteorder="big")     # QCLASS
            num = m["ttl"]
            answer += num.to_bytes(4,byteorder="big") # TTL
            answer += (4).to_bytes(2, byteorder="big") # RDLENGTH = 4 bytes       # RDLENGTH = 4 bytes
            ip = m["value"]
            answer += socket.inet_aton(ip)
        return question_bytes+answer
while True:
        i = 12
        data, addr = sock.recvfrom(1024)
        print("******************\n",data,"\n***********************")

        read = read_data(data)   
        question = read_question(data)
        if question[0] != 0:
            print("got answer")
            header = make_header(data,len(question[0]))
            answer = make_answer(data,question)
        else:
            header = make_header(data,0)
            answer = make_answer(data)

        print("******************\n")
        print(f"Answer hex:{header+answer}")
        print("******************\n")
        sock.sendto(header+answer,addr)
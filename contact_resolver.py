import socket
import random

def make_header(flag,qd,an,ns,ar):
        # r = len(rec[0])
        id_bytes = random.randint(0,32767).to_bytes(2, byteorder="big")
        if flag == 0:
        	flags = b'\x01\x00'
        else:
        	flags = b'\x81\x80'
        qdcount = (qd).to_bytes(2,byteorder="big")
        ancount = (an).to_bytes(2,byteorder="big")
        nscount = (ns).to_bytes(2,byteorder="big")
        arcount = (ar).to_bytes(2,byteorder="big")
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

def qname_creator(text):
	new = text.split(".")
	new.append("") 
	i = 0
	while (i<len(new)):
		new[i] = len(new[i]).to_bytes(1,byteorder="big")+new[i].encode('ascii')
		i = i + 1
	byte_domain = b''.join(new)
	print(byte_domain)
	return byte_domain

def query(text,qtype,qclass=1):
	header = make_header(0,1,0,0,0) 
	question = b''

	byte_domain = qname_creator(text)
	question += byte_domain

	qtp = (qtype).to_bytes(2, 'big')
	question += qtp

	qclass = (1).to_bytes(2, 'big')
	question += qclass

	return header + question

def read_answer(data):
	i = 0
	ans = data[answer_start:]
	val_arr = []

	while (i<len(ans)):
		rtype = int.from_bytes(ans[i+2:i+4], byteorder='big')
		rclass = int.from_bytes(ans[i+4:i+6], byteorder='big')
		rttl = int.from_bytes(ans[i+6:i+10], byteorder='big')
		rdlen = int.from_bytes(ans[i+10:i+12], byteorder='big')

		value = socket.inet_ntoa(ans[i+12:i+12+rdlen])

		val_arr.append((value,rttl))
		print(f"type = {rtype} ,rclass = {rclass} ,rttl = {rttl} ,rdlen={rdlen} ,value={value}")

		i = i + 12 + rdlen

	return val_arr
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP = "1.1.1.1"
UDP_PORT = 53
add = (UDP_IP, UDP_PORT)

domain = 'reddit.com'
packet = query(domain,1)
addr = sock.sendto(packet, (UDP_IP, UDP_PORT))

# addr.recvfrom(1024)

data, addr = sock.recvfrom(1024)
answer_start = 12 + len(qname_creator(domain)) + 2 + 2


print(read_answer(data))

print(f"Received response: {data} from {addr}")

print("***************")
print()







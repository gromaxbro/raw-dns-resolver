import re
import requests
import socket
import random
import time

root_ips = []
nearest_root = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1.0) 


def update_root_address():
	with open("root.hints","r+") as f:
		nm = f.read().splitlines()
		for line in nm:
			if "A " in line and "AAAA" not in line:
				match = re.match(r"([A-Z0-9.-]+)\s+\d+\s+A\s+(\d+\.\d+\.\d+\.\d+)", line, re.IGNORECASE)

				if match:
				    name, ip = match.groups()
				    # print("Name:", name)
				    # print("IP:", ip)
				    root_ips.append((name,ip))
				else:
				    print("[-] no ips found in root file")
				    return -1

		print("[+] root file updated")
		return 0


def make_header(flag,qd,an,ns,ar):
        # r = len(rec[0])
        id_bytes = random.randint(0,32767).to_bytes(2, byteorder="big")
        if flag == 0:
        	flags = b'\x01\x00'
        elif flag == 1:
        	flags = b'\x00\x00'
        else:
        	flags = b'\x81\x80'
        qdcount = (qd).to_bytes(2,byteorder="big")
        ancount = (an).to_bytes(2,byteorder="big")
        nscount = (ns).to_bytes(2,byteorder="big")
        arcount = (ar).to_bytes(2,byteorder="big")
        header = id_bytes + flags + qdcount + ancount + nscount + arcount
        return header


def qname_creator(text):
	new = text.split(".")
	new.append("") 
	i = 0
	while (i<len(new)):
		new[i] = len(new[i]).to_bytes(1,byteorder="big")+new[i].encode('ascii')
		i = i + 1
	byte_domain = b''.join(new)
	# print(byte_domain)
	return byte_domain

def query(text,qtype,qclass=1):
	header = make_header(1,1,0,0,0) 
	question = b''

	byte_domain = qname_creator(text)
	question += byte_domain

	qtp = (qtype).to_bytes(2, 'big')
	question += qtp

	qclass = (1).to_bytes(2, 'big')
	question += qclass

	# print("len :",len(header + question))
	return header + question


update_root_address()


def check_nearest_root():
	global nearest_root

	best = {"value":(0,0),"time":100}

	for i in root_ips:

		start_time = time.perf_counter()

		UDP_IP = i[1]
		UDP_PORT = 53
		add = (UDP_IP, UDP_PORT)
		packet = query(".com",2)
		# A = 1 ,NS = 2
		try:
			addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
			data, addr = sock.recvfrom(1024)
		except:
			continue
		end_time = time.perf_counter()



		execution_time = end_time - start_time
		print(f"{i[0]} Latecy: {execution_time:.4f} seconds")

		if best["time"] > execution_time:
			best["value"] = i
			best["time"] = execution_time

	nearest_root = best["value"]

def root_server(root_ip,domain):
	print(f"[+] contacting root server {root_ip[0]}")
	UDP_IP = root_ip[1]
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,2)
	tld_ips = []

	# A = 1 ,NS = 2
	addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
	data, addr = sock.recvfrom(1024)
	print(f"[+] response from {addr}")
	ns_count = int.from_bytes(data[8:10], byteorder="big")
	# Additional count (ARCOUNT) at bytes 10-11
	ar_count = int.from_bytes(data[10:12], byteorder="big")

	offset = 0

	# print(ns_count)
	print("tld count:",int(ar_count/2))
	# print(data)

	offset += len(packet)
	for i in range(ns_count):
		offset += 2 + 2 + 2 + 4 + 2
		rdata = int.from_bytes(data[offset-2:offset], byteorder="big")
		offset += rdata

	# print(data[offset:])

	for i in range(ar_count):
		offset += 2 # name
		type = int.from_bytes(data[offset:offset+2], byteorder="big")
		offset += 2 + 2 + 4 # type,class ,ttl
		rdata = int.from_bytes(data[offset:offset+2], byteorder="big")
		offset += 2
		if type == 1:
			ip = socket.inet_ntoa(data[offset:offset + rdata])
			print(ip)
			tld_ips.append(ip)
		offset += rdata
	return tld_ips
	
# print(root_server[3][1])
check_nearest_root()

domain = 'reddit.com'

root_response = root_server(nearest_root,domain)
print(root_response)

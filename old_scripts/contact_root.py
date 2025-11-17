import re
import requests
import socket
import random
import time

root_ips = []
nearest_root = []

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2.0) 


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

def read_answer(data,answer_start):
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


def read_addional(packet,data):
	additonal_ip = []
	ns_count = int.from_bytes(data[8:10], byteorder="big")
	# Additional count (ARCOUNT) at bytes 10-11
	ar_count = int.from_bytes(data[10:12], byteorder="big")

	offset = 0

	# print(ns_count)
	print("ar count:",int(ar_count/2))
	# print(data)

	offset += len(packet)

	# authority skip
	for i in range(ns_count):
		offset += 2 + 2 + 2 + 4 + 2
		rdata = int.from_bytes(data[offset-2:offset], byteorder="big")
		offset += rdata

	# reading additional
	for i in range(ar_count):
		offset += 2 # name
		type = int.from_bytes(data[offset:offset+2], byteorder="big")
		offset += 2 + 2 + 4 # type,class ,ttl
		rdata = int.from_bytes(data[offset:offset+2], byteorder="big")
		offset += 2
		if type == 1:
			ip = socket.inet_ntoa(data[offset:offset + rdata])
			print(ip)
			additonal_ip.append(ip)
		offset += rdata
	return additonal_ip

def decode_dns_name(data, offset):
    labels = []
    original_offset = offset
    jumped = False

    while True:
        length = data[offset]

        # Pointer detected
        if (length & 0xC0) == 0xC0:
            pointer_bytes = data[offset:offset+2]
            pointer_offset = int.from_bytes(pointer_bytes, 'big') & 0x3FFF
            if not jumped:
                original_offset = offset + 2  # next offset after pointer
            offset = pointer_offset
            jumped = True
            continue

        # End of name
        if length == 0:
            offset += 1
            if not jumped:
                original_offset = offset
            break

        # Normal label
        offset += 1
        labels.append(data[offset:offset+length].decode("ascii"))
        offset += length

    return ".".join(labels), original_offset

def read_authority(packet, data):
    authority_ip = []
    ns_count = int.from_bytes(data[8:10], "big")
    offset = len(packet)

    for i in range(ns_count):
        # Decode NAME first (handles pointers)
        name, name_end = decode_dns_name(data, offset)

        # TYPE (2), CLASS (2), TTL (4), RDLENGTH (2)
        rdata_len = int.from_bytes(data[name_end+8:name_end+10], "big")
        rdata_offset = name_end + 10

        # Decode NS RDATA (could have pointers)
        ns_name, _ = decode_dns_name(data, rdata_offset)
        print(f"NS record {i+1}: {ns_name}")

        offset = rdata_offset + rdata_len
        authority_ip.append(ns_name)


    return authority_ip

def root_server(root_ip,domain):
	print(f"[+] contacting root server {root_ip[0]}")
	UDP_IP = root_ip[1]
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,2)
	

	# A = 1 ,NS = 2
	addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
	data, addr = sock.recvfrom(1024)
	print(f"[+] response from {addr}")
	print(data)
	tld_ips = read_addional(packet,data)

	return tld_ips


def tld_server(tld_ips,domain,recursive=0):
	tld_ip = random.choice(tld_ips)
	tld_ips.remove(tld_ip)
	print(f"[+] contacting tld server ",tld_ip)
	UDP_IP = tld_ip
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,2)
	print(packet)
	data = ''
	try:
		addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
		data, addr = sock.recvfrom(1024)	
		print(f"[+] response from {addr}")
	except socket.timeout:
            print(f"[-] No response from , trying next server...")
            tld_server(tld_ips,domain,1)
            return 
	print("BROOO THE DATA ")
	print(data)
	if recursive == 1:
		nameserver_ns = random.choice(read_authority(packet,data))
		print("[+] finding ip of nameserver "+nameserver_ns)
		# print(nameserver_ns)
		mg = root_server(nearest_root,nameserver_ns)
		print(mg)
		ok = tld_server(mg,nameserver_ns,0)
		return ok

	else:
		print("OK UHHHHHHHHH")
		nameservers_ips = read_addional(packet,data)
		print("FOUND NAME SERVERS")
		print(nameservers_ips)
		return nameservers_ips

	# ns_count = int.from_bytes(data[8:10], byteorder="big")


def nameserver(name_ips,domain):
	name_ip = random.choice(name_ips)
	print(f"[+] contacting name server ",name_ip)
	print("DOOOOINGGGGGGGGGGGGGGGGGG")
	UDP_IP = name_ip
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,1)
	print(packet)
	addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
	data, addr = sock.recvfrom(1024)
	print(f"[+] response from {addr}")
	print(data)
	# print()
	return read_answer(data,len(packet))


check_nearest_root()
while True:
	domain = input("enter domain :")

	root_response = root_server(nearest_root,domain)
	print(root_response)

	nameserver_ips = tld_server(root_response,domain,1)

	domain_ip = nameserver(nameserver_ips,domain)
	print("*************WE FOUND YOUR IP************")
	print(f"{domain} :")
	print(domain_ip)

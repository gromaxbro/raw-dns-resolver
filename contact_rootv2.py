import re
import requests
import socket
import random
import time

root_ips = []
nearest_root = []
i = 12

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2) 


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


def make_header(recursion_desired=False, qd=1, an=0, ns=0, ar=0):
    msg_id = random.randint(0, 65535).to_bytes(2, "big")
    flags = (0x0100 if recursion_desired else 0x0000).to_bytes(2, "big")
    return (
        msg_id
        + flags
        + qd.to_bytes(2, "big")
        + an.to_bytes(2, "big")
        + ns.to_bytes(2, "big")
        + ar.to_bytes(2, "big")
    )


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

def make_opt_record(udp_payload_size=4096, extended_rcode=0, edns_version=0, z=0, data=b""):
    """
    Build a minimal EDNS(0) OPT pseudo-record.
    TYPE = 41, NAME = root (0x00)
    """
    record = b"\x00"  # NAME = root (empty)
    record += (41).to_bytes(2, "big")  # TYPE = OPT
    record += udp_payload_size.to_bytes(2, "big")  # UDP payload size
    record += extended_rcode.to_bytes(1, "big")  # Extended RCODE
    record += edns_version.to_bytes(1, "big")  # EDNS Version (0)
    record += z.to_bytes(2, "big")  # Flags (0 = none)
    record += len(data).to_bytes(2, "big")  # RDLEN
    record += data  # RDATA (usually empty)
    return record
    
def query(domain, qtype, qclass=1, use_edns=False):
    arcount = 1 if use_edns else 0
    header = make_header(recursion_desired=False, qd=1, an=0, ns=0, ar=arcount)
    qname = qname_creator(domain)
    question = qname + qtype.to_bytes(2, "big") + qclass.to_bytes(2, "big")
    if use_edns:
        question += make_opt_record()
    return header + question



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
			data, addr = sock.recvfrom(4096)

		except:
			continue
		end_time = time.perf_counter()



		execution_time = end_time - start_time
		print(f"{i[0]} Latecy: {execution_time:.4f} seconds")

		if best["time"] > execution_time:
			best["value"] = i
			best["time"] = execution_time

	nearest_root = best["value"]
def read_question(data, offset=12):
    """
    Parse and return only the QNAME (domain name) from a DNS query packet.
    Starts after the 12-byte DNS header.
    """
    labels = []
    while True:
        length = data[offset]
        if length == 0:
            break
        offset += 1
        labels.append(data[offset:offset + length].decode("ascii"))
        offset += length
    domain = ".".join(labels)
    return domain


def read_answer(data, answer_start):
    i = 0
    ans = data[answer_start:]
    val_arr = []

    while i + 12 <= len(ans):  # ensure header fits
        rtype = int.from_bytes(ans[i+2:i+4], 'big')
        rclass = int.from_bytes(ans[i+4:i+6], 'big')
        rttl = int.from_bytes(ans[i+6:i+10], 'big')
        rdlen = int.from_bytes(ans[i+10:i+12], 'big')

        rdata = ans[i+12:i+12+rdlen]

        # only process A records (type 1, 4-byte RDATA)
        if rtype == 1 and rdlen == 4:
            value = socket.inet_ntoa(rdata)
            val_arr.append((value, rttl))
            print(f"type={rtype}, class={rclass}, ttl={rttl}, rdlen={rdlen}, value={value}")

        # move to next record
        i += 12 + rdlen

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


def root_server(sock,root_ip,domain):
	print(f"[+] contacting root server {root_ip[0]}")
	UDP_IP = root_ip[1]
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,2)
	

	# A = 1 ,NS = 2
	addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
	data, addr = sock.recvfrom(4096)

	print(f"[+] response from {addr}")
	print(data)
	tld_ips = read_addional(packet,data)

	return tld_ips

def find_answer_start(data):
    # skip 12-byte header
    offset = 12
    # skip the question name (variable length)
    while data[offset] != 0:
        offset += data[offset] + 1
    # skip null terminator + QTYPE(2 bytes) + QCLASS(2 bytes)
    offset += 5
    return offset


def nameserver(sock,name_ips,domain):

	if isinstance(name_ips, tuple):
		name_ips = [name_ips]

	if not name_ips:
		print("[-] No nameserver IPs to query. Exiting.")
		return None

	choice = random.choice(name_ips)

	name_ip = choice[0] if isinstance(choice, tuple) else choice

    # Remove it safely
	name_ips = [x for x in name_ips if (x[0] if isinstance(x, tuple) else x) != name_ip]

	print(f"[+] contacting name server ",name_ip)
	print("DOOOOINGGGGGGGGGGGGGGGGGG")
	UDP_IP = name_ip
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain, 1, use_edns=True)

	print(packet)
	try:
		addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
		data, addr = sock.recvfrom(4096)

		print(f"[+] response from {addr}")
		print(data)
	except socket.timeout:
		print(f"[-] No response from nameserver {name_ip}, trying next server...")
		if name_ips:  # make sure there are servers left
			return nameserver(sock,name_ips,domain)
		else:
			print("[-] All Bopm bom servers failed.")
			return None

	# print(data)
	answer_start = find_answer_start(data)
	return read_answer(data, answer_start)


def NS_TO_IP(sock,packet,data):
	nameserver_ns = random.choice(read_authority(packet,data))
	print("[+] finding ip of nameserver "+nameserver_ns)
	mg = root_server(sock,nearest_root,nameserver_ns)
	print(mg)
	nameserver_tld = tld_server(sock,mg,nameserver_ns)
	print("Found namerserver NS -- namerserver Ip")
	print(nameserver_tld)
	namer_ip = nameserver(sock,nameserver_tld,nameserver_ns)
	return [namer_ip[0]]


def tld_server(sock,tld_ips,domain,recursive=0):
	tld_ip = random.choice(tld_ips)
	tld_ips.remove(tld_ip)
	print(f"[+] contacting tld server ",tld_ip)
	UDP_IP = tld_ip
	UDP_PORT = 53
	add = (UDP_IP, UDP_PORT)
	packet = query(domain,2)
	print(packet)
	# data = ''
	try:
		addr = sock.sendto(packet, (UDP_IP, UDP_PORT))
		data, addr = sock.recvfrom(4096)
	
		print(f"[+] response from {addr}")
	except socket.timeout:
	    print(f"[-] No response from {tld_ip}, trying next server...")
	    if tld_ips:  # make sure there are servers left
	        return tld_server(sock,tld_ips, domain, 1)
	    else:
	        print("[-] All TLD servers failed.")
	        return None

	print("Tld server response data :-")
	print(data)
	glued_ip = read_addional(packet,data)
	if glued_ip:
		print("[+] Found glued ip")
		return glued_ip

	ok = NS_TO_IP(sock,packet,data)
	return ok

def hostname(domain):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
	s.settimeout(2) 

	print("root --> tld")
	root_res = root_server(s,nearest_root,domain)

	print("Main query Tld :-",root_res)

	print("tld --> namerserver NS")
	tld = tld_server(s,root_res,domain,1)

	print("nameserver Ip ---> Domain IP")
	namer_res = nameserver(s,tld,domain)
	print(namer_res)
	return namer_res

update_root_address()
check_nearest_root()

UDP_IP = "127.0.0.1"
UDP_PORT = 1234

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket
add = (UDP_IP, UDP_PORT)
sock.bind(add)
print(f"Listening for UDP packets on {UDP_IP}:{UDP_PORT}")



while True:
	# domain = "human.com"
	# domain = input("fg: ")
	# hostname(domain)
	data, addr = sock.recvfrom(1024)
	print(addr)
	question = read_question(data)
	print("name:= ",question)
	hostname(question)
	# ok
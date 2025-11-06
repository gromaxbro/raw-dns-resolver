# Python Raw DNS Resolver

A low-level recursive DNS resolver written in Python.  
Manually constructs DNS queries, contacts root, TLD, and authoritative name servers, and resolves IPv4 addresses (A records) for domains.

---

## Features

- Reads root server IPs from `root.hints` file.
- Measures latency to find the nearest root server.
- Supports EDNS(0) queries via OPT records.
- Resolves domains recursively:
  - Root → TLD → Authoritative Name Server → Domain IP
- Parses DNS response packets to extract:
  - A records (IPv4)
  - NS records (Name servers)
  - Additional records (glue IPs)
- Handles server timeouts and retries.
- Uses raw UDP sockets, no high-level DNS libraries.

---

## Requirements

- Python 3.x
- Internet access
- Optional: `requests` module

---

## Setup

Ensure you have a root.hints file with root server addresses in this format:
```
A.ROOT-SERVERS.NET. 3600000 IN A 198.41.0.4
B.ROOT-SERVERS.NET. 3600000 IN A 199.9.14.201
C.ROOT-SERVERS.NET. 3600000 IN A 192.33.4.12
```
(Use all 13 root servers for best results.)

### Run the resolver:
python resolver.py

### Enter a domain to resolve:
domain: example.com

## How It Works

### Load Root Servers
The script reads root.hints, extracting all A records. These are the starting points for resolution.

## Find Nearest Root
Sends small DNS queries to each root server and measures latency. Chooses the fastest root server to start queries.

### Build DNS Query Packets
```
Header: transaction ID, flags, question/answer counts

Question section: domain name, type (A/NS), class (IN)

Optional EDNS0 record

Recursive Resolution

Root → TLD: Queries root server for the TLD (e.g., .com) NS records and glue IPs.

TLD → Authoritative: Queries TLD server for authoritative name server of domain.

Authoritative → Domain IP: Queries authoritative server to get A record(s).

Parse Responses

Extracts answers, NS records, and additional glue IPs from raw DNS packet bytes.

Handles pointers, compression, and offsets manually.

Retries and Fallbacks

If a server does not respond within the timeout, moves to another server.

Supports multiple authoritative or TLD servers to improve reliability.
```
## Limitations

Only resolves IPv4 addresses (A records).

Does not cache results.

Minimal error handling; not suitable for production.

Requires UDP port 53 to be open.

May fail if a DNS server does not respond or blocks queries.

## Example Usage
```
$ python resolver.py
domain: example.com
[+] contacting root server A.ROOT-SERVERS.NET
root --> tld
[+] contacting TLD server for .com
tld --> nameserver NS
[+] contacting authoritative name server
nameserver IP --> domain IP
['93.184.216.34']
```
## File Structure

resolver.py — main Python script (your code)

root.hints — root server hints file (required)

License
MIT License

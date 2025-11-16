# Python Iterative DNS Resolver

A low-level iterative DNS resolver written in Python that talks directly to DNS root, TLD, and authoritative name servers over UDP, maintains a simple cache, and exposes a local UDP DNS server interface (like a tiny custom dig/resolver).

> Educational project: focuses on understanding DNS packet structure, iterative resolution, caching, and concurrent request handling.

---

## Features

- Pure-Python DNS resolver using raw UDP sockets.
- Iterative resolution from root → TLD → authoritative name server.
- Uses a `root.hints` file (like real resolvers) to bootstrap root server IPs.
- Latency-based selection of the “nearest” root server.
- Parses and builds DNS packets manually (no dnspython).
- Supports:
  - A-record lookups (IPv4).
  - EDNS(0) OPT record for larger UDP payloads.
  - Basic DNS name compression (pointers) when parsing.
- Simple cache layer with TTL and periodic eviction.
- Multithreaded UDP server that listens on `127.0.0.1:1234` and answers queries from DNS clients.

---

## How It Works (High-Level)

1. **Startup**
   - `update_root_address()` parses `root.hints` and extracts all IPv4 root server addresses.
   - `check_nearest_root()` measures round-trip latency to each root using a test NS query and picks the fastest one as `nearest_root`.

2. **Handling a client query**
   - The main thread binds a UDP socket on `127.0.0.1:1234` and waits for incoming DNS packets.
   - For every incoming packet, a new worker thread is spawned with `worker(data)`.
   - `worker`:
     - Prints header info (`read_data`).
     - Extracts the QNAME/domain using `read_question`.
     - Calls `hostname(domain)` to resolve the domain.
     - Builds a DNS response with the original ID, flags set to “standard response, no error” and the resolved A records (if any).
     - Sends the full DNS response back to the client.

3. **Resolution path (`hostname`)**
   - Checks the local cache with `get_records(domain, "A", "IN")`.
     - If cache hit: converts cached records to `(ip, ttl)` list and returns immediately.
   - Otherwise:
     - Uses the pre-computed `nearest_root` and calls `root_server` with QTYPE NS for the domain.
     - From the root server response, `read_addional` extracts “glue” IPs for TLD servers.
     - `tld_server` queries one of these TLD servers:
       - If additional section contains authoritative NS IPs (glue), they are returned.
       - Otherwise, `NS_TO_IP` is used to resolve NS hostnames to IPs by recursively querying again.
     - `nameserver` finally queries the authoritative name server for the A record (QTYPE A, EDNS enabled).
     - The A records are parsed by `read_answer` (extracts IPv4 and TTL).
     - Successful answers are cached via `set_records(domain, namer_res, "A")`.

4. **Caching**
   - External `cache.py` exposes:
     - `get_records(domain, rtype, rclass="IN")`.
     - `set_records(domain, records, rtype)`.
     - `purge_expired()` to remove entries whose TTL has passed.
   - A daemon thread `periodic_purge` runs every 5 minutes and calls `purge_expired()` to keep cache fresh.
   - `purge_expired()` is also called after every client request loop.

---

## Project Structure

Example layout:

.
├── resolver.py        # main code shown in the snippet
├── cache.py           # cache implementation (TTL store)
├── root.hints         # list of root DNS servers (like ISC root hints)
└── README.md          # this file

---

## File: root.hints

`root.hints` should contain root server records, similar to:

; Root hints example
A.ROOT-SERVERS.NET.      3600000 A 198.41.0.4
B.ROOT-SERVERS.NET.      3600000 A 199.9.14.201
; ...

`update_root_address()` uses a regex to extract only IPv4 `A` records from this file and appends them to `root_ips` as `(name, ip)` tuples.

---

## Key Functions (Overview)

### DNS Message Construction

- `make_header(recursion_desired=False, qd=1, an=0, ns=0, ar=0)`
  Builds the DNS header with a random message ID and flags. Sets the RD bit according to `recursion_desired`.

- `qname_creator(text)`
  Converts a domain like `"example.com"` into DNS wire format labels: `<len>example<len>com<0>`.

- `make_opt_record(...)`
  Creates a minimal EDNS(0) OPT record (TYPE 41) to allow larger UDP payloads.

- `query(domain, qtype, qclass=1, use_edns=False)`
  Assembles full DNS query message = header + question (+ optional OPT record in additional).

### DNS Parsing

- `read_question(data, offset=12)`
  Parses QNAME labels from a DNS query and returns them as a dot-separated domain string.

- `decode_dns_name(data, offset)`
  Generic name decoder that supports:
  - Plain labels.
  - Compressed names with pointer bytes (`0xC0` prefix).

- `read_data(data)`
  Reads and prints header fields:
  ID, FLAGS, QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT.

- `read_answer(data, answer_start)`
  Iterates over the answer section, extracting:
  `rtype`, `rclass`, `ttl`, `rdlen`, and IPv4 addresses.
  Returns a list of `(ip, ttl)` tuples for A records.

- `read_authority(packet, data)`
  Parses authority section NS records using `decode_dns_name` for both owner name and NS target.
  Returns a list of nameserver hostnames.

- `read_addional(packet, data)`
  Parses additional section and collects IPv4 addresses from A records (glue).
  Skips over authority section by using header counts and RDLENGTH.

### Resolution Logic

- `root_server(sock, root_ip, domain)`
  Sends NS query for `domain` to the selected root server.
  Returns TLD server IPs from additional section if present.

- `tld_server(sock, tld_ips, domain, recursive=0)`
  Picks a random TLD server from `tld_ips` and queries for NS records of `domain`.
  If glue A records are present in additional: returns them.
  Else: calls `NS_TO_IP` to convert NS names to IP addresses.

- `NS_TO_IP(sock, packet, data)`
  Uses `read_authority` to get NS names.
  Randomly picks one NS hostname, resolves it using:
  `root_server` → `tld_server` → `nameserver` again.
  Returns authoritative name server IPs as a list.

- `nameserver(sock, name_ips, domain)`
  Handles querying the authoritative nameserver for final A records.
  Supports `name_ips` as list of raw IPs or `(name, ip)` tuples.
  Uses EDNS and recursion-off queries.
  Retries with other nameservers on timeout.

- `hostname(domain)`
  Top-level resolver function:
  - Check cache; if hit, return cached A records.
  - Else:
    1. Query root server for TLD referral.
    2. Query TLD server for NS referral or glue.
    3. Query nameserver for final A record(s).
  - Cache results via `set_records`.
  - Return `(ip, ttl)` list.

---

## DNS Server Loop

- Binds UDP socket on `127.0.0.1:1234`.

- Background thread:
  - `periodic_purge()` runs every 300 seconds and calls `purge_expired()`.

- Main loop:

  while True:
      data, addr = sock.recvfrom(1024)
      t = threading.Thread(target=worker, args=(data,))
      t.daemon = True
      t.start()
      purge_expired()

- `worker(data)`:
  - Parses query, extracts QNAME.
  - Calls `hostname(question)` for resolution.
  - Constructs client header with `make_client_header(data, len(asn))`.
  - Constructs answer section with `make_answer(data, asn)`.
  - Sends full DNS response back via `sock.sendto(header + answer, addr)`.

---

## Usage

### Requirements

- Python 3.x
- A `root.hints` file with valid root server A records.
- A `cache.py` module exposing at least:

  def get_records(domain, rtype, rclass="IN"): ...
  def set_records(domain, records, rtype): ...
  def purge_expired(): ...
  def view_all(): ...
  def print_view(): ...

### Run the Resolver

python resolver.py

You should see logs like:

[+] root file updated
<root> Latency: ...
Listening for UDP packets on 127.0.0.1:1234
...

Then you can point a DNS client at 127.0.0.1:1234 and send A-record queries to test the resolver.

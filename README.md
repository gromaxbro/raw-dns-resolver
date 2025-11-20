# Custom DNS Resolver

This project implements a DNS resolver that performs iterative queries from root servers down to authoritative name servers to resolve domain names to IP addresses.

---

## Features

- Reads root server hints from `root.hints`
- Contacts root, TLD, and authoritative DNS servers via UDP
- Constructs and parses DNS query and response packets manually
- Supports DNS query types A (IPv4 address) and NS (Name Server)
- Caches DNS records locally with TTL support
- Handles additional and authority DNS sections including glue records
- Uses threading for concurrent query handling and periodic cache purging
- Implements EDNS(0) OPT pseudo-record for extended DNS features

---

## How It Works

See detailed explanation and design in [Note.md](./Note.md).


1. **Initialization**  
   Loads root server IPs from `root.hints` file.

2. **Finding Nearest Root Server**  
   Measures latency to root servers and selects the fastest for queries.

3. **DNS Query Construction**  
   Builds DNS query packets including headers, questions, and optional EDNS record.
   ```
   +---------------------+
   | Header              |
   +---------------------+
   | Question            |
   +---------------------+
   | Answer              | 
   +---------------------+
   | Authority           | 
   +---------------------+
   | Additional          | 
   +---------------------+
```
4. **Iterative Resolution**  
   - Query root server for TLD servers for the domain.  
   - Query TLD servers for it returns namerserver domain + glued ip (only if in same zone) like .com tld only will give hostinger.com nameserver ip not hostinger.net ip.  
   - Query authoritative servers for the final IP address.

   `root server --> tld server --> nameserver`

   *note:- sometimes tld only return nameserver domain name (because of out-zone) .so we have to start new query from starting for finding namerserver ip`root server --> tld server -->(gluedip)`*

5. **Response Parsing**  
   Parses DNS response sections: answers, authority, and additional records.

   rootserver server returns:- only authority
   tld server server returns :- authority + additional
   nameserver returns :- answer

6. **Caching**  
   Stores resolved DNS records with TTL and purges expired entries periodically.
   we used `lmdb` incache memory for fast reponse

7. **UDP Server**  
   Listens locally on UDP port 1234 for incoming DNS queries and responds using cache or fresh resolution.

---

## Usage

- Run the resolver: it listens on `127.0.0.1:1234` UDP for DNS queries.
- Queries are resolved by iterative DNS lookup and answered with cached or fresh data.
- Logs resolution steps and latency for debugging.

---

## Requirements

- Python 3.x
- `cache.py` module for DNS record caching and management

---

## Limitations

- Supports only basic DNS query types (A and NS).
- No DNSSEC or advanced security features.
- Assumes IPv4-only queries and responses.
- Timeout handling with retries is basic.

---

## Future Improvements

- Support for other query types (AAAA, MX, TXT).
- Full DNSSEC validation.
- Better error handling and retry logic.
- IPv6 support.
- Performance optimizations and asynchronous IO.

---

This project demonstrates low-level DNS protocol handling and iterative resolver mechanics suitable for learning network programming and DNS internals.

Python DNS Resolver

A minimal recursive DNS resolver implemented in Python.
Constructs DNS packets, queries root/TLD/authoritative servers, and returns A records (IPv4).

USAGE
1. Place root server hints in `root.hints`, lines like:
   A.ROOT-SERVERS.NET. 3600000 IN A 198.41.0.4

2. Run the script:
   python resolver.py

3. Enter a domain when prompted:
   domain: example.com

WHAT IT DOES
- Reads root.hints for root server IPs.
- Chooses nearest root by UDP latency.
- Builds DNS queries (supports EDNS(0) OPT).
- Walks resolution: root -> TLD -> authoritative -> A record.
- Parses DNS response bytes for A, NS and additional glue records.
- Retries other servers on timeouts.

LIMITATIONS
- IPv4 only (A records).
- No caching.
- Basic error handling; not production hardened.
- Requires UDP port 53 access.

FILES
- resolver.py        # main script (your code)
- root.hints         # root server hints file (required)

DEPENDENCIES
- Python 3.x
- (optional) requests

LICENSE
MIT

# HEADERS
```
### Field   Size (bits)     Description
ID         16              A unique identifier assigned by the client. Used to match responses to queries.
Flags      16              Contains control bits (see below).
QDCOUNT    16              Number of entries in the Question section.
ANCOUNT    16              Number of resource records in the Answer section.
NSCOUNT    16              Number of name server (Authority) records.
ARCOUNT    16              Number of additional records
```

# QUESTION
```
QNAME   The queried domain name, encoded as labels (e.g., www.google.com → 3www6google3com0).
QTYPE   Type of record requested (e.g., 1 = A, 28 = AAAA, 15 = MX).
QCLASS  Usually 1 for Internet (IN).
```

## QTYPE (DNS Records)
```
### QTYPE   Meaning Notes
1       A       IPv4 address
28      AAAA    IPv6 address
5       CNAME   Canonical name / alias
15      MX      Mail exchange server
2       NS      Authoritative name server
12      PTR     Reverse DNS lookup
16      TXT     Arbitrary text
33      SRV     Service location (used in SIP, XMPP, etc.)
```

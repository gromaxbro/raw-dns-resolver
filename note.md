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

1️⃣ Byte 1 (first 8 bits)
```
Bit	Value	Meaning
7	128	QR (0=query, 1=response)
6	64	Opcode bit 3 (0)
5	32	Opcode bit 2(00000 Standard Query,rare need change)
4	16	Opcode bit 1 (0)
3	8	Opcode bit 0 (0)
2	4	AA (AA 0 (set clients no auth) or a recersive, 1 = is a namserver)
1	2	TC (Truncated) (TC = 1 truncated use TCP ,TC = 0 the message iscomplete)
0	1	RD (Recursion Desired) (1 → server can do recursion ,0 → cannot do)

1+0+0+0+0+0+0+128

```
2️⃣ Byte 2 (next 8 bits)
```
Bit	Value	Meaning
7	128	RA (Recursion Available) queries  RA = 0.responses,most modern resolver RA = 1.
6	64	Z (Reserved) (0)
5	32	Z (Reserved) (0)
4	16	Z (Reserved) (0)
3	8	RCODE bit 3
2	4	RCODE bit 2 only for response else 0
1	2	RCODE bit 1
0	1	RCODE bit 0
```


## contact to root server

there are 13 root server in the world we can find ips in `root hint file`

- first ping all the servers and get nearest one and work with it

usually root servers are Anycast (many physical server uses same ip) 

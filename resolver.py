import socket
from urllib.parse import urlparse

from cache import get_records, set_records, print_view, purge_expired

def sanitize_url(url: str):
    url = url.strip()
    parsed = urlparse(url if "://" in url else f"https://{url}")
    host = parsed.netloc or parsed.path
    host = host.strip("[]")
    if "@" in host:
        host = host.split("@", 1)[-1]
    if ":" in host:
        host, _ = host.rsplit(":", 1)
    return host.lower()

def resolve_any(hostname: str, rtype: str = "A", rclass: str = "IN"):
    rtype = rtype.upper()

    # 1) Try cache
    cached = get_records(hostname, rtype, rclass)
    if cached:
        return cached

    # 2) Resolve with lib.
    # System stub for addresses; no TTLs available
    results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
    addrs = []
    for fam, _t, _p, _c, sockaddr in results:
        addr = sockaddr[0]
        if (rtype == "A" and fam == socket.AF_INET) or (rtype == "AAAA" and fam == socket.AF_INET6):
            addrs.append(addr)
    addrs = list(dict.fromkeys(addrs))
    # Use conservative default TTL when no authoritative TTL is available
    if addrs:
        set_records(hostname, [(v, 300) for v in addrs], rtype, rclass)
    return addrs


if __name__ == "__main__":
    purge_expired()
    
    url = input("provide the url: ")
    if len(url) <= 0:
        print_view()
    else:
        host = sanitize_url(url)
        # Example: resolve MX
        print("A:", resolve_any(host, "A"))
        print("AAAA:", resolve_any(host, "AAAA"))
        print("MX:", resolve_any(host, "MX"))
        print("TXT:", resolve_any(host, "TXT"))

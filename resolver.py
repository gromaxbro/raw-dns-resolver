from urllib.parse import urlparse
import socket

# User provides the URL
url = input("provide the url: ")

def sanitize_url(url):
    """Adds a default scheme (https://) if the URL is missing one."""
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url

    sanitized_url = urlparse(url)

    return sanitized_url.netloc


def resolve(hostname):
    """
    Performs a DNS lookup that uses the OS-level cache.
    The OS will check its cache before performing a new query.
    """
    try:
        # getaddrinfo is the recommended modern function
        # It can return multiple results for a hostname
        results = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
        
        # Extract and print the unique IP addresses
        ips = {addr[4][0] for addr in results}
        
        print(f"IP addresses for {hostname}: {list(ips)}")
        
    except socket.gaierror as e:
        print(f"Error resolving {hostname}: {e}")


print(resolve(sanitize_url(url)))
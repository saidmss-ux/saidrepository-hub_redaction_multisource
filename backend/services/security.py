import ipaddress
import socket
from urllib.parse import urlparse

from backend.services.errors import ServiceError


PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def validate_public_http_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ServiceError(code="invalid_url_scheme", message="Only http/https URLs are allowed")

    host = parsed.hostname
    if not host:
        raise ServiceError(code="invalid_url", message="URL host is required")

    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        raise ServiceError(code="blocked_host", message="Localhost and loopback hosts are blocked")

    try:
        addr_info = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise ServiceError(code="dns_resolution_failed", message="Unable to resolve host")

    for info in addr_info:
        ip = ipaddress.ip_address(info[4][0])
        if any(ip in network for network in PRIVATE_NETS):
            raise ServiceError(code="blocked_private_network", message="Private network addresses are blocked")

    return url

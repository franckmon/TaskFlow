import ipaddress
from typing import Sequence

from fastapi import Request

DEFAULT_CLIENT_IP = "127.0.0.1"


def parse_trusted_proxies(value: str) -> tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...]:
    """Parse comma-separated proxy IPs or CIDR ranges."""
    networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
    for part in value.split(","):
        entry = part.strip()
        if not entry:
            continue
        if "/" in entry:
            networks.append(ipaddress.ip_network(entry, strict=False))
            continue
        address = ipaddress.ip_address(entry)
        networks.append(ipaddress.ip_network(f"{address}/{address.max_prefixlen}", strict=False))
    return tuple(networks)


def is_trusted_proxy(
    ip: str,
    trusted_proxies: Sequence[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> bool:
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(address in network for network in trusted_proxies)


def _normalize_ip(value: str) -> str | None:
    candidate = value.strip()
    if not candidate:
        return None

    if candidate.startswith("["):
        closing = candidate.find("]")
        if closing != -1:
            candidate = candidate[1:closing]
    elif candidate.count(":") == 1 and "." in candidate:
        host, port = candidate.rsplit(":", 1)
        if port.isdigit():
            candidate = host

    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _get_direct_peer_ip(request: Request) -> str:
    if not request.client or not request.client.host:
        return DEFAULT_CLIENT_IP
    normalized = _normalize_ip(request.client.host)
    return normalized or DEFAULT_CLIENT_IP


def _resolve_client_ip(
    request: Request,
    trusted_proxies: Sequence[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> str:
    """
    Resolve client IP for rate limiting behind reverse proxies.

    X-Forwarded-For and X-Real-IP are honored only when the direct peer is trusted.
    """
    peer = _get_direct_peer_ip(request)
    if not trusted_proxies or not is_trusted_proxy(peer, trusted_proxies):
        return peer

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        chain: list[str] = []
        for part in forwarded_for.split(","):
            normalized = _normalize_ip(part)
            if normalized is not None:
                chain.append(normalized)
        chain.append(peer)

        for ip in reversed(chain):
            if not is_trusted_proxy(ip, trusted_proxies):
                return ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        normalized = _normalize_ip(real_ip)
        if normalized and not is_trusted_proxy(normalized, trusted_proxies):
            return normalized

    return peer


def get_client_ip(request: Request) -> str:
    """Return the client IP used for login rate limiting."""
    from app.core.config import settings

    return _resolve_client_ip(request, settings.trusted_proxies)

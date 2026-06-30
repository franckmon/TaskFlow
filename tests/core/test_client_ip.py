import ipaddress

import pytest
from starlette.requests import Request

from app.core.client_ip import (
    DEFAULT_CLIENT_IP,
    _resolve_client_ip,
    is_trusted_proxy,
    parse_trusted_proxies,
)


def _make_request(
    *,
    client_host: str,
    x_forwarded_for: str | None = None,
    x_real_ip: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if x_forwarded_for is not None:
        headers.append((b"x-forwarded-for", x_forwarded_for.encode()))
    if x_real_ip is not None:
        headers.append((b"x-real-ip", x_real_ip.encode()))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "client": (client_host, 0),
        "server": ("testserver", 80),
        "scheme": "http",
        "http_version": "1.1",
    }
    return Request(scope)


class TestParseTrustedProxies:
    def test_parses_single_ip(self) -> None:
        networks = parse_trusted_proxies("10.0.0.1")

        assert len(networks) == 1
        assert ipaddress.ip_address("10.0.0.1") in networks[0]

    def test_parses_cidr_range(self) -> None:
        networks = parse_trusted_proxies("10.0.0.0/8")

        assert ipaddress.ip_address("10.0.0.5") in networks[0]

    def test_parses_comma_separated_values(self) -> None:
        networks = parse_trusted_proxies("10.0.0.1, 192.168.1.0/24")

        assert len(networks) == 2

    def test_rejects_invalid_entry(self) -> None:
        with pytest.raises(ValueError):
            parse_trusted_proxies("not-an-ip")


class TestResolveClientIp:
    def test_ignores_x_forwarded_for_without_trusted_proxies(self) -> None:
        request = _make_request(client_host="203.0.113.10", x_forwarded_for="198.51.100.20")

        assert _resolve_client_ip(request, ()) == "203.0.113.10"

    def test_ignores_spoofed_x_forwarded_for_from_untrusted_peer(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.1")
        request = _make_request(client_host="203.0.113.10", x_forwarded_for="198.51.100.20")

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_uses_x_forwarded_for_from_trusted_proxy(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.1")
        request = _make_request(client_host="10.0.0.1", x_forwarded_for="203.0.113.10")

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_uses_x_real_ip_from_trusted_proxy(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.1")
        request = _make_request(client_host="10.0.0.1", x_real_ip="203.0.113.10")

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_falls_back_to_peer_when_trusted_proxy_has_no_header(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.1")
        request = _make_request(client_host="10.0.0.1")

        assert _resolve_client_ip(request, trusted) == "10.0.0.1"

    def test_resolves_client_across_multiple_trusted_hops(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.0/8")
        request = _make_request(
            client_host="10.0.0.2",
            x_forwarded_for="203.0.113.10, 10.0.0.1",
        )

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_uses_leftmost_untrusted_ip_in_forwarded_chain(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.2")
        request = _make_request(
            client_host="10.0.0.2",
            x_forwarded_for="198.51.100.20, 203.0.113.10",
        )

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_normalizes_ipv4_with_port(self) -> None:
        trusted = parse_trusted_proxies("10.0.0.1")
        request = _make_request(client_host="10.0.0.1", x_forwarded_for="203.0.113.10:12345")

        assert _resolve_client_ip(request, trusted) == "203.0.113.10"

    def test_returns_default_when_client_is_missing(self) -> None:
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "client": None,
            "server": ("testserver", 80),
            "scheme": "http",
            "http_version": "1.1",
        }
        request = Request(scope)

        assert _resolve_client_ip(request, ()) == DEFAULT_CLIENT_IP

    def test_is_trusted_proxy_matches_cidr(self) -> None:
        trusted = parse_trusted_proxies("172.16.0.0/12")

        assert is_trusted_proxy("172.16.5.1", trusted) is True
        assert is_trusted_proxy("8.8.8.8", trusted) is False

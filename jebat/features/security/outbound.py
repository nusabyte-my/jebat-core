"""Validation helpers for user-controlled outbound network requests."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urljoin, urlsplit

import httpx


class OutboundURLBlocked(ValueError):
    """Raised when an outbound destination is not safe to contact."""


Resolver = Callable[..., list[tuple]]

_METADATA_HOSTS = {"metadata", "metadata.google.internal"}
_SHARED_ADDRESS_SPACE = ipaddress.ip_network("100.64.0.0/10")


def _is_blocked_ip(value: str) -> bool:
    address = ipaddress.ip_address(value)
    if address.version == 6 and address.ipv4_mapped:
        address = address.ipv4_mapped
    return (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
        or getattr(address, "is_site_local", False)
        or address in _SHARED_ADDRESS_SPACE
    )


def validate_outbound_host(host: str, *, resolver: Resolver = socket.getaddrinfo) -> str:
    """Return a public host after rejecting unsafe literals and DNS answers."""
    normalized = host.rstrip(".").lower()
    if not normalized or normalized in _METADATA_HOSTS:
        raise OutboundURLBlocked("Outbound destination is not allowed")

    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        pass
    else:
        if _is_blocked_ip(normalized):
            raise OutboundURLBlocked("Outbound destination resolves to a blocked address")
        return normalized

    try:
        answers = resolver(normalized, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise OutboundURLBlocked("Outbound destination could not be resolved") from exc
    if not answers:
        raise OutboundURLBlocked("Outbound destination could not be resolved")
    for answer in answers:
        if _is_blocked_ip(answer[4][0]):
            raise OutboundURLBlocked("Outbound destination resolves to a blocked address")
    return normalized


def validate_outbound_url(url: str, *, resolver: Resolver = socket.getaddrinfo) -> str:
    """Validate an HTTP(S) URL and every address currently returned by DNS."""
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise OutboundURLBlocked("Only absolute HTTP(S) URLs without credentials are allowed")
    try:
        _ = parsed.port
    except ValueError as exc:
        raise OutboundURLBlocked("Outbound URL has an invalid port") from exc
    validate_outbound_host(parsed.hostname, resolver=resolver)
    return url


async def get_validated(
    client: httpx.AsyncClient,
    url: str,
    *,
    max_redirects: int = 5,
    **kwargs: object,
) -> httpx.Response:
    """GET a public URL, validating DNS before each request and redirect hop."""
    current_url = url
    for _ in range(max_redirects + 1):
        validate_outbound_url(current_url)
        response = await client.get(current_url, follow_redirects=False, **kwargs)
        if not response.is_redirect:
            return response
        location = response.headers.get("location")
        await response.aclose()
        if not location:
            raise OutboundURLBlocked("Redirect response did not include a location")
        current_url = urljoin(current_url, location)
    raise OutboundURLBlocked("Too many redirects")

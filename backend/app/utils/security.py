import socket
import ipaddress
import urllib.parse
from typing import List, Optional
from fastapi import HTTPException, status


def parse_numeric_ipv4(hostname: str) -> Optional[str]:
    """
    Parses non-standard numeric IPv4 formats (e.g., dword integer 2130706433, hex 0x7f000001, shorthand 127.1)
    into standard dotted-decimal IPv4 address strings.
    """
    if not hostname or not isinstance(hostname, str):
        return None

    # Handle dword / hex / octal integer strings (e.g. 2130706433 or 0x7f000001)
    if hostname.isdigit() or hostname.startswith(("0x", "0X")):
        try:
            val = int(hostname, 0)
            if 0 <= val <= 0xFFFFFFFF:
                return str(ipaddress.IPv4Address(val))
        except Exception:
            pass

    # Handle shorthand octet formats (e.g. 127.1 -> 127.0.0.1 or 10.1 -> 10.0.0.1)
    parts = hostname.split(".")
    if 2 <= len(parts) <= 3:
        try:
            nums = [int(p, 0) for p in parts]
            if all(0 <= n <= 255 for n in nums[:-1]):
                last_num = nums[-1]
                if len(parts) == 2 and 0 <= last_num <= 0xFFFFFF:
                    val = (nums[0] << 24) + last_num
                    return str(ipaddress.IPv4Address(val))
                elif len(parts) == 3 and 0 <= last_num <= 0xFFFF:
                    val = (nums[0] << 24) + (nums[1] << 16) + last_num
                    return str(ipaddress.IPv4Address(val))
        except Exception:
            pass

    return None


def is_ip_prohibited(ip_str: str) -> bool:
    """
    Evaluates whether an IPv4 or IPv6 address belongs to a prohibited/non-global network range.
    Uses default-deny for non-global addresses (private, loopback, link-local, multicast, reserved, ULA, CGNAT).
    Supports IPv4-mapped IPv6 addresses (e.g., ::ffff:127.0.0.1 or ::ffff:169.254.169.254).
    """
    try:
        ip_obj = ipaddress.ip_address(ip_str)
    except ValueError:
        return True

    # Unwrap IPv4-mapped IPv6 addresses
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        ip_obj = ip_obj.ipv4_mapped

    # Default-deny any address that is not globally routable
    if not ip_obj.is_global:
        return True

    if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_unspecified or ip_obj.is_multicast:
        return True

    return False


def resolve_host_ips(hostname: str) -> List[str]:
    """
    Resolves hostname to a list of IP addresses via DNS.
    Handles standard and non-standard numeric IPv4 representations (dword, hex, octal, shorthand).
    """
    # Check non-standard numeric IPv4 representation first
    numeric_ip = parse_numeric_ipv4(hostname)
    if numeric_ip:
        return [numeric_ip]

    try:
        ip_obj = ipaddress.ip_address(hostname)
        return [str(ip_obj)]
    except ValueError:
        pass

    resolved_ips: List[str] = []
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for res in addr_info:
            sockaddr = res[4]
            ip_str = sockaddr[0]
            if ip_str not in resolved_ips:
                resolved_ips.append(ip_str)
    except Exception:
        pass
    return resolved_ips


def validate_and_sanitize_url(
    url: str,
    mode: str = "remote",
    is_production: bool = False,
    allow_localhost: bool = False
) -> str:
    """
    Validates that a URL is a well-formed HTTP/HTTPS URL and enforces strict SSRF protections.
    
    Modes:
      - 'remote': Public websites only. Rejects loopback, private IP targets, and non-global DNS destinations.
      - 'local': Controlled localhost / loopback targets only (dev environment only).
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL string is required."
        )
    
    url = url.strip()
    
    url_lower = url.lower()
    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must begin with http:// or https://"
        )
    
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid URL structure: {str(e)}"
        )
    
    if parsed.scheme.lower() not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only HTTP and HTTPS schemes are supported."
        )

    # Reject URLs containing embedded credentials or userinfo (e.g. http://user:pass@host or http://example.com@127.0.0.1)
    if parsed.username or parsed.password or "@" in (parsed.netloc.split(":")[0] if ":" in parsed.netloc else parsed.netloc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Embedded credentials or userinfo syntax in target URLs are not permitted."
        )
    
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must contain a valid domain name or host IP."
        )
    
    hostname_lower = hostname.lower()

    if allow_localhost and (mode is None or mode == "remote"):
        effective_mode = "local"
    else:
        effective_mode = mode or "remote"

    mode_str = effective_mode.lower()
    if mode_str not in ("remote", "local"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audit mode '{mode}'. Must be 'remote' or 'local'."
        )

    # Check loopback or unspecified
    is_unspecified = hostname_lower in ("0.0.0.0", "::")
    is_allowed_local = hostname_lower in ("localhost", "localhost.localdomain", "127.0.0.1", "::1")

    # Also resolve non-standard numeric representation if present
    parsed_ip = parse_numeric_ipv4(hostname_lower)
    if parsed_ip:
        try:
            ip_obj = ipaddress.ip_address(parsed_ip)
            if ip_obj.is_loopback:
                is_allowed_local = True
            elif ip_obj.is_unspecified:
                is_unspecified = True
        except ValueError:
            pass

    if not is_allowed_local and not is_unspecified:
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_loopback:
                is_allowed_local = True
            elif ip_obj.is_unspecified:
                is_unspecified = True
        except ValueError:
            pass

    is_loopback_or_unspecified = is_allowed_local or is_unspecified

    # Production Mode Enforcement
    if is_production:
        if mode_str == "local":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local audit mode is not allowed in production environment."
            )
        if is_loopback_or_unspecified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to localhost / loopback addresses is restricted."
            )

    # Development Mode Enforcement
    if mode_str == "local":
        if is_unspecified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="0.0.0.0 is not a supported Local Audit target. Use localhost or 127.0.0.1."
            )
        if not is_allowed_local:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Local audit mode only supports localhost or 127.0.0.1 targets."
            )
        return url

    # Remote Audit Mode Enforcement: Perform DNS resolution & IP check
    if is_loopback_or_unspecified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remote audit mode does not allow localhost targets."
        )

    resolved_ips = resolve_host_ips(hostname_lower)
    for ip_str in resolved_ips:
        if is_ip_prohibited(ip_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to private, loopback, link-local, or restricted network addresses is prohibited."
            )

    return url

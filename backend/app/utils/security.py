import ipaddress
import urllib.parse
from fastapi import HTTPException, status


def validate_and_sanitize_url(
    url: str,
    mode: str = "remote",
    is_production: bool = False,
    allow_localhost: bool = False
) -> str:
    """
    Validates that a URL is a well-formed HTTP/HTTPS URL and enforces mode-aware SSRF protections.
    
    Modes:
      - 'remote': Public websites only. Rejects loopback & private IP targets.
      - 'local': Controlled localhost / loopback targets only (dev environment only).
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL string is required."
        )
    
    url = url.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
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
    
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must contain a valid domain name or host IP."
        )
    
    hostname_lower = hostname.lower()

    # Legacy compatibility helper: allow_localhost=True sets mode to local if mode was default/remote
    if allow_localhost and (mode is None or mode == "remote"):
        effective_mode = "local"
    else:
        effective_mode = mode or "remote"

    # Validate audit mode parameter strictly
    mode_str = effective_mode.lower()
    if mode_str not in ("remote", "local"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audit mode '{mode}'. Must be 'remote' or 'local'."
        )

    # Detect unspecified target (0.0.0.0 or ::)
    is_unspecified = False
    if hostname_lower in ("0.0.0.0", "::"):
        is_unspecified = True
    else:
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_unspecified:
                is_unspecified = True
        except ValueError:
            pass

    # Detect allowed local target (localhost, 127.0.0.1, ::1)
    is_allowed_local = False
    if hostname_lower in ("localhost", "localhost.localdomain", "127.0.0.1", "::1"):
        is_allowed_local = True
    else:
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_loopback and not ip_obj.is_unspecified:
                is_allowed_local = True
        except ValueError:
            pass

    is_loopback_or_unspecified = is_allowed_local or is_unspecified

    # Production Environment Rules: Local mode & loopback/unspecified targets are strictly forbidden
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

    # Development Environment Rules
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
    else:  # mode_str == "remote"
        if is_loopback_or_unspecified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Remote audit mode does not allow localhost targets."
            )

    # Private IP non-loopback targets (192.168.x.x, 10.x.x.x, 172.16-31.x.x, 169.254.x.x) are ALWAYS restricted
    try:
        ip_obj = ipaddress.ip_address(hostname_lower)
        if not is_loopback_or_unspecified and (ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to private, loopback, or local IP addresses is restricted."
            )
    except ValueError:
        # Domain name target (e.g. example.com)
        pass

    return url


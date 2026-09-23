import ipaddress
import urllib.parse
from fastapi import HTTPException, status


def validate_and_sanitize_url(url: str, allow_localhost: bool = False) -> str:
    """
    Validates that a URL is a well-formed HTTP/HTTPS URL and enforces SSRF protections.
    
    - Must start with http:// or https://
    - Rejects non-HTTP schemes (file://, ftp://, etc.)
    - Rejects localhost, loopback addresses, and private IPv4/IPv6 ranges
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
    
    if not allow_localhost:
        # Check explicit localhost names
        if hostname_lower in ("localhost", "localhost.localdomain", "0.0.0.0"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access to localhost / loopback addresses is restricted."
            )
        
        # Check IP address targets
        try:
            ip_obj = ipaddress.ip_address(hostname_lower)
            if ip_obj.is_loopback or ip_obj.is_private or ip_obj.is_link_local or ip_obj.is_reserved or ip_obj.is_unspecified:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access to private, loopback, or local IP addresses is restricted."
                )
        except ValueError:
            # Not an IP address string, it's a domain name (e.g. example.com)
            pass

    return url

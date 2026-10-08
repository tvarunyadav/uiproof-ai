import time
import logging
import threading
from typing import Dict, List, Tuple, Optional
from fastapi import Request, HTTPException, status

logger = logging.getLogger("uiproof.rate_limiter")


class InMemoryRateLimiter:
    """
    Process-local, thread-safe sliding-window rate limiter for FastAPI.
    
    Limitations:
    - In-memory storage is process-local and resets upon process restart or container redeployment.
    - In multi-worker or multi-instance environments (e.g. Render multi-container deploys),
      rate limit state is not shared across workers without a centralized store (e.g. Redis).
    """

    def __init__(self, requests_per_minute: int = 20, cleanup_interval_sec: int = 300):
        self.limit = requests_per_minute
        self.window_sec = 60
        self.cleanup_interval = cleanup_interval_sec
        self._records: Dict[str, List[float]] = {}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _cleanup_old_records(self, now: float) -> None:
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now
        cutoff = now - self.window_sec
        expired_keys = []
        for key, timestamps in self._records.items():
            valid = [t for t in timestamps if t > cutoff]
            if valid:
                self._records[key] = valid
            else:
                expired_keys.append(key)
        for k in expired_keys:
            del self._records[k]

    def is_rate_limited(self, key: str, limit: Optional[int] = None) -> Tuple[bool, int]:
        max_requests = limit if limit is not None else self.limit
        now = time.time()
        cutoff = now - self.window_sec

        with self._lock:
            self._cleanup_old_records(now)
            timestamps = self._records.get(key, [])
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                oldest_in_window = valid_timestamps[0]
                retry_after = max(1, int(self.window_sec - (now - oldest_in_window)))
                self._records[key] = valid_timestamps
                return True, retry_after

            valid_timestamps.append(now)
            self._records[key] = valid_timestamps
            return False, 0


# Global instances for endpoint rate-limiting
auth_rate_limiter = InMemoryRateLimiter(requests_per_minute=10)
expensive_op_rate_limiter = InMemoryRateLimiter(requests_per_minute=10)


def extract_client_ip(request: Request) -> str:
    """
    Extracts the verified client IP address.
    Takes the rightmost IP in X-Forwarded-For (appended by trusted reverse proxy like Render)
    or falls back to direct connection socket peer host.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Split IPs appended by proxies; rightmost IP is appended by the outermost trusted edge proxy
        ips = [ip.strip() for ip in forwarded_for.split(",") if ip.strip()]
        if ips:
            return ips[-1]
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    return request.client.host if request.client else "unknown_ip"


def check_rate_limit(request: Request, limiter: InMemoryRateLimiter, limit: Optional[int] = None, key_prefix: str = "") -> None:
    client_ip = extract_client_ip(request)
    key = f"{key_prefix}:{client_ip}"
    is_limited, retry_after = limiter.is_rate_limited(key, limit=limit)

    if is_limited:
        logger.warning(f"Rate limit exceeded for key {key}. Retry after {retry_after}s.")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again later.",
            headers={"Retry-After": str(retry_after)}
        )

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def http_request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 30,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> requests.Response:
    """
    Small, deterministic retry wrapper for transient failures.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            resp = session.request(method, url, json=json, data=data, timeout=timeout_seconds)
            # Retry on 429/5xx
            if resp.status_code in (429, 500, 502, 503, 504):
                logger.warning("HTTP %s %s -> %s (attempt %s/%s)", method, url, resp.status_code, attempt, max_retries)
                if attempt < max_retries:
                    time.sleep(backoff_seconds * attempt)
                    continue
            return resp
        except Exception as e:
            last_exc = e
            logger.warning("HTTP %s %s exception (attempt %s/%s): %s", method, url, attempt, max_retries, e)
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Unreachable: http_request_with_retries")

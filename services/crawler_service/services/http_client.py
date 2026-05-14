"""HTTP fetch with retry + exponential backoff.

Wraps cloudscraper sessions so transient failures (timeouts, 5xx, rate limits)
don't kill a whole crawl run. Each crawler uses one PoliteHttpClient instance.
"""
import logging
import random
import time
from typing import Optional

import cloudscraper
import requests

logger = logging.getLogger(__name__)


# HTTP status codes we'll retry on. 403 is NOT here because Cloudflare 403
# means "blocked" — retrying immediately won't help (handled at adapter level).
_RETRY_STATUSES = {429, 500, 502, 503, 504}


class PoliteHttpClient:
    """cloudscraper-backed session with retry + jitter sleep between calls."""

    def __init__(
        self,
        extra_headers: Optional[dict] = None,
        max_retries: int = 3,
        backoff_base: float = 2.0,
        sleep_min: float = 3.0,
        sleep_max: float = 6.0,
        timeout: float = 20.0,
    ) -> None:
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "linux", "mobile": False}
        )
        if extra_headers:
            self.session.headers.update(extra_headers)
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.sleep_min = sleep_min
        self.sleep_max = sleep_max
        self.timeout = timeout

    def get(self, url: str, **kwargs) -> str:
        """Return response.text. Raises after all retries exhausted."""
        timeout = kwargs.pop("timeout", self.timeout)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=timeout, **kwargs)
                if resp.status_code in _RETRY_STATUSES:
                    raise requests.HTTPError(
                        f"{resp.status_code} retryable", response=resp
                    )
                resp.raise_for_status()
                return resp.text
            except (requests.RequestException, requests.HTTPError) as e:
                last_exc = e
                if attempt >= self.max_retries:
                    break
                backoff = self.backoff_base ** attempt + random.uniform(0, 1)
                logger.warning(
                    "fetch failed (attempt %d/%d) url=%s: %s — retry in %.1fs",
                    attempt, self.max_retries, url, e, backoff,
                )
                time.sleep(backoff)
        raise last_exc  # type: ignore[misc]

    def polite_sleep(self) -> None:
        """Sleep a random duration between request bursts to avoid rate limits."""
        time.sleep(random.uniform(self.sleep_min, self.sleep_max))

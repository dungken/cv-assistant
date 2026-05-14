"""Shared Selenium session for sites that require JS execution.

undetected-chromedriver bypasses Cloudflare's JS challenge that blocks
cloudscraper on TopCV detail pages. We keep a long-lived driver across
many detail fetches to amortize the Chrome startup cost (~3-5s).

Usage:
    with SeleniumSession() as sess:
        sess.warmup("https://www.topcv.vn/")  # set cookies once
        html = sess.fetch("https://www.topcv.vn/viec-lam/.../12345.html")
"""
import logging
import time
from contextlib import contextmanager
from typing import Optional

import undetected_chromedriver as uc

logger = logging.getLogger(__name__)


class SeleniumSession:
    def __init__(
        self,
        headless: bool = True,
        page_load_wait: float = 8.0,
        chrome_version: int = 147,
    ) -> None:
        self.page_load_wait = page_load_wait
        self.chrome_version = chrome_version
        self.headless = headless
        self.driver: Optional[uc.Chrome] = None

    def __enter__(self) -> "SeleniumSession":
        self._start()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _start(self) -> None:
        if self.driver is not None:
            return
        options = uc.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=vi-VN,vi,en-US,en")

        logger.info("Starting Chrome (headless=%s)…", self.headless)
        self.driver = uc.Chrome(
            options=options,
            version_main=self.chrome_version,
            headless=self.headless,
        )
        logger.info("Chrome ready")

    def warmup(self, homepage_url: str, wait: float = 3.0) -> None:
        """Visit homepage to obtain cookies for subsequent detail fetches."""
        if self.driver is None:
            self._start()
        logger.info("Warmup: %s", homepage_url)
        self.driver.get(homepage_url)
        time.sleep(wait)

    def fetch(self, url: str, wait: Optional[float] = None) -> str:
        """Load url, return rendered HTML. Empty string on failure.

        Handles Cloudflare 'Just a moment...' interstitial by polling the
        page title for up to `cf_max_wait` seconds. Once the challenge clears,
        the real page is auto-loaded and we capture its source.
        """
        if self.driver is None:
            self._start()
        wait = self.page_load_wait if wait is None else wait
        cf_max_wait = 30.0
        try:
            self.driver.get(url)
            time.sleep(wait)
            # Loop while Cloudflare interstitial is visible.
            deadline = time.time() + cf_max_wait
            while time.time() < deadline:
                title = (self.driver.title or "").lower()
                if "just a moment" not in title and "challenge" not in title:
                    break
                logger.debug("CF challenge in progress (title=%r)…", title)
                time.sleep(2.0)
            return self.driver.page_source
        except Exception as e:
            logger.warning("Selenium fetch failed url=%s: %s", url, e)
            return ""

    def close(self) -> None:
        if self.driver is None:
            return
        try:
            self.driver.quit()
        except Exception:
            pass
        self.driver = None

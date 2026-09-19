"""
browser.py — Generic browser loader for rendering modern web pages.

Uses Playwright (headless Chromium) to render JavaScript-heavy dynamic websites,
with clean resource lifecycle management and friendly error handling.
Also provides a fallback to requests for simple pages or if Playwright is unavailable.
"""
from __future__ import annotations

import logging
import os
import re
from urllib.parse import urlparse

import requests
import demo_site

logger = logging.getLogger(__name__)

# Standard browser user agent to avoid basic blocks on public sites
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


class BrowserFetchError(Exception):
    """User-friendly error when a page cannot be retrieved."""
    pass


def is_demo_url(url: str) -> bool:
    """Check if URL targets the internal demo endpoint."""
    if not url:
        return False
    u = url.lower()
    return "localhost" in u or "127.0.0.1" in u or "/demo/" in u


def fetch_html_requests(url: str, timeout: int = 15) -> str:
    """Fetch HTML using standard HTTP request."""
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": DEFAULT_USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.Timeout:
        raise BrowserFetchError(f"Connection timed out while loading {url}")
    except requests.exceptions.ConnectionError:
        raise BrowserFetchError(f"Could not connect to {url}. Please verify the URL is valid and accessible.")
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code if e.response else "Unknown"
        if code in (401, 403):
            raise BrowserFetchError(f"Website access restricted (HTTP {code}). Website could not be accessed automatically.")
        raise BrowserFetchError(f"HTTP Error {code} while loading {url}")
    except Exception as e:
        raise BrowserFetchError(f"Failed to fetch {url}: {str(e)}")


def fetch_html_playwright(url: str, timeout_seconds: int = 20) -> str:
    """Fetch and render HTML using Playwright headless Chromium."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        logger.warning("Playwright not installed, falling back to HTTP request loader.")
        return fetch_html_requests(url, timeout=timeout_seconds)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
            )
            page = context.new_page()

            # Set navigation timeout in milliseconds
            timeout_ms = timeout_seconds * 1000
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                # Wait briefly for dynamic elements or hydration
                try:
                    page.wait_for_load_state("networkidle", timeout=3000)
                except PlaywrightTimeout:
                    pass  # Network idle timeout is fine if DOM is already loaded

                html = page.content()
                return html
            finally:
                page.close()
                context.close()
                browser.close()

    except PlaywrightTimeout:
        raise BrowserFetchError(f"Page loading timed out after {timeout_seconds}s for {url}")
    except Exception as e:
        err_msg = str(e).lower()
        if "net::err_name_not_resolved" in err_msg or "net::err_connection_refused" in err_msg:
            raise BrowserFetchError(f"Cannot resolve host for {url}. Please check the URL.")
        if "access denied" in err_msg or "403" in err_msg or "challenge" in err_msg:
            raise BrowserFetchError("Website could not be accessed automatically (Access restricted/bot protection).")
        logger.warning("Playwright rendering failed (%s); trying HTTP request fallback.", e)
        return fetch_html_requests(url, timeout=timeout_seconds)


def get_rendered_html(url: str, timeout_seconds: int = 20) -> str:
    """
    Unified entry point to get rendered HTML for ANY URL.
    - If URL points to controlled demo site, returns current demo HTML immediately.
    - For all other URLs, uses the generic browser loader.
    """
    if not url or not url.strip():
        raise BrowserFetchError("No URL provided.")

    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    # Validate URL structure
    parsed = urlparse(url)
    if not parsed.netloc:
        raise BrowserFetchError(f"Invalid URL format: '{url}'")

    # Fast path for controlled demo site
    if is_demo_url(url):
        return demo_site.get_demo_html()

    # Generic browser loading for external websites
    return fetch_html_playwright(url, timeout_seconds=timeout_seconds)

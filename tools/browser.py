"""Controlled browser reading through Playwright.

The default path opens a fresh, isolated Chromium page. Existing personal
Chrome tabs are only readable when the user explicitly starts Chrome with a
local CDP endpoint (normally http://127.0.0.1:9222).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def _page_payload(page, max_chars: int, detail: str = "compact") -> dict:
    """Extract semantic content while dropping repeated browser chrome."""
    limit = max(1000, min(int(max_chars), 30000))
    data = page.evaluate("""() => {
      const clone = document.body.cloneNode(true);
      clone.querySelectorAll('script,style,noscript,template,nav,header,footer,aside,[role="navigation"],[aria-hidden="true"]').forEach((node) => node.remove());
      const root = clone.querySelector('main,article,[role="main"]') || clone;
      const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
      const text = Array.from(root.querySelectorAll('p,li,blockquote,pre,h1,h2,h3,h4')).map((node) => clean(node.innerText)).filter(Boolean);
      const unique = [...new Set(text)];
      const headings = [...root.querySelectorAll('h1,h2,h3')].map((node) => clean(node.innerText)).filter(Boolean).slice(0, 20);
      const links = [...root.querySelectorAll('a[href]')].map((node) => ({text: clean(node.innerText), url: node.href})).filter((item) => item.text).slice(0, 20);
      return {text: unique.join('\\n'), headings, links};
    }""")
    text = str(data.get("text", "")).strip()
    if detail == "full":
        return {"url": page.url, "title": page.title(), "text": text[:limit]}
    lines = text.splitlines()
    compact = "\n".join(line for line in lines if len(line) >= 2 and line not in lines[:lines.index(line)])
    result = {"url": page.url, "title": page.title()}
    if data.get("headings"):
        result["headings"] = data["headings"]
    if data.get("links"):
        result["links"] = data["links"]
    result["text"] = compact[:limit]
    return result


def _validate_url(url: str) -> str:
    value = str(url or "").strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL harus menggunakan http:// atau https://.")
    return value


def open_chrome(url: str) -> dict:
    """Open a URL in the user's installed Google Chrome application."""
    target = _validate_url(url)
    candidates = [
        shutil.which("chrome.exe"),
        str(Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"),
    ]
    executable = next((item for item in candidates if item and Path(item).exists()), None)
    if not executable:
        return {"success": False, "error": "Google Chrome tidak ditemukan. Gunakan read_webpage untuk browser terisolasi."}
    process = subprocess.Popen([executable, target], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return {"success": True, "pid": process.pid, "url": target, "application": "Google Chrome"}


def read_webpage(url: str, max_chars: int = 8000, detail: str = "compact") -> dict:
    """Open an isolated page and return compact semantic content by default."""
    target = _validate_url(url)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError("Playwright belum terpasang. Jalankan: pip install -r requirements.txt && python -m playwright install chromium") from error

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(target, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(500)
            return _page_payload(page, max_chars, detail)
        finally:
            browser.close()


def read_connected_chrome(cdp_url: str = "http://127.0.0.1:9222", max_chars: int = 8000, detail: str = "compact") -> dict:
    """Read the active page from a user-started Chrome CDP session.

    This deliberately does not start or attach to arbitrary desktop Chrome.
    Chrome must have been launched with --remote-debugging-port explicitly.
    """
    endpoint = str(cdp_url or "").strip().rstrip("/")
    if not endpoint.startswith("http://127.0.0.1:"):
        raise ValueError("CDP endpoint harus berada di http://127.0.0.1.")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        raise RuntimeError("Playwright belum terpasang. Jalankan: pip install -r requirements.txt && python -m playwright install chromium") from error

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(endpoint)
        pages = [page for context in browser.contexts for page in context.pages]
        if not pages:
            raise RuntimeError("Tidak ada tab Chrome yang tersedia pada CDP endpoint tersebut.")
        page = pages[-1]
        return _page_payload(page, max_chars, detail)


__all__ = ["open_chrome", "read_webpage", "read_connected_chrome"]

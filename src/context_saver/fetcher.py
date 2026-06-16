from __future__ import annotations

import httpx


def fetch_url_text(url: str, timeout: float = 30.0) -> str:
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.text

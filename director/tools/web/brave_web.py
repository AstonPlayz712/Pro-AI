"""
brave_web.py — Brave Search API backend.

Used when BRAVE_API_KEY is set and no Google CSE is configured.
Requires:  pip install requests beautifulsoup4

API docs: https://api.search.brave.com/app/documentation/web-search
"""

from __future__ import annotations

import logging

from director.tools.web.interface import (
    WebInterface,
    WebSearchResponse,
    WebSearchResult,
    WebFetchResponse,
)

logger = logging.getLogger(__name__)

BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveWebInterface(WebInterface):
    """Web search backed by the Brave Search API."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        try:
            import requests  # type: ignore
            headers = {
                "Accept":               "application/json",
                "Accept-Encoding":      "gzip",
                "X-Subscription-Token": self.api_key,
            }
            params = {
                "q":     query,
                "count": min(max_results, 20),
            }
            resp = requests.get(
                BRAVE_SEARCH_ENDPOINT,
                headers=headers,
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            web_items = (data.get("web") or {}).get("results", [])
            results = [
                WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                )
                for item in web_items[:max_results]
            ]
            return WebSearchResponse(query=query, results=results, raw={"provider": "brave"})
        except ImportError as exc:
            return WebSearchResponse(query=query, error=f"requests not installed: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("BraveWebInterface.search error: %s", exc)
            return WebSearchResponse(query=query, error=str(exc))

    def fetch(self, url: str) -> WebFetchResponse:
        try:
            import requests  # type: ignore
            from bs4 import BeautifulSoup  # type: ignore
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Pro-AI/1.0"})
            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            return WebFetchResponse(url=url, content=text[:8000], status=resp.status_code)
        except ImportError as exc:
            return WebFetchResponse(url=url, error=f"requests/bs4 not installed: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("BraveWebInterface.fetch error: %s", exc)
            return WebFetchResponse(url=url, error=str(exc))

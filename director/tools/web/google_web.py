"""
google_web.py — Google Programmable Search Engine backend.

Used when GOOGLE_API_KEY and GOOGLE_CSE_ID are both present.
Requires:  pip install requests beautifulsoup4
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

GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleWebInterface(WebInterface):
    """Web search backed by Google's Custom Search JSON API."""

    def __init__(self, api_key: str, cse_id: str) -> None:
        self.api_key = api_key
        self.cse_id  = cse_id

    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        try:
            import requests  # type: ignore
            params = {
                "key": self.api_key,
                "cx":  self.cse_id,
                "q":   query,
                "num": min(max_results, 10),
            }
            resp = requests.get(GOOGLE_CSE_ENDPOINT, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = [
                WebSearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    snippet=item.get("snippet", ""),
                )
                for item in data.get("items", [])
            ]
            return WebSearchResponse(query=query, results=results, raw={"provider": "google"})
        except ImportError as exc:
            return WebSearchResponse(query=query, error=f"requests not installed: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("GoogleWebInterface.search error: %s", exc)
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
            logger.exception("GoogleWebInterface.fetch error: %s", exc)
            return WebFetchResponse(url=url, error=str(exc))

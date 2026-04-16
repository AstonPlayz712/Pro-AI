"""
web/interface.py — Abstract interface for web search / lookup tools.

Concrete implementations (DuckDuckGo, Brave Search, Bing, etc.) must
subclass WebInterface and implement `search` and `fetch`.

The NullWebInterface is the default no-op used when no backend is configured.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------

@dataclass
class WebSearchResult:
    """A single result from a web search query."""
    title:   str = ""
    url:     str = ""
    snippet: str = ""


@dataclass
class WebSearchResponse:
    """Aggregated response from a `search` call."""
    query:   str                     = ""
    results: list[WebSearchResult]   = field(default_factory=list)
    raw:     dict[str, Any]          = field(default_factory=dict)
    error:   str | None              = None

    @property
    def top_snippet(self) -> str:
        """Return the first result's snippet, or empty string."""
        return self.results[0].snippet if self.results else ""


@dataclass
class WebFetchResponse:
    """Response from a `fetch` call (single URL)."""
    url:     str            = ""
    content: str            = ""
    status:  int            = 0
    error:   str | None     = None


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class WebInterface(ABC):
    """
    Abstract base for all web/search backends.

    Implement `search` (keyword query → list of results) and
    `fetch` (single URL → page text) in your concrete subclass.
    """

    @abstractmethod
    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        """
        Run a keyword search and return ranked results.

        Parameters
        ----------
        query       : Natural-language or keyword search string.
        max_results : Maximum number of results to return.
        """

    @abstractmethod
    def fetch(self, url: str) -> WebFetchResponse:
        """
        Fetch and return the textual content of a URL.

        Parameters
        ----------
        url : Fully-qualified URL to retrieve.
        """


# ---------------------------------------------------------------------------
# Null (no-op) implementation
# ---------------------------------------------------------------------------

class NullWebInterface(WebInterface):
    """
    No-op web backend.

    Used when no real search provider is configured.
    All calls return empty results without raising.
    """

    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        logger.debug("NullWebInterface.search — skipped: %s", query)
        return WebSearchResponse(query=query, error="No web backend configured.")

    def fetch(self, url: str) -> WebFetchResponse:
        logger.debug("NullWebInterface.fetch — skipped: %s", url)
        return WebFetchResponse(url=url, error="No web backend configured.")


# ---------------------------------------------------------------------------
# Example: DuckDuckGo implementation stub (requires duckduckgo-search)
# ---------------------------------------------------------------------------

class DuckDuckGoWebInterface(WebInterface):
    """
    Web search backed by DuckDuckGo (no API key required).

    Install:  pip install duckduckgo-search requests beautifulsoup4

    Example
    -------
    >>> from director.tools.web.interface import DuckDuckGoWebInterface
    >>> web = DuckDuckGoWebInterface()
    >>> resp = web.search("MacBook Pro 2010 SATA cable failure symptoms")
    >>> print(resp.results[0].snippet)
    """

    def search(self, query: str, max_results: int = 5) -> WebSearchResponse:
        try:
            from duckduckgo_search import DDGS  # type: ignore
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=max_results))
            results = [
                WebSearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
                for r in raw
            ]
            return WebSearchResponse(query=query, results=results, raw={"provider": "ddg"})
        except ImportError as exc:
            return WebSearchResponse(query=query, error=f"duckduckgo-search not installed: {exc}")
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("DuckDuckGoWebInterface.search error: %s", exc)
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
            logger.exception("DuckDuckGoWebInterface.fetch error: %s", exc)
            return WebFetchResponse(url=url, error=str(exc))

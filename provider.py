"""TinyFish Web Search & Extract Provider for Hermes Agent."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

import httpx

try:
    from agent.web_search_provider import WebSearchProvider
except ImportError:
    # Graceful fallback when imported outside of the Hermes agent core
    class WebSearchProvider:  # type: ignore[no-redef]
        """Fallback ABC mirroring agent.web_search_provider.WebSearchProvider."""

        @property
        def name(self) -> str:
            raise NotImplementedError

        @property
        def display_name(self) -> str:
            return self.name

        def is_available(self) -> bool:
            raise NotImplementedError

        def supports_search(self) -> bool:
            return True

        def supports_extract(self) -> bool:
            return False

        def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
            raise NotImplementedError

        def extract(self, urls: List[str], **kwargs: Any) -> Dict[str, Any]:
            raise NotImplementedError


logger = logging.getLogger(__name__)


class TinyFishWebSearchProvider(WebSearchProvider):
    """Web search and extraction provider powered by TinyFish AI."""

    SEARCH_API_URL = "https://api.search.tinyfish.ai"
    FETCH_API_URL = "https://api.fetch.tinyfish.ai"
    DEFAULT_TIMEOUT = 15.0

    @property
    def name(self) -> str:
        """Stable provider ID for Hermes config (web.backend / web.search_backend)."""
        return "tinyfish"

    @property
    def display_name(self) -> str:
        """Human-readable name shown in `hermes tools` UI."""
        return "TinyFish"

    def is_available(self) -> bool:
        """Cheap availability check.

        Must not make network calls because it runs on every `hermes tools` paint loop.
        """
        return bool(os.getenv("TINYFISH_API_KEY", "").strip())

    def supports_search(self) -> bool:
        """Enables routing for Hermes `web_search` tool."""
        return True

    def supports_extract(self) -> bool:
        """Enables routing for Hermes `web_extract` tool."""
        return True

    def _get_api_key(self) -> str:
        api_key = os.getenv("TINYFISH_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "TINYFISH_API_KEY is not set. Please set it in ~/.hermes/.env or your environment."
            )
        return api_key

    def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Perform web search via TinyFish Search API and return Hermes response envelope."""
        clean_query = (query or "").strip()
        if not clean_query:
            return {"success": False, "error": "Search query cannot be empty"}

        try:
            api_key = self._get_api_key()
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        count = max(1, min(int(limit), 20))
        headers = {
            "X-API-Key": api_key,
            "Accept": "application/json",
            "User-Agent": "hermes-agent-plugin/tinyfish-web",
        }
        params = {
            "query": clean_query,
        }

        try:
            with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
                response = client.get(self.SEARCH_API_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            msg = exc.response.text[:200]
            logger.error("TinyFish Search HTTP %d: %s", status, msg)
            if status == 401 or status == 403:
                return {
                    "success": False,
                    "error": f"TinyFish authentication failed (HTTP {status}): Invalid or missing API key.",
                }
            return {
                "success": False,
                "error": f"TinyFish Search API error (HTTP {status}): {msg}",
            }
        except httpx.RequestError as exc:
            logger.error("TinyFish Search request failed: %s", exc)
            return {"success": False, "error": f"TinyFish network request failed: {exc}"}
        except Exception as exc:
            logger.error("Unexpected error in TinyFish search: %s", exc)
            return {"success": False, "error": f"Unexpected error during search: {exc}"}

        # Map TinyFish results into standard Hermes search envelope
        raw_results = data.get("results", []) if isinstance(data, dict) else []
        formatted_results = []
        for idx, item in enumerate(raw_results[:count]):
            if not isinstance(item, dict):
                continue
            formatted_results.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("snippet", "") or item.get("description", ""),
                    "position": item.get("position", idx + 1),
                }
            )

        return {
            "success": True,
            "data": {
                "web": formatted_results,
            },
        }

    def extract(self, urls: List[str], **kwargs: Any) -> Dict[str, Any]:
        """Fetch and extract clean markdown content from URLs via TinyFish Fetch API."""
        if not urls:
            return {"success": False, "error": "No URLs provided for extraction"}

        try:
            api_key = self._get_api_key()
        except ValueError as exc:
            return {"success": False, "error": str(exc)}

        # Cap URLs at 10 as per TinyFish API specification
        target_urls = [u.strip() for u in urls if isinstance(u, str) and u.strip()][:10]
        if not target_urls:
            return {"success": False, "error": "No valid URLs provided"}

        headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "hermes-agent-plugin/tinyfish-web",
        }
        payload = {
            "urls": target_urls,
            "format": "markdown",
        }

        try:
            with httpx.Client(timeout=self.DEFAULT_TIMEOUT) as client:
                response = client.post(self.FETCH_API_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            msg = exc.response.text[:200]
            logger.error("TinyFish Fetch HTTP %d: %s", status, msg)
            if status == 401 or status == 403:
                return {
                    "success": False,
                    "error": f"TinyFish authentication failed (HTTP {status}): Invalid or missing API key.",
                }
            return {
                "success": False,
                "error": f"TinyFish Fetch API error (HTTP {status}): {msg}",
            }
        except httpx.RequestError as exc:
            logger.error("TinyFish Fetch request failed: %s", exc)
            return {"success": False, "error": f"TinyFish network request failed: {exc}"}
        except Exception as exc:
            logger.error("Unexpected error in TinyFish extract: %s", exc)
            return {"success": False, "error": f"Unexpected error during extraction: {exc}"}

        # Map TinyFish results into standard Hermes extract envelope
        raw_results = data.get("results", []) if isinstance(data, dict) else []
        errors = data.get("errors", []) if isinstance(data, dict) else []

        formatted_pages = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            text_content = item.get("text", "") or item.get("markdown", "")
            formatted_pages.append(
                {
                    "url": item.get("final_url") or item.get("url", ""),
                    "title": item.get("title", ""),
                    "content": text_content,
                    "raw_content": text_content,
                    "metadata": {
                        "site_name": item.get("site_name", ""),
                        "description": item.get("description", ""),
                    },
                }
            )

        # Include any per-URL error entries if present
        for err_item in errors:
            if isinstance(err_item, dict):
                formatted_pages.append(
                    {
                        "url": err_item.get("url", ""),
                        "title": "",
                        "content": "",
                        "raw_content": "",
                        "error": err_item.get("error", "Failed to extract content"),
                    }
                )

        return {
            "success": True,
            "data": formatted_pages,
        }


def register(ctx: Any) -> None:
    """Plugin entry point registered with Hermes Agent."""
    provider = TinyFishWebSearchProvider()
    ctx.register_web_search_provider(provider)
    logger.info("Registered TinyFish Web Search Provider (%s)", provider.name)


"""TinyFish Web Search & Extract plugin entry point for Hermes Agent."""

from __future__ import annotations

import logging

try:
    from .provider import TinyFishWebSearchProvider
except ImportError:
    from provider import TinyFishWebSearchProvider

logger = logging.getLogger(__name__)


def register(ctx) -> None:
    """Invoked once at Hermes startup to register backend providers."""
    provider = TinyFishWebSearchProvider()
    ctx.register_web_search_provider(provider)
    logger.info("Registered TinyFish Web Search Provider (%s)", provider.name)


__all__ = ["register", "TinyFishWebSearchProvider"]

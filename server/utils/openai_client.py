"""
Centralized OpenAI client factory.

Provides a single source for creating OpenAI clients with consistent
configuration across the application.
"""

from openai import AsyncOpenAI, OpenAI
from httpx import Timeout
from server.config import settings


def _client_kwargs() -> dict:
    """Shared kwargs for sync and async clients."""
    kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    
    # Set timeout for HTTP requests (connect, read, write, pool timeouts)
    # Using a longer timeout for streaming responses
    kwargs["timeout"] = Timeout(
        timeout=settings.streaming_timeout_seconds,
        connect=60.0,
        read=settings.streaming_timeout_seconds,
        write=60.0,
        pool=60.0
    )
    return kwargs


def create_openai_client() -> OpenAI:
    """
    Create an OpenAI client with settings from config.

    Treats empty or None base_url as optional - SDK will use default endpoint.
    Non-empty base_url is passed for Azure/proxy configurations.

    Returns:
        OpenAI: Configured OpenAI client instance
    """
    return OpenAI(**_client_kwargs())


def create_async_openai_client() -> AsyncOpenAI:
    """Create an async OpenAI client (e.g. for streaming)."""
    return AsyncOpenAI(**_client_kwargs())

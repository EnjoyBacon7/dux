"""
Centralized OpenAI client factory.

Provides a single source for creating OpenAI clients with consistent
configuration across the application.
"""

from openai import OpenAI
from server.config import settings


def create_openai_client() -> OpenAI:
    """
    Create an OpenAI client with settings from config.

    Treats empty or None base_url as optional - SDK will use default endpoint.
    Non-empty base_url is passed for Azure/proxy configurations.

    Returns:
        OpenAI: Configured OpenAI client instance
    """
    kwargs = {"api_key": settings.openai_api_key}
    
    # Only set base_url if it's provided and non-empty
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    
    return OpenAI(**kwargs)

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

    Returns:
        OpenAI: Configured OpenAI client instance
    """
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

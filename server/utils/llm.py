"""
Unified LLM calling interface.

Provides a consistent way to make LLM calls across the application,
handling client initialization, error handling, JSON parsing, and response extraction.
"""

import json
import logging
from typing import Optional, Dict, Any, List, Union
from openai import OpenAI

from server.config import settings
from server.utils.openai_client import create_openai_client

logger = logging.getLogger(__name__)


# ============================================================================
# Response Extraction and Parsing Utilities
# ============================================================================


def extract_response_content(choice: Any) -> str:
    """
    Extract content from API response choice, handling reasoning models.

    Args:
        choice: Response choice object from OpenAI API

    Returns:
        str: Extracted content

    Raises:
        ValueError: If no valid content found in response
    """
    content = choice.message.content

    # Handle reasoning models that put content in reasoning_content
    if content is None:
        if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
            content = choice.message.reasoning_content
            logger.info("Using reasoning_content from message")
        elif hasattr(choice, 'provider_specific_fields'):
            fields = choice.provider_specific_fields
            if isinstance(fields, dict) and 'reasoning_content' in fields:
                content = fields['reasoning_content']
                logger.info("Using reasoning_content from provider_specific_fields")

        if content is None:
            logger.error(f"Content is None. Finish reason: {choice.finish_reason}")
            if choice.finish_reason == "length":
                raise ValueError(
                    "Response was cut off due to max_tokens limit. Try increasing max_tokens or shortening your query."
                )
            elif choice.finish_reason == "content_filter":
                raise ValueError("Response was filtered by content policy")
            else:
                raise ValueError(f"No content in response (finish_reason: {choice.finish_reason})")

    if not content:
        raise ValueError("Empty response from LLM")

    return content


def parse_json_response(content: str, json_array: bool = False) -> Union[Dict[str, Any], List[Any]]:
    """
    Parse JSON from LLM response, extracting JSON from surrounding text if needed.

    Args:
        content: Response content string
        json_array: Whether to extract JSON array (vs object)

    Returns:
        Parsed JSON object or array

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        if json_array:
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
        else:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {content}")
        raise ValueError(f"Invalid JSON in LLM response: {str(e)}")


def build_usage_dict(response: Any) -> Dict[str, int]:
    """Build usage statistics dictionary from API response."""
    return {
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens
    }


# ============================================================================
# Core LLM Call Functions
# ============================================================================


def call_llm_sync(
    prompt: str,
    system_content: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    parse_json: bool = False,
    json_array: bool = False,
    model: Optional[str] = None,
    response_format: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Synchronous LLM call (blocking operation for thread pool).

    This is the core blocking operation that should run in a thread pool
    to avoid blocking the event loop.

    Args:
        prompt: User message content
        system_content: System message content
        temperature: Model temperature (0.0-2.0, default: 0.7)
        max_tokens: Maximum tokens for response (default: 2000)
        parse_json: Whether to parse response as JSON (default: False)
        json_array: Whether to extract JSON array vs object (default: False)
        model: Optional model override (defaults to settings.openai_model)
        response_format: Optional response format spec (e.g., {"type": "json_object"})

    Returns:
        dict: Response data with keys:
        - data: Parsed response (dict/list if parse_json=True, else str)
        - usage: Token usage statistics
        - model: Model used

    Raises:
        ValueError: If LLM call fails or response is invalid
    """
    model = model or settings.openai_model
    client = create_openai_client()

    try:
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)

        # Extract content
        content = extract_response_content(response.choices[0])

        # Parse JSON if requested
        if parse_json:
            data = parse_json_response(content, json_array=json_array)
        else:
            data = content

        return {
            "data": data,
            "usage": build_usage_dict(response),
            "model": response.model,
        }

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"LLM call failed: {str(e)}")
        raise ValueError(f"LLM call failed: {str(e)}")


async def call_llm_async(
    prompt: str,
    system_content: str,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    parse_json: bool = False,
    json_array: bool = False,
    model: Optional[str] = None,
    response_format: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Asynchronous LLM call (runs sync function in thread pool).

    This is the async wrapper that can be used in async contexts.
    It runs the blocking LLM call in a thread pool.

    Args:
        prompt: User message content
        system_content: System message content
        temperature: Model temperature (0.0-2.0, default: 0.7)
        max_tokens: Maximum tokens for response (default: 2000)
        parse_json: Whether to parse response as JSON (default: False)
        json_array: Whether to extract JSON array vs object (default: False)
        model: Optional model override (defaults to settings.openai_model)
        response_format: Optional response format spec (e.g., {"type": "json_object"})

    Returns:
        dict: Response data with keys:
        - data: Parsed response (dict/list if parse_json=True, else str)
        - usage: Token usage statistics
        - model: Model used

    Raises:
        ValueError: If LLM call fails or response is invalid
    """
    from server.thread_pool import run_blocking_in_executor

    return await run_blocking_in_executor(
        call_llm_sync,
        prompt,
        system_content,
        temperature,
        max_tokens,
        parse_json,
        json_array,
        model,
        response_format,
    )

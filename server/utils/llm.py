"""
Unified LLM calling interface.

Provides a consistent way to make LLM calls across the application,
handling client initialization, error handling, JSON parsing, and response extraction.
"""

import json
import logging
import base64
from io import BytesIO
from typing import AsyncIterator, Optional, Dict, Any, List, Union, TYPE_CHECKING
from openai import APIError, OpenAI

from server.config import settings
from server.utils.openai_client import create_openai_client, create_async_openai_client

if TYPE_CHECKING:
    from PIL import Image

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
        # Redact content to avoid PII leakage in logs
        content_preview = content[:200] + "…" if len(content) > 200 else content
        logger.error(
            f"Failed to parse JSON response. "
            f"Content length: {len(content)} chars. "
            f"Preview: {content_preview}. "
            f"Error: {str(e)}"
        )
        raise ValueError(f"Invalid JSON in LLM response: {str(e)}")


def build_usage_dict(response: Any) -> Dict[str, int]:
    """Build usage statistics dictionary from API response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.warning("LLM response missing usage; defaulting token counts to zero.")
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }


# ============================================================================
# VLM Helper Functions
# ============================================================================


def create_vlm_client() -> OpenAI:
    """Create VLM client with settings from config"""
    if not settings.vlm_api_key:
        raise ValueError("VLM API key not configured. Set VLM_API_KEY in environment variables.")
    if not settings.vlm_base_url:
        raise ValueError("VLM base URL not configured. Set VLM_BASE_URL in environment variables.")
    
    return OpenAI(
        api_key=settings.vlm_api_key,
        base_url=settings.vlm_base_url,
    )


def image_to_base64(image: "Image.Image") -> str:
    """
    Convert PIL Image to base64-encoded string for API transmission.
    
    Args:
        image: PIL Image object
        
    Returns:
        Base64-encoded string (data URL format)
    """
    from PIL import Image as PILImage
    
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


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
    vlm_request: Optional[Dict[str, Any]] = None,
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
        vlm_request: Optional VLM request dict with keys:
            - images: List of PIL Image objects
            - use_vlm_client: Whether to use VLM client (default: True)

    Returns:
        dict: Response data with keys:
        - data: Parsed response (dict/list if parse_json=True, else str)
        - usage: Token usage statistics
        - model: Model used

    Raises:
        ValueError: If LLM call fails or response is invalid
    """
    # Handle VLM requests
    if vlm_request and vlm_request.get("images"):
        use_vlm_client = vlm_request.get("use_vlm_client", True)
        images = vlm_request["images"]
        
        # Use VLM client and model if specified
        if use_vlm_client:
            model = model or settings.vlm_model
            client = create_vlm_client()
        else:
            model = model or settings.openai_model
            client = create_openai_client()
        
        # Prepare image content for API
        image_contents = [
            {"type": "image_url", "image_url": {"url": image_to_base64(img)}}
            for img in images
        ]
        
        # Build user message with text and images
        user_content = [
            {"type": "text", "text": prompt},
            *image_contents
        ]
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]
    else:
        # Standard text-only LLM request
        model = model or settings.openai_model
        client = create_openai_client()
        
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ]

    try:
        kwargs = {
            "model": model,
            "messages": messages,
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
    vlm_request: Optional[Dict[str, Any]] = None,
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
        vlm_request: Optional VLM request dict with keys:
            - images: List of PIL Image objects
            - use_vlm_client: Whether to use VLM client (default: True)

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
        vlm_request,
    )


def call_llm_messages_sync(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """
    Synchronous LLM call with a full list of messages (for chat with history).
    Each message must have "role" ("system" | "user" | "assistant") and "content" (str).
    """
    model = model or settings.openai_model
    client = create_openai_client()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = extract_response_content(response.choices[0])
        return {
            "data": content,
            "usage": build_usage_dict(response),
            "model": response.model,
        }
    except ValueError:
        raise
    except Exception as e:
        logger.exception("LLM call failed")
        raise ValueError("LLM call failed") from e


async def call_llm_messages_async(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    model: Optional[str] = None,
) -> dict[str, Any]:
    """Async wrapper for call_llm_messages_sync (runs in thread pool)."""
    from server.thread_pool import run_blocking_in_executor
    return await run_blocking_in_executor(
        call_llm_messages_sync,
        messages,
        temperature,
        max_tokens,
        model,
    )


async def stream_llm_messages_async(
    messages: list[dict[str, str]],
    temperature: float = 0.7,
    max_tokens: int = 2000,
    model: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Async generator that yields content chunks from a streaming LLM call.
    Yields str chunks; use for SSE or other streaming responses.
    """
    model = model or settings.openai_model
    client = create_async_openai_client()
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta is not None:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
    except APIError as e:
        logger.exception("LLM stream failed")
        raise ValueError("LLM stream failed") from e
    except Exception as e:
        logger.exception("LLM stream failed")
        raise
    finally:
        await client.close()

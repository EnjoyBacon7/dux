"""
Thread pool utilities for handling blocking operations in async context.

Provides thread pool executors for running blocking operations (France Travail API calls,
LLM requests) without blocking the main event loop, allowing other clients to continue
accessing the application.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

# Thread pool for blocking I/O operations
# Using max_workers to prevent resource exhaustion
_blocking_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="blocking_io_")

T = TypeVar('T')


def run_in_thread_pool(func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a blocking function in a thread pool and wait for result.

    This is a synchronous wrapper that blocks the calling thread but doesn't
    block the event loop. Use this in sync functions that need to call blocking I/O.

    Args:
        func: Blocking function to execute
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        Exception: Any exception raised by func
    """
    try:
        loop = asyncio.get_event_loop()
        # If we're in the main thread, use run_coroutine_threadsafe
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(
                asyncio.to_thread(func, *args, **kwargs),
                loop
            )
            return future.result()
        else:
            # If loop is not running, we're in a thread, just call directly
            return func(*args, **kwargs)
    except RuntimeError:
        # No event loop in this thread, call directly
        return func(*args, **kwargs)


async def run_blocking_in_executor(func: Callable[..., T], *args, **kwargs) -> T:
    """
    Run a blocking function asynchronously using thread pool.

    This is an async wrapper that allows blocking I/O to run without blocking
    the event loop. Use this in async functions.

    Args:
        func: Blocking function to execute
        *args: Positional arguments to pass to func
        **kwargs: Keyword arguments to pass to func

    Returns:
        Result from func

    Raises:
        Exception: Any exception raised by func
    """
    loop = asyncio.get_event_loop()
    try:
        # Use to_thread for Python 3.9+
        if hasattr(asyncio, 'to_thread'):
            return await asyncio.to_thread(func, *args, **kwargs)
        else:
            # Fallback for Python 3.8
            return await loop.run_in_executor(_blocking_executor, func, *args, **kwargs)
    except Exception as e:
        logger.error(f"Error running blocking function in executor: {str(e)}", exc_info=True)
        raise


def shutdown_thread_pool():
    """Shutdown the thread pool executor gracefully."""
    try:
        _blocking_executor.shutdown(wait=True, timeout=10)
        logger.info("Thread pool executor shutdown complete")
    except Exception as e:
        logger.error(f"Error shutting down thread pool: {str(e)}")

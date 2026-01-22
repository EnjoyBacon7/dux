"""
Main API router for the application.

Aggregates all specialized routers (chat, profile, jobs) and provides
general endpoints like health checks.
"""

import logging
import time
from typing import Dict, Any
from fastapi import APIRouter

from server.routers import chat_router, profile_router, jobs_router, cv_router, metiers_router
from server.thread_pool import run_blocking_in_executor

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================================
# Router Registration
# ============================================================================

# Include all specialized routers
router.include_router(chat_router.router)
router.include_router(profile_router.router)
router.include_router(jobs_router.router)
router.include_router(cv_router.router)
router.include_router(metiers_router.router)


# ============================================================================
# General Endpoints
# ============================================================================


@router.get("/healthcheck", tags=["General"], summary="Health check endpoint")
async def healthcheck() -> Dict[str, str]:
    """
    Simple healthcheck endpoint to verify the API is running.

    This endpoint can be used by load balancers, monitoring services,
    or frontend applications to verify API availability.

    Returns:
        dict: Status message with "healthy" status
    """
    return {"status": "healthy"}


@router.get("/test/block-indefinitely", tags=["Testing"], summary="Test blocking endpoint (indefinite)")
async def test_block_indefinitely(duration: int = 300) -> Dict[str, Any]:
    """
    Test endpoint that blocks indefinitely in thread pool.

    This endpoint is useful for testing that the thread pool prevents blocking
    the event loop. While this endpoint is processing, other clients should still
    be able to access the API.

    Call /healthcheck in another terminal/client while this is running to verify
    other requests are not blocked.

    Args:
        duration: How long to block in seconds (default: 300 = 5 minutes)

    Returns:
        dict: Confirmation message with elapsed time
    """
    def blocking_operation(seconds: int) -> Dict[str, Any]:
        """Simulate indefinite blocking operation."""
        start = time.time()
        time.sleep(seconds)
        elapsed = time.time() - start
        return {
            "blocked_for_seconds": elapsed,
            "message": f"Successfully blocked for {elapsed:.1f} seconds in thread pool"
        }

    # Run blocking operation in thread pool so event loop stays free
    result = await run_blocking_in_executor(blocking_operation, duration)
    return result

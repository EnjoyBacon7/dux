"""
Main API router for the application.

Aggregates all specialized routers (chat, profile, jobs) and provides
general endpoints like health checks.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter

from server.routers import chat_router, profile_router, jobs_router, cv_router

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

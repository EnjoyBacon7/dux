import logging

from fastapi import APIRouter
from server.routers import chat_router, profile_router, jobs_router

router = APIRouter(tags=["General"])
logger = logging.getLogger(__name__)

# Include all specialized routers
router.include_router(chat_router.router)
router.include_router(profile_router.router)
router.include_router(jobs_router.router)


@router.get("/healthcheck", summary="Health check endpoint")
async def healthcheck() -> dict:
    """
    Simple healthcheck endpoint to verify the API is running.

    Returns:
        dict: Status message
    """
    return {"status": "healthy"}

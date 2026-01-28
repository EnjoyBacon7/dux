"""
Chat and LLM-based analysis router.

Provides endpoints for CV analysis, France Travail parameter identification,
and job offer ranking using AI/LLM services.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import User, OptimalOffer
from server.utils.dependencies import get_current_user

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request Models
# ============================================================================
# (Deprecated models removed - endpoints now use read-only GET only)


# ============================================================================
# Helper Functions
# ============================================================================



# ============================================================================
# Profile Matching Endpoints
# ============================================================================


@router.get("/optimal_offers", summary="Get user's cached optimal offers (read-only)")
async def get_optimal_offers(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retrieve optimal offers from cache (does NOT trigger generation).

    Returns empty array if no offers exist or CV not uploaded.
    This endpoint ONLY reads from database - it does not search,
    rank, or generate new offers.

    Args:
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: List of optimal offers with metadata
    """
    if not current_user.cv_text:
        return {"success": True, "offers": []}

    optimal_offers = db.query(OptimalOffer).filter(
        OptimalOffer.user_id == current_user.id
    ).order_by(OptimalOffer.position).all()

    offers_data = []
    for offer in optimal_offers:
        offers_data.append({
            "job_id": offer.job_id,
            "position": offer.position,
            "score": offer.score,
            "match_reasons": offer.match_reasons,
            "concerns": offer.concerns,
        })

    return {
        "success": True,
        "offers": offers_data,
        "count": len(offers_data)
    }




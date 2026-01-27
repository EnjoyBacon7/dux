"""
Chat and LLM-based analysis router.

Provides endpoints for CV analysis, France Travail parameter identification,
and job offer ranking using AI/LLM services.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.methods.chat import identify_ft_parameters, rank_job_offers
from server.methods.FT_job_search import search_france_travail
from server.database import get_db_session
from server.models import User, OptimalOffer
from server.dependencies import get_current_user
from server.thread_pool import run_blocking_in_executor

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request Models
# ============================================================================


class ProfileMatchRequest(BaseModel):
    """Request body for profile matching endpoint."""
    query: Optional[str] = None


class FTParametersRequest(BaseModel):
    """Request body for France Travail parameters identification endpoint."""
    preferences: Optional[str] = None


class OptimalOffersRequest(BaseModel):
    """Request body for optimal job offers ranking endpoint."""
    ft_parameters: Optional[dict] = None
    preferences: Optional[str] = None
    top_k: int = 5


# ============================================================================
# Helper Functions
# ============================================================================


def _check_user_cv(current_user: User) -> None:
    """
    Validate that user has uploaded a CV.

    Args:
        current_user: The current user to check

    Raises:
        HTTPException: If user has no CV uploaded
    """
    if not current_user.cv_text:
        raise HTTPException(
            status_code=400,
            detail="No CV found. Please upload a CV first."
        )


async def _get_optimal_offers_with_cache(
    current_user: User,
    db: Session,
    ft_parameters: dict,
    preferences: Optional[str] = None,
    top_k: int = 5,
    cache_hours: int = 24
) -> Dict[str, Any]:
    """
    Get optimal job offers, using cache if available and fresh.

    Checks if cached offers exist and are less than cache_hours old.
    If cache is valid, returns cached results. Otherwise, fetches new offers
    from France Travail API, ranks them with LLM, and saves to database.

    Args:
        current_user: Current authenticated user
        db: Database session
        ft_parameters: France Travail search parameters
        preferences: Optional user preferences for ranking
        top_k: Number of top offers to return
        cache_hours: Number of hours before cache is considered stale

    Returns:
        dict: Ranked job offers with match scores, reasoning, and cache status

    Raises:
        ValueError: If no offers found
        Exception: If ranking or database operations fail
    """
    # Check cache first
    try:
        cached_offers = db.query(OptimalOffer).filter(
            OptimalOffer.user_id == current_user.id
        ).order_by(OptimalOffer.position).all()

        if cached_offers:
            # Check if cache is fresh
            most_recent = max(cached_offers, key=lambda o: o.updated_at or o.created_at)
            last_updated = most_recent.updated_at or most_recent.created_at
            cache_age = datetime.now(last_updated.tzinfo) - last_updated

            if cache_age < timedelta(hours=cache_hours):
                # Cache is fresh, return cached results
                # Return offers with job_id for frontend to fetch full data
                offers_data = []
                for o in cached_offers:
                    offer_dict = {
                        "job_id": o.job_id,
                        "position": o.position,
                        "score": o.score,
                        "match_reasons": o.match_reasons,
                        "concerns": o.concerns,
                    }
                    offers_data.append(offer_dict)

                return {
                    "success": True,
                    "offers": offers_data,
                    "count": len(offers_data),
                    "cached": True,
                    "cache_age_hours": round(cache_age.total_seconds() / 3600, 1)
                }
    except Exception as e:
        logger.warning(f"Error checking cache: {str(e)}, proceeding with fresh search")

    # Cache is stale or missing, fetch new offers in thread pool
    # Run France Travail API call in thread pool to avoid blocking other clients
    offers = await run_blocking_in_executor(
        search_france_travail,
        ft_parameters or {},
        50
    )

    if not offers:
        raise ValueError("No job offers found from France Travail API with the provided parameters")

    # Rank the offers using LLM (also in thread pool)
    result = await rank_job_offers(
        current_user.cv_text,
        offers,
        preferences=preferences,
        top_k=top_k
    )

    # Save optimal offers to database (delete old ones first)
    db.query(OptimalOffer).filter(OptimalOffer.user_id == current_user.id).delete()

    ranked_offers = result.get("ranked_offers", [])
    # Map ranked offers to get job IDs from full job data using position (1-indexed)
    offers_with_data = []
    for offer in ranked_offers:
        position = offer.get("position", 0)
        # Position is 1-indexed, so subtract 1 to get the correct offer from the list
        job_data = offers[position - 1] if 0 < position <= len(offers) else None
        job_id = job_data.get("id") if job_data else None

        db_offer = OptimalOffer(
            user_id=current_user.id,
            position=position,
            job_id=job_id,
            score=offer.get("score", 0),
            match_reasons=offer.get("match_reasons", []),
            concerns=offer.get("concerns", []),
        )
        db.add(db_offer)

        # Build simplified OptimalOffer for response
        offer_with_data = {
            "job_id": job_id,
            "position": position,
            "score": offer.get("score", 0),
            "match_reasons": offer.get("match_reasons", []),
            "concerns": offer.get("concerns", []),
        }
        offers_with_data.append(offer_with_data)

    db.commit()

    # Add cache status and offers to result
    result["cached"] = False
    result["offers"] = offers_with_data

    return result


# ============================================================================
# Profile Matching Endpoints
# ============================================================================


@router.post("/match_profile", summary="Match profile and return optimal offers")
async def match_profile_endpoint(
    request: Request,
    data: ProfileMatchRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Identify search parameters and return optimal offers (using cache if available).

    Orchestrates two operations:
    1. Checks cache first - if fresh cached offers exist, skip LLM parameter identification
    2. If cache is stale/missing, identifies France Travail search parameters from CV
    3. Gets optimal offers (from cache or fresh search and ranking)

    Args:
        request: FastAPI request object
        data: ProfileMatchRequest with optional user query
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: France Travail parameters and optimal offers (cached or fresh)

    Raises:
        HTTPException: If CV not found, validation fails, or offer lookup fails
    """
    _check_user_cv(current_user)

    try:
        ft_result = await identify_ft_parameters(
            current_user.cv_text,
            preferences=data.query
        )
        ft_parameters = ft_result.get("parameters", {})

        offers_result = await _get_optimal_offers_with_cache(
            current_user=current_user,
            db=db,
            ft_parameters=ft_parameters,
            preferences=data.query,
            top_k=5,
            cache_hours=24
        )

        return {
            "success": True,
            "ft_parameters": ft_parameters,
            "offers": offers_result.get("offers", []),
            "cached": offers_result.get("cached", False),
            "cache_age_hours": offers_result.get("cache_age_hours"),
            "total_offers_analyzed": offers_result.get("total_offers_analyzed"),
            "top_offers_returned": offers_result.get("top_offers_returned"),
            "model": offers_result.get("model"),
            "usage": {
                "ft_parameters": ft_result.get("usage"),
                "ranking": offers_result.get("usage")
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in profile matching: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile matching failed")


# ============================================================================
# France Travail API Endpoints
# ============================================================================


@router.post("/FT_parameters_identification", summary="Identify France Travail API search parameters")
async def ft_parameters_identification_endpoint(
    request: Request,
    data: FTParametersRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Identify optimal France Travail API search parameters based on user's CV.

    Uses the extracted CV text and user preferences to generate optimized
    search parameters for the France Travail job search API.

    Args:
        request: FastAPI request object
        data: FTParametersRequest with optional user preferences
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Identified search parameters and usage information

    Raises:
        HTTPException: If CV not found, validation fails, or LLM call fails
    """
    _check_user_cv(current_user)

    try:
        result = await identify_ft_parameters(
            current_user.cv_text,
            preferences=data.preferences
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in FT parameters identification: {str(e)}")
        raise HTTPException(status_code=500, detail="FT parameters identification failed")


# ============================================================================
# Job Offer Ranking Endpoints
# ============================================================================


@router.post("/optimal_offers", summary="Find optimal job offers based on France Travail parameters")
async def optimal_offers(
    request: Request,
    data: OptimalOffersRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    cache_hours: int = 24
) -> Dict[str, Any]:
    """
    Find and rank the most relevant job offers based on search parameters.

    First checks if cached offers exist and are fresh (less than cache_hours old).
    If cache is valid, returns cached results. Otherwise, fetches new offers from
    France Travail API and ranks them using LLM.

    Args:
        request: FastAPI request object
        data: OptimalOffersRequest with search parameters, preferences, and top_k
        db: Database session
        current_user: Current authenticated user
        cache_hours: Number of hours before cache is considered stale (default: 24)

    Returns:
        dict: Ranked job offers with match scores and reasoning, plus cache status

    Raises:
        HTTPException: If CV not found, no offers found, or ranking fails
    """
    _check_user_cv(current_user)

    try:
        result = await _get_optimal_offers_with_cache(
            current_user=current_user,
            db=db,
            ft_parameters=data.ft_parameters or {},
            preferences=data.preferences,
            top_k=data.top_k,
            cache_hours=cache_hours
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in optimal offers: {str(e)}")
        raise HTTPException(status_code=500, detail="Optimal offers ranking failed")

"""
Chat and LLM-based analysis router.

Provides endpoints for CV analysis, France Travail parameter identification,
and job offer ranking using AI/LLM services.
"""

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.methods.chat import match_profile, identify_ft_parameters, rank_job_offers
from server.database import get_db_session
from server.models import User

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
    ft_parameters: dict
    preferences: Optional[str] = None
    top_k: int = 5


# ============================================================================
# Dependencies
# ============================================================================


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """
    Dependency to extract and validate the current authenticated user from session.

    Args:
        request: FastAPI request object containing session
        db: Database session

    Returns:
        User: The currently authenticated user

    Raises:
        HTTPException: If user is not authenticated or not found in database
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


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


# ============================================================================
# Profile Matching Endpoints
# ============================================================================


@router.post("/match_profile", summary="Match profile using CV and LLM")
async def match_profile_endpoint(
    request: Request,
    data: ProfileMatchRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Analyze user's profile and match with opportunities using LLM.

    Uses the extracted CV text from a previous upload to generate
    insights on key strengths, relevant job matches, and career recommendations.

    Args:
        request: FastAPI request object
        data: ProfileMatchRequest with optional user query
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Analysis and recommendations from LLM with model and usage info

    Raises:
        HTTPException: If CV not found, validation fails, or LLM call fails
    """
    _check_user_cv(current_user)

    try:
        result = await match_profile(
            current_user.cv_text,
            user_query=data.query
        )
        return result
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
async def optimal_offers_endpoint(
    request: Request,
    data: OptimalOffersRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Find and rank the most relevant job offers based on search parameters.

    Takes a set of search parameters, fetches matching job offers from
    the database, and uses the LLM to rank them based on the user's
    CV and preferences.

    Args:
        request: FastAPI request object
        data: OptimalOffersRequest with search parameters, preferences, and top_k
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Ranked job offers with match scores and reasoning

    Raises:
        HTTPException: If CV not found, no offers found, or ranking fails
    """
    _check_user_cv(current_user)

    try:
        from server.methods.job_search import search_job_offers

        # Extract search query from parameters if available
        search_query = data.ft_parameters.get('motsCles')

        # Search for job offers using the provided parameters
        search_result = search_job_offers(
            db,
            query=search_query,
            page=1,
            page_size=50  # Get up to 50 offers to rank
        )

        offers = search_result.get('results', [])

        if not offers:
            raise ValueError("No job offers found matching the search parameters")

        # Rank the offers using LLM
        result = await rank_job_offers(
            current_user.cv_text,
            offers,
            preferences=data.preferences,
            top_k=data.top_k
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in optimal offers: {str(e)}")
        raise HTTPException(status_code=500, detail="Optimal offers ranking failed")

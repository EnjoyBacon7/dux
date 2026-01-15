import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.methods.chat import match_profile, identify_ft_parameters, rank_job_offers
from server.database import get_db_session
from server.models import User

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


class ProfileMatchRequest(BaseModel):
    query: Optional[str] = None


class FTParametersRequest(BaseModel):
    preferences: Optional[str] = None


class OptimalOffersRequest(BaseModel):
    ft_parameters: dict
    preferences: Optional[str] = None
    top_k: int = 5


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """
    Dependency to get the current authenticated user.
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.post("/match_profile", summary="Match profile using CV and LLM")
async def match_profile_endpoint(
    request: Request,
    data: ProfileMatchRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Analyze user's profile and match with opportunities using LLM.

    Uses the extracted CV text from a previous upload to generate
    insights and job matching recommendations.

    Args:
        request: FastAPI request object
        data: ProfileMatchRequest with query, model, base_url, api_key
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Analysis and recommendations from LLM
    """
    # Check if user has uploaded CV
    if not current_user.cv_text:
        raise HTTPException(
            status_code=400,
            detail="No CV found. Please upload a CV first."
        )

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


@router.post("/FT_parameters_identification", summary="Identify France Travail API search parameters")
async def ft_parameters_identification_endpoint(
    request: Request,
    data: FTParametersRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Identify optimal France Travail API search parameters based on user's CV and preferences.

    Uses the extracted CV text from a previous upload and user preferences to generate
    optimized search parameters for the France Travail job search API.

    Args:
        request: FastAPI request object
        data: FTParametersRequest with preferences, model, base_url, api_key
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Identified search parameters and usage information
    """
    # Check if user has uploaded CV
    if not current_user.cv_text:
        raise HTTPException(
            status_code=400,
            detail="No CV found. Please upload a CV first."
        )

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


@router.post("/optimal_offers", summary="Find optimal job offers based on France Travail parameters")
async def optimal_offers_endpoint(
    request: Request,
    data: OptimalOffersRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Find and rank the most relevant job offers based on France Travail API parameters.

    Takes a set of France Travail API compatible search parameters, fetches matching
    job offers from the database, and uses the LLM to rank them based on the user's
    CV and preferences.

    Args:
        request: FastAPI request object
        data: OptimalOffersRequest with ft_parameters, preferences, and top_k
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Ranked job offers with match scores and reasoning
    """
    # Check if user has uploaded CV
    if not current_user.cv_text:
        raise HTTPException(
            status_code=400,
            detail="No CV found. Please upload a CV first."
        )
    
    try:
        from server.methods.job_search import search_job_offers
        
        # Extract search query from FT parameters if available
        search_query = data.ft_parameters.get('motsCles')
        
        # Search for job offers using the FT parameters
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

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.methods.chat import match_profile
from server.database import get_db_session
from server.models import User

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


class ProfileMatchRequest(BaseModel):
    query: Optional[str] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None


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
            user_query=data.query,
            model=data.model,
            base_url=data.base_url,
            api_key=data.api_key
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in profile matching: {str(e)}")
        raise HTTPException(status_code=500, detail="Profile matching failed")

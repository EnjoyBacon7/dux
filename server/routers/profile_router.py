"""Profile management router.

Provides endpoints for user profile setup, CV upload, and experience/education management.
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.methods.upload import upload_file
from server.database import get_db_session
from server.models import User, Experience, Education

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/profile", tags=["Profile"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request Models
# ============================================================================


class ExperienceData(BaseModel):
    """Experience entry data for profile setup."""
    company: str
    title: str
    startDate: str
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None


class EducationData(BaseModel):
    """Education entry data for profile setup."""
    school: str
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    description: Optional[str] = None


class ProfileSetupRequest(BaseModel):
    """Request body for profile setup endpoint."""
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experiences: List[ExperienceData] = []
    educations: List[EducationData] = []


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


# ============================================================================
# File Upload Endpoints
# ============================================================================


@router.post("/upload", summary="Upload CV file")
async def upload_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and process a CV file (PDF, DOCX, or TXT).
    
    Handles file validation, text extraction, and storage of CV data
    in the user's profile.

    Args:
        request: FastAPI request object
        file: The CV file to upload (multipart/form-data)
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Upload result with filename, content_type, size, extracted_text, and status message
        
    Raises:
        HTTPException: If file validation or processing fails
    """
    result = await upload_file(file)

    # Update user's CV filename and extracted text in database
    current_user.cv_filename = result["filename"]
    current_user.cv_text = result["extracted_text"]
    db.commit()

    return result


# ============================================================================
# Profile Setup Endpoints
# ============================================================================


@router.post("/setup", summary="Complete profile setup")
async def complete_profile_setup(
    request: Request,
    data: ProfileSetupRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Complete user profile setup with detailed career information.
    
    Saves profile data including headline, summary, location, skills,
    work experience, and education history to the database.

    Args:
        request: FastAPI request object
        data: Profile setup data with headline, summary, location, skills, experience, education
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message confirming profile setup completion
        
    Raises:
        HTTPException: If database operations fail
    """
    try:
        # Update user profile fields
        if data.headline:
            current_user.headline = data.headline
        if data.summary:
            current_user.summary = data.summary
        if data.location:
            current_user.location = data.location
        if data.skills:
            current_user.skills = data.skills

        # Delete existing experiences and educations for this user
        db.query(Experience).filter(Experience.user_id == current_user.id).delete()
        db.query(Education).filter(Education.user_id == current_user.id).delete()

        # Add new experiences
        for exp_data in data.experiences:
            experience = Experience(
                user_id=current_user.id,
                company=exp_data.company,
                title=exp_data.title,
                start_date=exp_data.startDate,
                end_date=exp_data.endDate if not exp_data.isCurrent else None,
                is_current=exp_data.isCurrent,
                description=exp_data.description
            )
            db.add(experience)

        # Add new educations
        for edu_data in data.educations:
            education = Education(
                user_id=current_user.id,
                school=edu_data.school,
                degree=edu_data.degree,
                field_of_study=edu_data.fieldOfStudy,
                start_date=edu_data.startDate,
                end_date=edu_data.endDate,
                description=edu_data.description
            )
            db.add(education)

        # Mark profile setup as completed
        current_user.profile_setup_completed = True

        db.commit()

        return {"message": "Profile setup completed successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Profile setup failed for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete profile setup")

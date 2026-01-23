import logging
from unittest import result
"""Profile management router.

Provides endpoints for user profile setup, CV upload, and experience/education management.
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import mimetypes

from server.methods.upload import UPLOAD_DIR, upload_file
from server.database import get_db_session
from server.models import User, Experience, Education
from server.dependencies import get_current_user

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
# File Upload Endpoints
# ============================================================================


@router.post("/upload", summary="Upload CV file")
async def upload_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Upload and process a CV file (PDF, DOCX, or TXT).

    Handles file validation, text extraction, and storage of CV data
    in the user's profile. Automatically triggers CV evaluation in the background.

    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
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

    # Trigger CV evaluation in the background
    if result.get("extracted_text"):
        from server.routers.cv_router import run_cv_evaluation
        from server.database import SessionLocal

        background_tasks.add_task(
            run_cv_evaluation,
            user_id=current_user.id,
            cv_text=result["extracted_text"],
            cv_filename=result["filename"],
            db_session_factory=SessionLocal,
        )
        result["evaluation_status"] = "started"
        logger.info(f"CV evaluation triggered for user {current_user.id}")

    return result


@router.get("/cv", summary="Get current user's CV file")
async def get_cv_file(
    current_user: User = Depends(get_current_user)
):
    """
    Return the authenticated user's CV file for inline display/download.

    Ensures the user has a CV on record and that the file exists on disk
    before streaming it back to the client.
    """
    if not current_user.cv_filename:
        raise HTTPException(status_code=404, detail="No CV found for this user")

    upload_root = UPLOAD_DIR.resolve()
    file_path = (UPLOAD_DIR / current_user.cv_filename).resolve()

    # Prevent path traversal outside the upload directory
    if upload_root not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid CV path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="CV file not found")

    media_type, _ = mimetypes.guess_type(current_user.cv_filename)
    headers = {"Content-Disposition": f'inline; filename="{current_user.cv_filename}"'}

    return FileResponse(
        path=file_path,
        media_type=media_type or "application/octet-stream",
        headers=headers
    )


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


@router.post("/setup/skip", summary="Skip profile setup")
async def skip_profile_setup(
    request: Request,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Skip profile setup and mark it as completed.

    Allows users to skip the onboarding process and complete their profile later.
    Marks the profile_setup_completed flag as True to prevent forced redirects.

    Args:
        request: FastAPI request object
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message confirming setup was skipped

    Raises:
        HTTPException: If database operations fail
    """
    try:
        # Mark profile setup as completed even though skipped
        current_user.profile_setup_completed = True
        db.commit()

        logger.info(f"User {current_user.id} skipped profile setup")
        return {"message": "Profile setup skipped successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to skip profile setup for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to skip profile setup")

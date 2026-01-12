from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request
from server.methods.upload import upload_file
from server.database import get_db_session
from server.models import User, Experience, Education
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["General"])


class ExperienceData(BaseModel):
    company: str
    title: str
    startDate: str
    endDate: Optional[str] = None
    isCurrent: bool = False
    description: Optional[str] = None


class EducationData(BaseModel):
    school: str
    degree: str
    fieldOfStudy: Optional[str] = None
    startDate: str
    endDate: Optional[str] = None
    description: Optional[str] = None


class ProfileSetupRequest(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    location: Optional[str] = None
    skills: List[str] = []
    experiences: List[ExperienceData] = []
    educations: List[EducationData] = []


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """
    Dependency to get the current authenticated user.

    Args:
        request: FastAPI request object
        db: Database session

    Returns:
        User: The authenticated user object

    Raises:
        HTTPException: If user is not authenticated or not found
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.get("/healthcheck", summary="Health check")
def read_root() -> str:
    """
    Healthcheck endpoint to verify that the application is running.

    Returns:
        str: "OK" if the service is running
    """
    return "OK"


@router.post("/upload", summary="Upload file")
async def upload_endpoint(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Upload endpoint to handle file uploads (CV).

    Args:
        request: FastAPI request object
        file: The file to upload (multipart/form-data)
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Upload result containing filename, content_type, size, and message
    """
    result = await upload_file(file)

    # Update user's CV filename in database
    current_user.cv_filename = result["filename"]
    db.commit()

    return result


@router.post("/profile/setup", summary="Complete profile setup")
async def complete_profile_setup(
    request: Request,
    data: ProfileSetupRequest,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Complete user profile setup after registration.

    Args:
        data: Profile setup data including headline, summary, skills, experience, education
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message
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
        # Log error for debugging
        import logging
        logging.error(f"Profile setup failed for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to complete profile setup")

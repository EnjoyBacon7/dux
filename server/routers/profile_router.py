"""Profile management router.

Provides endpoints for user profile setup, CV upload, and experience/education management.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import mimetypes

from server.methods.upload import UPLOAD_DIR, upload_file
from server.database import get_db_session
from server.models import User
from server.utils.dependencies import get_current_user

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/profile", tags=["Profile"])
logger = logging.getLogger(__name__)

# ============================================================================
# Request Models
# ============================================================================

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
        from server.scheduler import generate_optimal_offers_for_user

        background_tasks.add_task(
            run_cv_evaluation,
            user_id=current_user.id,
            cv_text=result["extracted_text"],
            cv_filename=result["filename"],
            db_session_factory=SessionLocal,
        )
        result["evaluation_status"] = "started"
        logger.info(f"CV evaluation triggered for user {current_user.id}")

        # Trigger optimal offers generation after CV upload
        # Create a new database session for the background task
        def generate_offers_task():
            """Background task to generate optimal offers after CV upload."""
            import asyncio
            db_session = SessionLocal()
            try:
                asyncio.run(generate_optimal_offers_for_user(current_user.id, db_session))
                logger.info(f"Optimal offers generation triggered for user {current_user.id}")
            except Exception as e:
                logger.error(f"Error generating optimal offers for user {current_user.id}: {str(e)}")
            finally:
                db_session.close()

        background_tasks.add_task(generate_offers_task)
        result["optimal_offers_status"] = "started"

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

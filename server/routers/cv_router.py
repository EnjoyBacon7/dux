"""CV Evaluation router.

Provides endpoints for CV evaluation, retrieving evaluation results,
and viewing evaluation history.
"""

import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.database import get_db_session
from server.models import User, CVEvaluation
from server.cv.cv_pipeline import CVEvaluationPipeline
from server.cv.cv_schemas import EvaluationResult
from server.dependencies import get_current_user

# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/cv", tags=["CV Evaluation"])
logger = logging.getLogger(__name__)

# Constants
MAX_EVAL_LIMIT = 100  # Maximum number of evaluations to return in history


# ============================================================================
# Response Models
# ============================================================================


class EvaluationScoresResponse(BaseModel):
    """Response model for evaluation scores."""
    overall_score: Optional[int] = None
    overall_summary: Optional[str] = None
    completeness_score: Optional[int] = None
    experience_quality_score: Optional[int] = None
    skills_relevance_score: Optional[int] = None
    impact_evidence_score: Optional[int] = None
    clarity_score: Optional[int] = None
    consistency_score: Optional[int] = None


class EvaluationFeedbackResponse(BaseModel):
    """Response model for evaluation feedback."""
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []
    red_flags: List[str] = []
    missing_info: List[str] = []


class EvaluationResponse(BaseModel):
    """Full evaluation response."""
    id: int
    scores: EvaluationScoresResponse
    feedback: EvaluationFeedbackResponse
    cv_filename: Optional[str] = None
    created_at: Optional[str] = None
    evaluation_status: Optional[str] = None  # "completed", "failed", "pending"
    error_message: Optional[str] = None  # Error message if failed


class EvaluationHistoryItem(BaseModel):
    """Summary item for evaluation history."""
    id: int
    overall_score: Optional[int] = None
    cv_filename: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def run_cv_evaluation(user_id: int, cv_text: str, cv_filename: str, db_session_factory) -> None:
    """
    Run CV evaluation in the background and save results to database.

    Args:
        user_id: ID of the user whose CV is being evaluated
        cv_text: Raw CV text content
        cv_filename: Name of the CV file
        db_session_factory: Function to create a new database session
    """
    db = db_session_factory()
    pending_evaluation = None
    try:
        logger.info(f"Starting background CV evaluation for user {user_id}")
        
        # Validate CV text is not empty before starting
        if not cv_text or not cv_text.strip():
            error_msg = "CV text is empty or missing. The CV file may have been deleted from the filesystem."
            logger.error(f"CV evaluation validation failed for user {user_id}: {error_msg}")
            # Create a failed evaluation record immediately
            save_failed_evaluation_to_db(db, user_id, cv_filename, error_msg)
            return
        
        # Create a pending evaluation record so frontend knows evaluation is in progress
        pending_evaluation = CVEvaluation(
            user_id=user_id,
            cv_filename=cv_filename,
            evaluation_status="pending",
        )
        db.add(pending_evaluation)
        db.commit()
        db.refresh(pending_evaluation)
        pending_id = pending_evaluation.id
        
        # Run the pipeline (don't save to file, we'll save to DB)
        pipeline = CVEvaluationPipeline(save_results=False)
        result = pipeline.evaluate(cv_text, cv_filename=cv_filename)
        
        # Update the pending record with results
        update_evaluation_with_results(db, pending_id, result)
        
        logger.info(f"CV evaluation completed for user {user_id}: score={result.scores.overall_score}")

    except Exception as e:
        error_msg = str(e) if str(e) else "Unknown error"
        logger.error(f"CV evaluation failed for user {user_id}, cv_filename={cv_filename}: {error_msg}", exc_info=True)
        db.rollback()
        # If we created a pending record, update it to failed; otherwise create a new failed record
        if pending_evaluation and pending_evaluation.id:
            try:
                db.query(CVEvaluation).filter(CVEvaluation.id == pending_evaluation.id).update({
                    "evaluation_status": "failed",
                    "error_message": error_msg[:500]
                })
                db.commit()
            except Exception as persist_error:
                logger.exception(f"Failed to update evaluation failure status: {persist_error}")
                # Fallback: try to create a new failed record
                save_failed_evaluation_to_db(db, user_id, cv_filename, error_msg)
        else:
            save_failed_evaluation_to_db(db, user_id, cv_filename, error_msg)
    finally:
        db.close()


def save_evaluation_to_db(db: Session, user_id: int, result: EvaluationResult, cv_filename: str) -> CVEvaluation:
    """
    Save an evaluation result to the database.

    Args:
        db: Database session
        user_id: User ID
        result: EvaluationResult from the pipeline
        cv_filename: CV filename at time of evaluation

    Returns:
        CVEvaluation: The saved database record
    """
    evaluation = CVEvaluation(
        user_id=user_id,
        evaluation_id=result.evaluation_id,
        cv_filename=cv_filename,

        # Scores
        overall_score=result.scores.overall_score,
        overall_summary=result.scores.overall_summary,
        completeness_score=result.scores.completeness.score,
        experience_quality_score=result.scores.experience_quality.score,
        skills_relevance_score=result.scores.skills_relevance.score,
        impact_evidence_score=result.scores.impact_evidence.score,
        clarity_score=result.scores.clarity.score,
        consistency_score=result.scores.consistency.score,

        # Feedback
        strengths=result.scores.strengths,
        weaknesses=result.scores.weaknesses,
        recommendations=result.scores.recommendations,
        red_flags=result.scores.red_flags,
        missing_info=result.scores.missing_info,

        # Full data for traceability
        structured_cv=result.structured_cv.model_dump(mode='json'),
        derived_features=result.derived_features.model_dump(mode='json'),
        full_scores=result.scores.model_dump(mode='json'),

        # Metadata
        processing_time_seconds=int(result.processing_time_seconds) if result.processing_time_seconds else None,

        # Status
        evaluation_status="completed",
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation


def update_evaluation_with_results(db: Session, evaluation_id: int, result: EvaluationResult) -> None:
    """
    Update an existing pending evaluation record with results.
    
    Args:
        db: Database session
        evaluation_id: ID of the pending evaluation record to update
        result: EvaluationResult from the pipeline
    """
    db.query(CVEvaluation).filter(CVEvaluation.id == evaluation_id).update({
        "evaluation_id": result.evaluation_id,
        
        # Scores
        "overall_score": result.scores.overall_score,
        "overall_summary": result.scores.overall_summary,
        "completeness_score": result.scores.completeness.score,
        "experience_quality_score": result.scores.experience_quality.score,
        "skills_relevance_score": result.scores.skills_relevance.score,
        "impact_evidence_score": result.scores.impact_evidence.score,
        "clarity_score": result.scores.clarity.score,
        "consistency_score": result.scores.consistency.score,
        
        # Feedback
        "strengths": result.scores.strengths,
        "weaknesses": result.scores.weaknesses,
        "recommendations": result.scores.recommendations,
        "red_flags": result.scores.red_flags,
        "missing_info": result.scores.missing_info,
        
        # Full data for traceability
        "structured_cv": result.structured_cv.model_dump(mode='json'),
        "derived_features": result.derived_features.model_dump(mode='json'),
        "full_scores": result.scores.model_dump(mode='json'),
        
        # Metadata
        "processing_time_seconds": int(result.processing_time_seconds) if result.processing_time_seconds else None,
        
        # Status
        "evaluation_status": "completed",
    })
    db.commit()


def save_failed_evaluation_to_db(db: Session, user_id: int, cv_filename: str, error_message: str) -> None:
    """
    Save a failed evaluation record to the database.

    Args:
        db: Database session
        user_id: User ID
        cv_filename: CV filename at time of evaluation
        error_message: Error message (truncated to 500 chars)
    """
    try:
        evaluation = CVEvaluation(
            user_id=user_id,
            cv_filename=cv_filename,
            evaluation_status="failed",
            error_message=error_message[:500] if error_message else "Unknown error",
        )
        db.add(evaluation)
        db.commit()
    except Exception as persist_error:
        logger.exception(f"Failed to persist evaluation failure status for user {user_id}: {persist_error}")


def evaluation_to_response(evaluation: CVEvaluation) -> EvaluationResponse:
    """Convert a CVEvaluation database record to an API response."""
    return EvaluationResponse(
        id=evaluation.id,
        scores=EvaluationScoresResponse(
            overall_score=evaluation.overall_score,
            overall_summary=evaluation.overall_summary,
            completeness_score=evaluation.completeness_score,
            experience_quality_score=evaluation.experience_quality_score,
            skills_relevance_score=evaluation.skills_relevance_score,
            impact_evidence_score=evaluation.impact_evidence_score,
            clarity_score=evaluation.clarity_score,
            consistency_score=evaluation.consistency_score,
        ),
        feedback=EvaluationFeedbackResponse(
            strengths=evaluation.strengths or [],
            weaknesses=evaluation.weaknesses or [],
            recommendations=evaluation.recommendations or [],
            red_flags=evaluation.red_flags or [],
            missing_info=evaluation.missing_info or [],
        ),
        cv_filename=evaluation.cv_filename,
        created_at=evaluation.created_at.isoformat() if evaluation.created_at else None,
        evaluation_status=evaluation.evaluation_status,
        error_message=evaluation.error_message,
    )


# ============================================================================
# API Endpoints
# ============================================================================


@router.post("/evaluate", summary="Trigger CV evaluation")
async def evaluate_cv(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Trigger a CV evaluation for the current user.

    The evaluation runs in the background and results are saved to the database.
    Use GET /api/cv/evaluation to retrieve results.

    Returns:
        dict: Status message indicating evaluation has started

    Raises:
        HTTPException: If user has no CV uploaded
    """
    # Validate that CV text exists and is not empty
    if not current_user.cv_text or not current_user.cv_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No CV text found. The CV file may be missing or corrupted. Please upload a CV again."
        )

    # Import here to avoid circular imports
    from server.database import SessionLocal

    # Add evaluation task to background
    background_tasks.add_task(
        run_cv_evaluation,
        user_id=current_user.id,
        cv_text=current_user.cv_text,
        cv_filename=current_user.cv_filename or "unknown",
        db_session_factory=SessionLocal,
    )

    return {
        "status": "started",
        "message": "CV evaluation started. Results will be available shortly."
    }


@router.get("/evaluation", summary="Get latest CV evaluation")
async def get_evaluation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> Optional[EvaluationResponse]:
    """
    Get the most recent CV evaluation for the current user's CURRENT CV.
    
    Only returns an evaluation if it matches the user's current cv_filename.
    If the user has uploaded a new CV since the last evaluation, returns null.
    Returns pending evaluations so frontend can show "evaluating" state.
    
    Returns:
        EvaluationResponse: The latest evaluation results, or null if none exists
                           or if the evaluation is for an outdated CV
    """
    # Normalize missing filenames to "unknown" (same sentinel used by /evaluate endpoint)
    filename = current_user.cv_filename or "unknown"
    
    # First check for any evaluation (pending, completed, or failed) for current CV
    evaluation = (
        db.query(CVEvaluation)
        .filter(
            CVEvaluation.user_id == current_user.id,
            CVEvaluation.cv_filename == filename,
        )
        .order_by(CVEvaluation.created_at.desc())
        .first()
    )

    if not evaluation:
        return None

    return evaluation_to_response(evaluation)


@router.get("/evaluations", summary="Get CV evaluation history")
async def get_evaluation_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    limit: int = 10
) -> List[EvaluationHistoryItem]:
    """
    Get the evaluation history for the current user.

    Args:
        limit: Maximum number of evaluations to return (default: 10, max: 100)

    Returns:
        List of evaluation history items (summary view)
    """
    # Clamp limit to valid range
    limit = max(1, min(limit, MAX_EVAL_LIMIT))

    evaluations = (
        db.query(CVEvaluation)
        .filter(CVEvaluation.user_id == current_user.id)
        .order_by(CVEvaluation.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        EvaluationHistoryItem(
            id=e.id,
            overall_score=e.overall_score,
            cv_filename=e.cv_filename,
            created_at=e.created_at.isoformat() if e.created_at else None,
        )
        for e in evaluations
    ]


@router.get("/evaluation/{evaluation_id}", summary="Get specific CV evaluation")
async def get_evaluation_by_id(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> EvaluationResponse:
    """
    Get a specific CV evaluation by ID.

    Args:
        evaluation_id: The evaluation ID to retrieve

    Returns:
        EvaluationResponse: The evaluation results

    Raises:
        HTTPException: If evaluation not found or doesn't belong to current user
    """
    evaluation = (
        db.query(CVEvaluation)
        .filter(
            CVEvaluation.id == evaluation_id,
            CVEvaluation.user_id == current_user.id
        )
        .first()
    )

    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return evaluation_to_response(evaluation)

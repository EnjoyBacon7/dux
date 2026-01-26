"""CV Evaluation router.

Provides endpoints for CV evaluation, retrieving evaluation results,
and viewing evaluation history.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from server.database import get_db_session
from server.models import User, CVEvaluation
from server.cv.cv_pipeline import CVEvaluationPipeline
from server.cv.cv_schemas import EvaluationResult
from server.dependencies import get_current_user
from server.methods.upload import UPLOAD_DIR

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


class VisualAnalysisResponse(BaseModel):
    """Visual analysis response model."""
    visual_strengths: List[str] = []
    visual_weaknesses: List[str] = []
    visual_recommendations: List[str] = []
    layout_assessment: Optional[str] = None
    typography_assessment: Optional[str] = None
    readability_assessment: Optional[str] = None
    image_quality_notes: List[str] = []


class EvaluationResponse(BaseModel):
    """Full evaluation response."""
    id: int
    scores: EvaluationScoresResponse
    feedback: EvaluationFeedbackResponse
    visual_analysis: Optional[VisualAnalysisResponse] = None
    merged_recommendations: Optional[List[str]] = None  # Prioritized recommendations from both LLM and VLM
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
# Detailed Evaluation Response Models
# ============================================================================


class ScoreDimensionResponse(BaseModel):
    """Individual score dimension with justification and evidence."""
    score: int
    justification: str
    evidence: List[str] = []


class FullScoresResponse(BaseModel):
    """Complete scores with justifications for each dimension."""
    overall_score: int
    overall_summary: str
    completeness: ScoreDimensionResponse
    experience_quality: ScoreDimensionResponse
    skills_relevance: ScoreDimensionResponse
    impact_evidence: ScoreDimensionResponse
    clarity: ScoreDimensionResponse
    consistency: ScoreDimensionResponse
    strengths: List[str] = []
    weaknesses: List[str] = []
    missing_info: List[str] = []
    red_flags: List[str] = []
    recommendations: List[str] = []


class PersonalInfoResponse(BaseModel):
    """Personal info from structured CV."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class WorkExperienceResponse(BaseModel):
    """Work experience entry."""
    role: str
    company: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    location: Optional[str] = None
    responsibilities: List[str] = []


class EducationResponse(BaseModel):
    """Education entry."""
    degree: str
    field_of_study: Optional[str] = None
    institution: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None


class SkillCategoryResponse(BaseModel):
    """Skill category with list of skills."""
    category: Optional[str] = None
    skills: List[str] = []


class ProjectResponse(BaseModel):
    """Project entry."""
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    url: Optional[str] = None
    date: Optional[str] = None


class CertificationResponse(BaseModel):
    """Certification entry."""
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    credential_id: Optional[str] = None


class LanguageResponse(BaseModel):
    """Language proficiency entry."""
    language: str
    proficiency: Optional[str] = None


class StructuredCVResponse(BaseModel):
    """Full structured CV data."""
    personal_info: PersonalInfoResponse
    professional_summary: Optional[str] = None
    work_experience: List[WorkExperienceResponse] = []
    education: List[EducationResponse] = []
    skills: List[SkillCategoryResponse] = []
    projects: List[ProjectResponse] = []
    certifications: List[CertificationResponse] = []
    languages: List[LanguageResponse] = []


class TimelineGapResponse(BaseModel):
    """Timeline gap in employment."""
    start_date: str
    end_date: str
    duration_months: int
    between_jobs: List[str]


class TimelineOverlapResponse(BaseModel):
    """Overlapping positions."""
    job1: str
    job2: str
    overlap_start: str
    overlap_end: str
    overlap_months: int


class DateIssueResponse(BaseModel):
    """Date-related issue."""
    section: str
    issue_type: str
    description: str


class DerivedFeaturesResponse(BaseModel):
    """Derived features from CV analysis."""
    # Experience metrics
    total_experience_months: Optional[int] = None
    total_experience_years: Optional[float] = None
    experience_count: int = 0
    education_count: int = 0
    skills_count: int = 0
    projects_count: int = 0
    certifications_count: int = 0
    
    # Quantified results
    has_quantified_results: bool = False
    quantified_results_count: int = 0
    quantified_examples: List[str] = []
    
    # Timeline analysis
    timeline_gaps: List[TimelineGapResponse] = []
    timeline_overlaps: List[TimelineOverlapResponse] = []
    date_issues: List[DateIssueResponse] = []
    
    # Tenure analysis
    avg_tenure_months: Optional[float] = None
    shortest_tenure_months: Optional[int] = None
    longest_tenure_months: Optional[int] = None
    job_hopping_flag: bool = False
    
    # Completeness flags
    missing_sections: List[str] = []
    has_contact_info: bool = False
    has_summary: bool = False
    has_experience: bool = False
    has_education: bool = False
    has_skills: bool = False


class DetailedEvaluationResponse(BaseModel):
    """Full detailed evaluation response including all data."""
    id: int
    cv_filename: Optional[str] = None
    created_at: Optional[str] = None
    evaluation_status: Optional[str] = None
    error_message: Optional[str] = None
    
    # Full scores with justifications
    full_scores: Optional[FullScoresResponse] = None
    
    # Structured CV data
    structured_cv: Optional[StructuredCVResponse] = None
    
    # Derived features
    derived_features: Optional[DerivedFeaturesResponse] = None
    
    # Visual analysis
    visual_analysis: Optional[VisualAnalysisResponse] = None


# ============================================================================
# Helper Functions
# ============================================================================


def _parse_visual_analysis(visual_analysis_dict: Optional[Dict[str, Any]], evaluation_id: Optional[int] = None) -> Optional[VisualAnalysisResponse]:
    """
    Parse visual analysis dictionary into VisualAnalysisResponse.
    
    Shared helper to ensure consistent parsing and defaults across all endpoints.
    Coerces None list fields to empty lists to handle database JSON where list fields may be null.
    
    Args:
        visual_analysis_dict: Dictionary containing visual analysis data from database
        evaluation_id: Optional evaluation ID for logging purposes
        
    Returns:
        VisualAnalysisResponse if parsing succeeds, None otherwise
    """
    if not visual_analysis_dict:
        return None
    
    try:
        # Coerce None list fields to empty lists to handle database JSON where they may be null
        visual_strengths = visual_analysis_dict.get("visual_strengths") or []
        visual_weaknesses = visual_analysis_dict.get("visual_weaknesses") or []
        visual_recommendations = visual_analysis_dict.get("visual_recommendations") or []
        image_quality_notes = visual_analysis_dict.get("image_quality_notes") or []
        
        # Ensure they are lists (handle case where they might be other falsy values)
        if not isinstance(visual_strengths, list):
            visual_strengths = []
        if not isinstance(visual_weaknesses, list):
            visual_weaknesses = []
        if not isinstance(visual_recommendations, list):
            visual_recommendations = []
        if not isinstance(image_quality_notes, list):
            image_quality_notes = []
        
        return VisualAnalysisResponse(
            visual_strengths=visual_strengths,
            visual_weaknesses=visual_weaknesses,
            visual_recommendations=visual_recommendations,
            layout_assessment=visual_analysis_dict.get("layout_assessment"),
            typography_assessment=visual_analysis_dict.get("typography_assessment"),
            readability_assessment=visual_analysis_dict.get("readability_assessment"),
            image_quality_notes=image_quality_notes,
        )
    except Exception as e:
        eval_id_str = f" for evaluation {evaluation_id}" if evaluation_id else ""
        logger.warning(f"Failed to parse visual_analysis{eval_id_str}: {e}")
        return None


def _deduplicate_recommendations(recommendations: List[tuple[str, str]]) -> List[tuple[str, str]]:
    """
    Remove duplicate recommendations using simple string similarity.
    
    Args:
        recommendations: List of (source_type, recommendation) tuples
        
    Returns:
        List of unique recommendations
    """
    unique = []
    seen_lower = set()
    
    for source_type, rec in recommendations:
        # Normalize for comparison (lowercase, strip)
        rec_normalized = rec.lower().strip()
        
        # Check if similar recommendation already exists
        is_duplicate = False
        to_remove = None  # Track which seen_rec to remove if replacing
        to_replace_index = None  # Track which unique entry to replace
        
        for seen_rec in seen_lower:
            # Simple substring matching for duplicates
            if rec_normalized in seen_rec or seen_rec in rec_normalized:
                # If one is significantly longer, prefer the longer one
                if len(rec_normalized) > len(seen_rec) * 1.5:
                    # Mark for replacement (don't modify sets/lists during iteration)
                    to_remove = seen_rec
                    # Find the index in unique to replace
                    for idx, (_, existing_rec) in enumerate(unique):
                        if existing_rec.lower().strip() == seen_rec:
                            to_replace_index = idx
                            break
                    break
                else:
                    is_duplicate = True
                    break
        
        # Perform updates after iteration
        if to_remove is not None:
            # Replace shorter with longer
            seen_lower.remove(to_remove)
            if to_replace_index is not None:
                unique[to_replace_index] = (source_type, rec)
            seen_lower.add(rec_normalized)
        elif not is_duplicate:
            unique.append((source_type, rec))
            seen_lower.add(rec_normalized)
    
    return unique


def merge_and_prioritize_recommendations(
    llm_recommendations: List[str],
    vlm_recommendations: List[str],
    max_recommendations: int = 5
) -> List[str]:
    """
    Merge and prioritize recommendations from LLM and VLM sources.
    
    Priority order:
    1. Critical content issues (LLM recommendations about missing info, red flags)
    2. Important content improvements (LLM recommendations about content quality)
    3. Important visual improvements (VLM recommendations about layout/readability)
    4. Minor visual enhancements (VLM recommendations about aesthetics)
    
    Args:
        llm_recommendations: List of recommendations from LLM (content-based)
        vlm_recommendations: List of recommendations from VLM (visual-based)
        max_recommendations: Maximum number of recommendations to return
        
    Returns:
        List of top N prioritized recommendations with duplicates removed
    """
    # Combine all recommendations with source type
    all_recs = []
    
    # Add LLM recommendations with higher priority
    for rec in llm_recommendations:
        if rec and rec.strip():
            all_recs.append(("content", rec.strip()))
    
    # Add VLM recommendations with lower priority
    for rec in vlm_recommendations:
        if rec and rec.strip():
            all_recs.append(("visual", rec.strip()))
    
    # Remove duplicates
    unique_recs = _deduplicate_recommendations(all_recs)
    
    # Sort by priority (content first, then visual) while preserving original order within each bucket
    unique_recs.sort(key=lambda x: (x[0] == "visual"))
    
    # Return top N
    return [rec[1] for rec in unique_recs[:max_recommendations]]


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
        
        # Determine file path for VLM analysis
        cv_file_path = None
        if cv_filename:
            # Security: Reject absolute paths and validate path is within UPLOAD_DIR
            filename_path = Path(cv_filename)
            if filename_path.is_absolute():
                logger.warning(f"Rejected absolute path in cv_filename: {cv_filename}")
            else:
                potential_path = UPLOAD_DIR / cv_filename
                try:
                    # Resolve to absolute path and verify it's within UPLOAD_DIR
                    resolved_path = potential_path.resolve()
                    upload_root = UPLOAD_DIR.resolve()
                    
                    # Check if resolved path is within upload root, exists, and is a file (not a directory)
                    if (resolved_path.is_relative_to(upload_root) and 
                        resolved_path.exists() and 
                        resolved_path.is_file()):
                        cv_file_path = resolved_path
                    else:
                        logger.warning(f"Rejected path traversal attempt or non-existent file: {cv_filename}")
                except (ValueError, OSError) as e:
                    # Handle path resolution errors (e.g., too long paths, invalid characters)
                    logger.warning(f"Path resolution error for cv_filename '{cv_filename}': {e}")
        
        # Run the pipeline (don't save to file, we'll save to DB)
        pipeline = CVEvaluationPipeline(save_results=False)
        result = pipeline.evaluate(cv_text, cv_filename=cv_filename, cv_file_path=cv_file_path)
        
        # Update the pending record with results
        update_evaluation_with_results(db, pending_id, result)
        
        logger.info(f"CV evaluation completed for user {user_id}: score={result.scores.overall_score}")

    except Exception as e:
        # Log full exception details with context (user-facing message will be sanitized)
        logger.error(
            f"CV evaluation failed for user {user_id}, cv_filename={cv_filename}. "
            f"Exception type: {type(e).__name__}, Exception: {str(e)}",
            exc_info=True
        )
        
        # Use sanitized, user-facing error message (not raw exception text)
        user_facing_error = "Processing failed. Please retry or contact support if the issue persists."
        
        db.rollback()
        # If we created a pending record, update it to failed; otherwise create a new failed record
        if pending_evaluation and pending_evaluation.id:
            try:
                db.query(CVEvaluation).filter(CVEvaluation.id == pending_evaluation.id).update({
                    "evaluation_status": "failed",
                    "error_message": user_facing_error[:500]
                })
                db.commit()
            except Exception as persist_error:
                logger.exception(
                    f"Failed to update evaluation failure status for user {user_id}, "
                    f"evaluation_id={pending_evaluation.id}. Original error: {type(e).__name__}: {str(e)}"
                )
                # Fallback: try to create a new failed record
                save_failed_evaluation_to_db(db, user_id, cv_filename, user_facing_error)
        else:
            save_failed_evaluation_to_db(db, user_id, cv_filename, user_facing_error)
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
        visual_analysis=result.visual_analysis.model_dump(mode='json') if result.visual_analysis else None,

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
        "visual_analysis": result.visual_analysis.model_dump(mode='json') if result.visual_analysis else None,
        
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
    # Extract visual analysis if available
    visual_analysis_data = _parse_visual_analysis(evaluation.visual_analysis, evaluation.id)
    
    # Merge and prioritize recommendations
    llm_recommendations = evaluation.recommendations or []
    vlm_recommendations = visual_analysis_data.visual_recommendations if visual_analysis_data else []
    merged_recommendations = merge_and_prioritize_recommendations(
        llm_recommendations,
        vlm_recommendations,
        max_recommendations=5
    ) if (llm_recommendations or vlm_recommendations) else None
    
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
        visual_analysis=visual_analysis_data,
        merged_recommendations=merged_recommendations,
        cv_filename=evaluation.cv_filename,
        created_at=evaluation.created_at.isoformat() if evaluation.created_at else None,
        evaluation_status=evaluation.evaluation_status,
        error_message=evaluation.error_message,
    )


def evaluation_to_detailed_response(evaluation: CVEvaluation) -> DetailedEvaluationResponse:
    """Convert a CVEvaluation database record to a detailed API response with all data."""
    # Parse visual analysis
    visual_analysis_data = _parse_visual_analysis(evaluation.visual_analysis, evaluation.id)
    
    # Parse full scores
    full_scores_data = None
    if evaluation.full_scores:
        try:
            fs = evaluation.full_scores
            full_scores_data = FullScoresResponse(
                overall_score=fs.get("overall_score", 0),
                overall_summary=fs.get("overall_summary", ""),
                completeness=ScoreDimensionResponse(
                    score=fs.get("completeness", {}).get("score", 0),
                    justification=fs.get("completeness", {}).get("justification", ""),
                    evidence=fs.get("completeness", {}).get("evidence") or [],
                ),
                experience_quality=ScoreDimensionResponse(
                    score=fs.get("experience_quality", {}).get("score", 0),
                    justification=fs.get("experience_quality", {}).get("justification", ""),
                    evidence=fs.get("experience_quality", {}).get("evidence") or [],
                ),
                skills_relevance=ScoreDimensionResponse(
                    score=fs.get("skills_relevance", {}).get("score", 0),
                    justification=fs.get("skills_relevance", {}).get("justification", ""),
                    evidence=fs.get("skills_relevance", {}).get("evidence") or [],
                ),
                impact_evidence=ScoreDimensionResponse(
                    score=fs.get("impact_evidence", {}).get("score", 0),
                    justification=fs.get("impact_evidence", {}).get("justification", ""),
                    evidence=fs.get("impact_evidence", {}).get("evidence") or [],
                ),
                clarity=ScoreDimensionResponse(
                    score=fs.get("clarity", {}).get("score", 0),
                    justification=fs.get("clarity", {}).get("justification", ""),
                    evidence=fs.get("clarity", {}).get("evidence") or [],
                ),
                consistency=ScoreDimensionResponse(
                    score=fs.get("consistency", {}).get("score", 0),
                    justification=fs.get("consistency", {}).get("justification", ""),
                    evidence=fs.get("consistency", {}).get("evidence") or [],
                ),
                strengths=fs.get("strengths") or [],
                weaknesses=fs.get("weaknesses") or [],
                missing_info=fs.get("missing_info") or [],
                red_flags=fs.get("red_flags") or [],
                recommendations=fs.get("recommendations") or [],
            )
        except Exception as e:
            logger.warning(f"Failed to parse full_scores for evaluation {evaluation.id}: {e}")
    
    # Parse structured CV
    structured_cv_data = None
    if evaluation.structured_cv:
        try:
            scv = evaluation.structured_cv
            
            # Parse personal info
            pi = scv.get("personal_info", {})
            personal_info = PersonalInfoResponse(
                name=pi.get("name"),
                email=pi.get("email"),
                phone=pi.get("phone"),
                location=pi.get("location"),
                linkedin_url=pi.get("linkedin_url"),
                portfolio_url=pi.get("portfolio_url"),
            )
            
            # Parse professional summary
            prof_summary = scv.get("professional_summary")
            if prof_summary and isinstance(prof_summary, dict):
                prof_summary_text = prof_summary.get("text")
            else:
                prof_summary_text = None
            
            # Parse work experience
            work_exp = []
            for we in scv.get("work_experience") or []:
                work_exp.append(WorkExperienceResponse(
                    role=we.get("role", ""),
                    company=we.get("company", ""),
                    start_date=we.get("start_date"),
                    end_date=we.get("end_date"),
                    is_current=we.get("is_current", False),
                    location=we.get("location"),
                    responsibilities=we.get("responsibilities") or [],
                ))
            
            # Parse education
            education = []
            for edu in scv.get("education") or []:
                education.append(EducationResponse(
                    degree=edu.get("degree", ""),
                    field_of_study=edu.get("field_of_study"),
                    institution=edu.get("institution", ""),
                    start_date=edu.get("start_date"),
                    end_date=edu.get("end_date"),
                    gpa=edu.get("gpa"),
                    honors=edu.get("honors"),
                ))
            
            # Parse skills
            skills = []
            for sk in scv.get("skills") or []:
                skills.append(SkillCategoryResponse(
                    category=sk.get("category"),
                    skills=sk.get("skills") or [],
                ))
            
            # Parse projects
            projects = []
            for proj in scv.get("projects") or []:
                projects.append(ProjectResponse(
                    name=proj.get("name", ""),
                    description=proj.get("description"),
                    technologies=proj.get("technologies") or [],
                    url=proj.get("url"),
                    date=proj.get("date"),
                ))
            
            # Parse certifications
            certifications = []
            for cert in scv.get("certifications") or []:
                certifications.append(CertificationResponse(
                    name=cert.get("name", ""),
                    issuer=cert.get("issuer"),
                    date=cert.get("date"),
                    credential_id=cert.get("credential_id"),
                ))
            
            # Parse languages
            languages = []
            for lang in scv.get("languages") or []:
                languages.append(LanguageResponse(
                    language=lang.get("language", ""),
                    proficiency=lang.get("proficiency"),
                ))
            
            structured_cv_data = StructuredCVResponse(
                personal_info=personal_info,
                professional_summary=prof_summary_text,
                work_experience=work_exp,
                education=education,
                skills=skills,
                projects=projects,
                certifications=certifications,
                languages=languages,
            )
        except Exception as e:
            logger.warning(f"Failed to parse structured_cv for evaluation {evaluation.id}: {e}")
    
    # Parse derived features
    derived_features_data = None
    if evaluation.derived_features:
        try:
            df = evaluation.derived_features
            
            # Parse timeline gaps
            timeline_gaps = []
            for gap in df.get("timeline_gaps") or []:
                between_jobs = gap.get("between_jobs") or []
                if isinstance(between_jobs, tuple):
                    between_jobs = list(between_jobs)
                timeline_gaps.append(TimelineGapResponse(
                    start_date=gap.get("start_date", ""),
                    end_date=gap.get("end_date", ""),
                    duration_months=gap.get("duration_months", 0),
                    between_jobs=between_jobs,
                ))
            
            # Parse timeline overlaps
            timeline_overlaps = []
            for overlap in df.get("timeline_overlaps") or []:
                timeline_overlaps.append(TimelineOverlapResponse(
                    job1=overlap.get("job1", ""),
                    job2=overlap.get("job2", ""),
                    overlap_start=overlap.get("overlap_start", ""),
                    overlap_end=overlap.get("overlap_end", ""),
                    overlap_months=overlap.get("overlap_months", 0),
                ))
            
            # Parse date issues
            date_issues = []
            for issue in df.get("date_issues") or []:
                date_issues.append(DateIssueResponse(
                    section=issue.get("section", ""),
                    issue_type=issue.get("issue_type", ""),
                    description=issue.get("description", ""),
                ))
            
            derived_features_data = DerivedFeaturesResponse(
                total_experience_months=df.get("total_experience_months"),
                total_experience_years=df.get("total_experience_years"),
                experience_count=df.get("experience_count", 0),
                education_count=df.get("education_count", 0),
                skills_count=df.get("skills_count", 0),
                projects_count=df.get("projects_count", 0),
                certifications_count=df.get("certifications_count", 0),
                has_quantified_results=df.get("has_quantified_results", False),
                quantified_results_count=df.get("quantified_results_count", 0),
                quantified_examples=df.get("quantified_examples") or [],
                timeline_gaps=timeline_gaps,
                timeline_overlaps=timeline_overlaps,
                date_issues=date_issues,
                avg_tenure_months=df.get("avg_tenure_months"),
                shortest_tenure_months=df.get("shortest_tenure_months"),
                longest_tenure_months=df.get("longest_tenure_months"),
                job_hopping_flag=df.get("job_hopping_flag", False),
                missing_sections=df.get("missing_sections") or [],
                has_contact_info=df.get("has_contact_info", False),
                has_summary=df.get("has_summary", False),
                has_experience=df.get("has_experience", False),
                has_education=df.get("has_education", False),
                has_skills=df.get("has_skills", False),
            )
        except Exception as e:
            logger.warning(f"Failed to parse derived_features for evaluation {evaluation.id}: {e}")
    
    return DetailedEvaluationResponse(
        id=evaluation.id,
        cv_filename=evaluation.cv_filename,
        created_at=evaluation.created_at.isoformat() if evaluation.created_at else None,
        evaluation_status=evaluation.evaluation_status,
        error_message=evaluation.error_message,
        full_scores=full_scores_data,
        structured_cv=structured_cv_data,
        derived_features=derived_features_data,
        visual_analysis=visual_analysis_data,
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


@router.get("/evaluation/detailed", summary="Get detailed CV evaluation")
async def get_detailed_evaluation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
) -> DetailedEvaluationResponse:
    """
    Get the most recent CV evaluation with all detailed data for the current user.
    
    Returns full structured CV, derived features, complete scores with justifications,
    and visual analysis data.
    
    Returns:
        DetailedEvaluationResponse: The full detailed evaluation results
        
    Raises:
        HTTPException: 404 if no evaluation exists
        HTTPException: 400 if evaluation is pending or failed
    """
    # Normalize missing filenames to "unknown" (same sentinel used by /evaluate endpoint)
    filename = current_user.cv_filename or "unknown"
    
    # Get the latest evaluation for current CV
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
        raise HTTPException(
            status_code=404,
            detail="No evaluation found. Please evaluate your CV first."
        )
    
    if evaluation.evaluation_status == "pending":
        raise HTTPException(
            status_code=400,
            detail="Evaluation is still in progress. Please wait for it to complete."
        )
    
    if evaluation.evaluation_status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation failed: {evaluation.error_message or 'Unknown error'}"
        )
    
    return evaluation_to_detailed_response(evaluation)


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

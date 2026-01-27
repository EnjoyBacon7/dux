"""
CV Evaluation Pipeline - Pydantic Schemas

Defines all data models for:
- Structured CV (Step 1 output)
- Derived Features (Step 2 output)
- CV Scores (Step 3 output)
- Full Evaluation Result (Step 4 output)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Step 1: Structured CV Schema (LLM Extractor Output)
# =============================================================================

class PersonalInfo(BaseModel):
    """Personal and contact information extracted from CV"""
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    location: Optional[str] = Field(None, description="City, country or full address")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(None, description="Portfolio or personal website URL")
    evidence_quote: Optional[str] = Field(None, description="Verbatim text from CV supporting this extraction")


class ProfessionalSummary(BaseModel):
    """Professional summary or objective statement"""
    text: Optional[str] = Field(None, description="The summary/objective text")
    evidence_quote: Optional[str] = Field(None, description="Verbatim text from CV")


class WorkExperience(BaseModel):
    """Single work experience entry"""
    role: str = Field(..., description="Job title/role")
    company: str = Field(..., description="Company/organization name")
    start_date: Optional[str] = Field(None, description="Start date (extracted as-is from CV)")
    end_date: Optional[str] = Field(None, description="End date (extracted as-is, or 'Present')")
    is_current: bool = Field(False, description="Whether this is the current position")
    location: Optional[str] = Field(None, description="Work location if mentioned")
    responsibilities: list[str] = Field(default_factory=list, description="List of responsibilities/achievements")
    evidence_quote: str = Field(..., description="Verbatim text from CV for this experience")


class Education(BaseModel):
    """Single education entry"""
    degree: str = Field(..., description="Degree type (e.g., Bachelor's, Master's, PhD)")
    field_of_study: Optional[str] = Field(None, description="Field/major of study")
    institution: str = Field(..., description="School/university name")
    start_date: Optional[str] = Field(None, description="Start date (extracted as-is)")
    end_date: Optional[str] = Field(None, description="End date (extracted as-is)")
    gpa: Optional[str] = Field(None, description="GPA if mentioned")
    honors: Optional[str] = Field(None, description="Honors, distinctions if mentioned")
    evidence_quote: str = Field(..., description="Verbatim text from CV")


class SkillCategory(BaseModel):
    """Group of related skills"""
    category: Optional[str] = Field(None, description="Category name (e.g., 'Programming Languages', 'Tools')")
    skills: list[str] = Field(default_factory=list, description="List of skills in this category")
    evidence_quote: Optional[str] = Field(None, description="Verbatim text from CV")


class Project(BaseModel):
    """Project entry"""
    name: str = Field(..., description="Project name/title")
    description: Optional[str] = Field(None, description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Technologies/tools used")
    url: Optional[str] = Field(None, description="Project URL if mentioned")
    date: Optional[str] = Field(None, description="Date or date range")
    evidence_quote: str = Field(..., description="Verbatim text from CV")


class Certification(BaseModel):
    """Certification or license entry"""
    name: str = Field(..., description="Certification name")
    issuer: Optional[str] = Field(None, description="Issuing organization")
    date: Optional[str] = Field(None, description="Date obtained or expiry")
    credential_id: Optional[str] = Field(None, description="Credential ID if mentioned")
    evidence_quote: str = Field(..., description="Verbatim text from CV")


class Language(BaseModel):
    """Language proficiency entry"""
    language: str = Field(..., description="Language name")
    proficiency: Optional[str] = Field(None, description="Proficiency level (e.g., Native, Fluent, B2)")
    evidence_quote: Optional[str] = Field(None, description="Verbatim text from CV")


class StructuredCV(BaseModel):
    """
    Complete structured CV schema - Output of Step 1 (LLM Extractor)
    
    All fields are extracted strictly from the CV text.
    Missing information is marked as None/empty, never inferred.
    """
    personal_info: PersonalInfo = Field(default_factory=PersonalInfo)
    professional_summary: Optional[ProfessionalSummary] = None
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[SkillCategory] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)
    
    # Metadata
    extraction_timestamp: datetime = Field(default_factory=utc_now)
    extraction_warnings: list[str] = Field(default_factory=list, description="Any warnings during extraction")


# =============================================================================
# Step 2: Derived Features Schema (Validator Output)
# =============================================================================

class TimelineGap(BaseModel):
    """Represents a gap in employment timeline"""
    start_date: str = Field(..., description="Start of gap (end of previous job)")
    end_date: str = Field(..., description="End of gap (start of next job)")
    duration_months: int = Field(..., description="Gap duration in months")
    between_jobs: tuple[str, str] = Field(..., description="Jobs before and after the gap")


class TimelineOverlap(BaseModel):
    """Represents overlapping positions"""
    job1: str = Field(..., description="First overlapping job (role @ company)")
    job2: str = Field(..., description="Second overlapping job (role @ company)")
    overlap_start: str = Field(..., description="Start of overlap period")
    overlap_end: str = Field(..., description="End of overlap period")
    overlap_months: int = Field(..., description="Overlap duration in months")


class DateIssue(BaseModel):
    """Represents a date-related issue"""
    section: str = Field(..., description="Section where issue was found (e.g., 'work_experience[0]')")
    issue_type: str = Field(..., description="Type of issue (e.g., 'missing_start_date', 'invalid_format', 'future_date')")
    description: str = Field(..., description="Human-readable description of the issue")


class DerivedFeatures(BaseModel):
    """
    Derived features computed from structured CV - Output of Step 2 (Validator)
    
    All values are computed deterministically from the structured CV data.
    """
    # Experience metrics
    total_experience_months: Optional[int] = Field(None, description="Total work experience in months")
    total_experience_years: Optional[float] = Field(None, description="Total work experience in years")
    experience_count: int = Field(0, description="Number of work experience entries")
    education_count: int = Field(0, description="Number of education entries")
    skills_count: int = Field(0, description="Total number of unique skills")
    projects_count: int = Field(0, description="Number of project entries")
    certifications_count: int = Field(0, description="Number of certifications")
    
    # Quantified results detection
    has_quantified_results: bool = Field(False, description="Whether CV contains quantified achievements")
    quantified_results_count: int = Field(0, description="Number of quantified achievements found")
    quantified_examples: list[str] = Field(default_factory=list, description="Examples of quantified results")
    
    # Timeline analysis
    timeline_gaps: list[TimelineGap] = Field(default_factory=list, description="Gaps in employment timeline")
    timeline_overlaps: list[TimelineOverlap] = Field(default_factory=list, description="Overlapping positions")
    date_issues: list[DateIssue] = Field(default_factory=list, description="Date-related issues found")
    
    # Tenure analysis
    avg_tenure_months: Optional[float] = Field(None, description="Average job tenure in months")
    shortest_tenure_months: Optional[int] = Field(None, description="Shortest job tenure")
    longest_tenure_months: Optional[int] = Field(None, description="Longest job tenure")
    job_hopping_flag: bool = Field(False, description="True if avg tenure < 18 months with 3+ jobs")
    
    # Completeness flags
    missing_sections: list[str] = Field(default_factory=list, description="Missing CV sections")
    has_contact_info: bool = Field(False, description="Has at least email or phone")
    has_summary: bool = Field(False, description="Has professional summary")
    has_experience: bool = Field(False, description="Has work experience")
    has_education: bool = Field(False, description="Has education section")
    has_skills: bool = Field(False, description="Has skills section")
    
    # Validation metadata
    validation_timestamp: datetime = Field(default_factory=utc_now)
    validation_warnings: list[str] = Field(default_factory=list)


# =============================================================================
# Step 3: CV Scores Schema (Scorer Output)
# =============================================================================

class ScoreDimension(BaseModel):
    """Individual scoring dimension with justification"""
    score: int = Field(..., ge=0, le=100, description="Score from 0-100")
    justification: str = Field(..., description="Explanation for the score")
    evidence: list[str] = Field(default_factory=list, description="Evidence quotes supporting the score")


class CVScores(BaseModel):
    """
    CV evaluation scores - Output of Step 3 (LLM Scorer)
    
    All scores are based strictly on structured CV data and derived features.
    """
    # Overall score
    overall_score: int = Field(..., ge=0, le=100, description="Overall CV score 0-100")
    overall_summary: str = Field(..., description="Brief summary of overall evaluation")
    
    # Dimension scores
    completeness: ScoreDimension = Field(..., description="Completeness of CV sections")
    experience_quality: ScoreDimension = Field(..., description="Quality and relevance of experience")
    skills_relevance: ScoreDimension = Field(..., description="Breadth and specificity of skills")
    impact_evidence: ScoreDimension = Field(..., description="Presence of quantified achievements")
    clarity: ScoreDimension = Field(..., description="Structure and readability")
    consistency: ScoreDimension = Field(..., description="Timeline coherence and logical flow")
    
    # Qualitative feedback
    strengths: list[str] = Field(default_factory=list, description="Key strengths of the CV")
    weaknesses: list[str] = Field(default_factory=list, description="Areas for improvement")
    missing_info: list[str] = Field(default_factory=list, description="Important missing information")
    red_flags: list[str] = Field(default_factory=list, description="Potential concerns or red flags")
    recommendations: list[str] = Field(default_factory=list, description="Actionable improvement suggestions")
    
    # Metadata
    scoring_timestamp: datetime = Field(default_factory=utc_now)


# =============================================================================
# Visual Analysis Schema (VLM Output)
# =============================================================================

class VisualAnalysis(BaseModel):
    """
    Visual analysis of CV document - Output from VLM analysis
    
    Focuses exclusively on visual/structural aspects of the CV presentation.
    Does NOT evaluate content, skills, or candidate quality.
    """
    visual_strengths: list[str] = Field(default_factory=list, description="Visual strengths of the CV layout")
    visual_weaknesses: list[str] = Field(default_factory=list, description="Visual weaknesses in layout/presentation")
    visual_recommendations: list[str] = Field(default_factory=list, description="Actionable visual improvement suggestions")
    layout_assessment: Optional[str] = Field(None, description="Overall layout quality description")
    typography_assessment: Optional[str] = Field(None, description="Typography quality description")
    readability_assessment: Optional[str] = Field(None, description="Readability assessment")
    image_quality_notes: list[str] = Field(default_factory=list, description="Notes about image quality issues if any")
    analysis_timestamp: datetime = Field(default_factory=utc_now)


# =============================================================================
# Step 4: Full Evaluation Result (Pipeline Output)
# =============================================================================

class EvaluationResult(BaseModel):
    """
    Complete CV evaluation result - Output of Step 4 (Pipeline)
    
    Contains all intermediate outputs for full traceability and auditability.
    """
    # Identifiers
    evaluation_id: str = Field(..., description="Unique evaluation ID")
    cv_filename: Optional[str] = Field(None, description="Original CV filename if known")
    
    # Step outputs
    raw_cv_text: str = Field(..., description="Original raw CV text (Step 0 output)")
    structured_cv: StructuredCV = Field(..., description="Structured CV data (Step 1 output)")
    derived_features: DerivedFeatures = Field(..., description="Computed features (Step 2 output)")
    scores: CVScores = Field(..., description="Evaluation scores (Step 3 output)")
    visual_analysis: Optional[VisualAnalysis] = Field(None, description="Visual analysis from VLM (parallel to LLM)")
    
    # Pipeline metadata
    pipeline_version: str = Field("1.0.0", description="Pipeline version")
    evaluation_timestamp: datetime = Field(default_factory=utc_now)
    processing_time_seconds: Optional[float] = Field(None, description="Total processing time")
    errors: list[str] = Field(default_factory=list, description="Any errors during processing")



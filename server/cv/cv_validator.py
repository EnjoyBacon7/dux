"""
CV Evaluation Pipeline - Step 2: Deterministic Validator

Processes structured CV data to:
- Normalize and validate dates
- Detect timeline gaps and overlaps
- Compute derived features and signals

This step uses only deterministic code - no LLM calls.
"""

import re
import logging
from datetime import datetime
from typing import Optional
from dateutil import parser as date_parser
from dateutil.relativedelta import relativedelta

from server.cv.cv_schemas import (
    StructuredCV,
    DerivedFeatures,
    TimelineGap,
    TimelineOverlap,
    DateIssue,
)

logger = logging.getLogger(__name__)

# Patterns for detecting quantified results
QUANTIFIED_PATTERNS = [
    r'\d+%',  # Percentages
    r'\$[\d,]+',  # Dollar amounts
    r'€[\d,]+',  # Euro amounts
    r'[\d,]+\s*(users?|customers?|clients?|employees?|team members?)',  # User counts
    r'[\d,]+\s*(million|billion|k|K|M|B)',  # Large numbers
    r'(increased?|decreased?|reduced?|improved?|grew?|saved?|generated?)\s*(by\s*)?\d+',  # Action + number
    r'\d+x\s',  # Multipliers
    r'top\s*\d+',  # Rankings
    r'\d+\+\s*(years?|months?|projects?|clients?)',  # Count with unit
    r'(led?|managed?|oversaw?)\s*(a\s*)?(team\s*of\s*)?\d+',  # Team size
]


def validate_and_compute_features(structured_cv: StructuredCV) -> DerivedFeatures:
    """
    Validate structured CV data and compute derived features.
    
    Args:
        structured_cv: The structured CV from Step 1
    
    Returns:
        DerivedFeatures: Computed signals and validation results
    """
    features = DerivedFeatures()
    
    # Basic counts
    features.experience_count = len(structured_cv.work_experience)
    features.education_count = len(structured_cv.education)
    features.projects_count = len(structured_cv.projects)
    features.certifications_count = len(structured_cv.certifications)
    
    # Count total skills
    features.skills_count = sum(
        len(cat.skills) for cat in structured_cv.skills
    )
    
    # Completeness checks
    features = _check_completeness(structured_cv, features)
    
    # Quantified results analysis
    features = _analyze_quantified_results(structured_cv, features)
    
    # Timeline analysis (gaps, overlaps, tenure)
    features = _analyze_timeline(structured_cv, features)
    
    # Date validation
    features = _validate_dates(structured_cv, features)
    
    return features


def _check_completeness(cv: StructuredCV, features: DerivedFeatures) -> DerivedFeatures:
    """Check which sections are present and complete"""
    
    # Check contact info
    pi = cv.personal_info
    features.has_contact_info = bool(pi.email or pi.phone)
    
    # Check summary
    features.has_summary = bool(cv.professional_summary and cv.professional_summary.text)
    
    # Check experience
    features.has_experience = len(cv.work_experience) > 0
    
    # Check education
    features.has_education = len(cv.education) > 0
    
    # Check skills
    features.has_skills = features.skills_count > 0
    
    # Build missing sections list
    missing = []
    if not features.has_contact_info:
        missing.append("contact_info")
    if not features.has_summary:
        missing.append("professional_summary")
    if not features.has_experience:
        missing.append("work_experience")
    if not features.has_education:
        missing.append("education")
    if not features.has_skills:
        missing.append("skills")
    if not cv.personal_info.name:
        missing.append("name")
    
    features.missing_sections = missing
    
    return features


def _analyze_quantified_results(cv: StructuredCV, features: DerivedFeatures) -> DerivedFeatures:
    """Detect quantified achievements in the CV"""
    
    quantified_examples = []
    
    # Check work experience responsibilities
    for exp in cv.work_experience:
        for resp in exp.responsibilities:
            for pattern in QUANTIFIED_PATTERNS:
                if re.search(pattern, resp, re.IGNORECASE):
                    # Found a quantified result
                    quantified_examples.append(resp[:100])  # Truncate for brevity
                    break
    
    # Check project descriptions
    for proj in cv.projects:
        if proj.description:
            for pattern in QUANTIFIED_PATTERNS:
                if re.search(pattern, proj.description, re.IGNORECASE):
                    quantified_examples.append(proj.description[:100])
                    break
    
    features.quantified_results_count = len(quantified_examples)
    features.has_quantified_results = len(quantified_examples) > 0
    features.quantified_examples = quantified_examples[:5]  # Keep top 5 examples
    
    return features


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Attempt to parse a date string into a datetime object.
    
    Handles various formats:
    - "Present", "Current", "Now" -> returns None (handled specially)
    - "2020" -> January 2020
    - "Jan 2020", "January 2020" -> parsed month/year
    - "01/2020", "2020-01" -> parsed month/year
    - Full dates like "Jan 15, 2020" -> parsed date
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    
    # Handle "present" variants
    if date_str.lower() in ['present', 'current', 'now', 'ongoing', 'aujourd\'hui', 'présent']:
        return datetime.now()
    
    try:
        # Try dateutil parser first (handles most formats)
        parsed = date_parser.parse(date_str, default=datetime(2000, 1, 1))
        return parsed
    except (ValueError, TypeError):
        pass
    
    # Try year-only format
    year_match = re.match(r'^(\d{4})$', date_str)
    if year_match:
        return datetime(int(year_match.group(1)), 1, 1)
    
    # Try month/year formats like "01/2020" or "2020/01"
    my_match = re.match(r'^(\d{1,2})[/\-](\d{4})$', date_str)
    if my_match:
        month, year = int(my_match.group(1)), int(my_match.group(2))
        if 1 <= month <= 12:
            return datetime(year, month, 1)
    
    my_match2 = re.match(r'^(\d{4})[/\-](\d{1,2})$', date_str)
    if my_match2:
        year, month = int(my_match2.group(1)), int(my_match2.group(2))
        if 1 <= month <= 12:
            return datetime(year, month, 1)
    
    return None


def _months_between(start: datetime, end: datetime) -> int:
    """Calculate months between two dates"""
    delta = relativedelta(end, start)
    return delta.years * 12 + delta.months


def _analyze_timeline(cv: StructuredCV, features: DerivedFeatures) -> DerivedFeatures:
    """Analyze employment timeline for gaps, overlaps, and tenure"""
    
    if not cv.work_experience:
        return features
    
    # Parse all dates and build timeline
    timeline_entries = []
    for i, exp in enumerate(cv.work_experience):
        start = _parse_date(exp.start_date)
        end = _parse_date(exp.end_date) if not exp.is_current else datetime.now()
        
        if start and end:
            timeline_entries.append({
                'index': i,
                'job': f"{exp.role} @ {exp.company}",
                'start': start,
                'end': end,
                'is_current': exp.is_current,
            })
    
    if not timeline_entries:
        features.validation_warnings.append("Could not parse any work experience dates")
        return features
    
    # Sort by start date
    timeline_entries.sort(key=lambda x: x['start'])
    
    # Calculate tenure for each job
    tenures = []
    for entry in timeline_entries:
        months = _months_between(entry['start'], entry['end'])
        if months > 0:
            tenures.append(months)
    
    if tenures:
        features.avg_tenure_months = sum(tenures) / len(tenures)
        features.shortest_tenure_months = min(tenures)
        features.longest_tenure_months = max(tenures)
        
        # Job hopping flag: avg tenure < 18 months with 3+ jobs
        if len(tenures) >= 3 and features.avg_tenure_months < 18:
            features.job_hopping_flag = True
    
    # Calculate total experience
    total_months = sum(tenures) if tenures else 0
    features.total_experience_months = total_months
    features.total_experience_years = round(total_months / 12, 1) if total_months else None
    
    # Detect gaps (> 3 months between jobs)
    gaps = []
    for i in range(len(timeline_entries) - 1):
        current = timeline_entries[i]
        next_job = timeline_entries[i + 1]
        
        gap_months = _months_between(current['end'], next_job['start'])
        if gap_months > 3:  # Only flag gaps > 3 months
            gaps.append(TimelineGap(
                start_date=current['end'].strftime('%Y-%m'),
                end_date=next_job['start'].strftime('%Y-%m'),
                duration_months=gap_months,
                between_jobs=(current['job'], next_job['job']),
            ))
    
    features.timeline_gaps = gaps
    
    # Detect overlaps
    overlaps = []
    for i in range(len(timeline_entries)):
        for j in range(i + 1, len(timeline_entries)):
            entry1 = timeline_entries[i]
            entry2 = timeline_entries[j]
            
            # Check for overlap
            overlap_start = max(entry1['start'], entry2['start'])
            overlap_end = min(entry1['end'], entry2['end'])
            
            if overlap_start < overlap_end:
                overlap_months = _months_between(overlap_start, overlap_end)
                if overlap_months > 0:
                    overlaps.append(TimelineOverlap(
                        job1=entry1['job'],
                        job2=entry2['job'],
                        overlap_start=overlap_start.strftime('%Y-%m'),
                        overlap_end=overlap_end.strftime('%Y-%m'),
                        overlap_months=overlap_months,
                    ))
    
    features.timeline_overlaps = overlaps
    
    return features


def _validate_dates(cv: StructuredCV, features: DerivedFeatures) -> DerivedFeatures:
    """Validate all dates in the CV and flag issues"""
    
    date_issues = []
    now = datetime.now()
    
    # Validate work experience dates
    for i, exp in enumerate(cv.work_experience):
        section = f"work_experience[{i}]"
        
        if not exp.start_date:
            date_issues.append(DateIssue(
                section=section,
                issue_type="missing_start_date",
                description=f"Missing start date for {exp.role} at {exp.company}"
            ))
        else:
            parsed = _parse_date(exp.start_date)
            if not parsed:
                date_issues.append(DateIssue(
                    section=section,
                    issue_type="invalid_format",
                    description=f"Could not parse start date '{exp.start_date}'"
                ))
            elif parsed > now:
                date_issues.append(DateIssue(
                    section=section,
                    issue_type="future_date",
                    description=f"Start date '{exp.start_date}' is in the future"
                ))
        
        if not exp.is_current and not exp.end_date:
            date_issues.append(DateIssue(
                section=section,
                issue_type="missing_end_date",
                description=f"Missing end date for non-current position {exp.role} at {exp.company}"
            ))
    
    # Validate education dates
    for i, edu in enumerate(cv.education):
        section = f"education[{i}]"
        
        if edu.start_date:
            parsed = _parse_date(edu.start_date)
            if not parsed:
                date_issues.append(DateIssue(
                    section=section,
                    issue_type="invalid_format",
                    description=f"Could not parse start date '{edu.start_date}'"
                ))
        
        if edu.end_date:
            parsed = _parse_date(edu.end_date)
            if not parsed:
                date_issues.append(DateIssue(
                    section=section,
                    issue_type="invalid_format",
                    description=f"Could not parse end date '{edu.end_date}'"
                ))
    
    features.date_issues = date_issues
    
    return features


# Convenience function for testing
def validate_structured_cv(structured_cv_dict: dict) -> DerivedFeatures:
    """
    Validate from a dictionary (e.g., loaded from JSON).
    
    Args:
        structured_cv_dict: Dictionary representation of StructuredCV
    
    Returns:
        DerivedFeatures: Computed features
    """
    cv = StructuredCV.model_validate(structured_cv_dict)
    return validate_and_compute_features(cv)



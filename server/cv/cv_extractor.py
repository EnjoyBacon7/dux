"""
CV Evaluation Pipeline - Step 1: LLM Fact Extractor

Extracts structured facts from raw CV text using an LLM.
Only explicit information is extracted - no inference or guessing.
Each extracted item includes verbatim evidence quotes from the CV.
"""

import json
import logging
from typing import Optional

from server.config import settings
from server.utils.openai_client import create_openai_client
from server.utils.llm import call_llm_sync
from server.cv.cv_schemas import (
    StructuredCV,
    PersonalInfo,
    ProfessionalSummary,
    WorkExperience,
    Education,
    SkillCategory,
    Project,
    Certification,
    Language,
)

logger = logging.getLogger(__name__)

# System prompt for the extractor LLM
EXTRACTOR_SYSTEM_PROMPT = """You are a precise CV fact extractor. Your task is to extract ONLY explicit information from the provided CV text.

CRITICAL RULES:
1. Extract ONLY information that is explicitly stated in the CV text
2. Do NOT infer, guess, or complete missing information
3. If information is missing or unclear, use null or empty values
4. For each extracted item, include a verbatim "evidence_quote" from the CV text
5. Preserve original formatting of dates, names, and terms exactly as written
6. Do NOT translate or modify any text - extract as-is

OUTPUT FORMAT:
Return a valid JSON object matching the specified schema. Include evidence_quote fields with exact text snippets from the CV.

HANDLING AMBIGUITY:
- If a date is unclear (e.g., "2020" vs "Jan 2020"), extract exactly as written
- If a section header is ambiguous, use your best judgment but note in extraction_warnings
- If text is in a non-English language, extract as-is without translation"""


EXTRACTION_PROMPT_TEMPLATE = """Extract structured information from this CV text. Follow the schema exactly.

CV TEXT:
---
{cv_text}
---

Extract and return a JSON object with the following structure:
{{
    "personal_info": {{
        "name": "Full name or null",
        "email": "Email or null",
        "phone": "Phone or null",
        "location": "Location or null",
        "linkedin_url": "LinkedIn URL or null",
        "portfolio_url": "Portfolio URL or null",
        "evidence_quote": "Verbatim text containing contact info"
    }},
    "professional_summary": {{
        "text": "Summary/objective text or null",
        "evidence_quote": "Verbatim text"
    }} or null if not present,
    "work_experience": [
        {{
            "role": "Job title",
            "company": "Company name",
            "start_date": "Start date as written",
            "end_date": "End date as written or 'Present'",
            "is_current": true/false,
            "location": "Location or null",
            "responsibilities": ["List of responsibilities/achievements"],
            "evidence_quote": "Verbatim text for this job entry"
        }}
    ],
    "education": [
        {{
            "degree": "Degree type",
            "field_of_study": "Field or null",
            "institution": "School name",
            "start_date": "Start date or null",
            "end_date": "End date or null",
            "gpa": "GPA or null",
            "honors": "Honors or null",
            "evidence_quote": "Verbatim text"
        }}
    ],
    "skills": [
        {{
            "category": "Category name or null",
            "skills": ["skill1", "skill2"],
            "evidence_quote": "Verbatim text"
        }}
    ],
    "projects": [
        {{
            "name": "Project name",
            "description": "Description or null",
            "technologies": ["tech1", "tech2"],
            "url": "URL or null",
            "date": "Date or null",
            "evidence_quote": "Verbatim text"
        }}
    ],
    "certifications": [
        {{
            "name": "Certification name",
            "issuer": "Issuer or null",
            "date": "Date or null",
            "credential_id": "ID or null",
            "evidence_quote": "Verbatim text"
        }}
    ],
    "languages": [
        {{
            "language": "Language name",
            "proficiency": "Level or null",
            "evidence_quote": "Verbatim text or null"
        }}
    ],
    "extraction_warnings": ["Any warnings about unclear or ambiguous content"]
}}

Return ONLY the JSON object, no additional text."""


# ============================================================================
# CV Extraction Functions
# ============================================================================


def extract_cv_facts(raw_cv_text: str, model: Optional[str] = None) -> StructuredCV:
    """
    Extract structured facts from raw CV text using LLM.

    Args:
        raw_cv_text: The raw text content of the CV
        model: Optional model override (defaults to settings.openai_model)

    Returns:
        StructuredCV: Validated structured CV data

    Raises:
        ValueError: If extraction fails or returns invalid data
    """
    if not raw_cv_text or not raw_cv_text.strip():
        raise ValueError("CV text is empty or contains only whitespace")

    logger.info(f"Extracting CV facts using model: {model}")

    try:
        result = call_llm_sync(
            prompt=EXTRACTION_PROMPT_TEMPLATE.format(cv_text=raw_cv_text),
            system_content=EXTRACTOR_SYSTEM_PROMPT,
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=4000,
            parse_json=True,
            model=model,
            response_format={"type": "json_object"},
        )

        extracted_data = result["data"]

        # Convert to Pydantic models with validation
        structured_cv = _parse_extracted_data(extracted_data)

        logger.info(f"Successfully extracted CV with {len(structured_cv.work_experience)} experiences, "
                    f"{len(structured_cv.education)} education entries, "
                    f"{len(structured_cv.skills)} skill categories")

        return structured_cv

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"CV extraction failed: {e}")
        raise ValueError(f"CV extraction failed: {e}")


def _parse_extracted_data(data: dict) -> StructuredCV:
    """
    Parse extracted JSON data into validated Pydantic models.

    Handles missing fields gracefully and validates structure.
    """
    # Parse personal info
    personal_info_data = data.get("personal_info", {})
    personal_info = PersonalInfo(
        name=personal_info_data.get("name"),
        email=personal_info_data.get("email"),
        phone=personal_info_data.get("phone"),
        location=personal_info_data.get("location"),
        linkedin_url=personal_info_data.get("linkedin_url"),
        portfolio_url=personal_info_data.get("portfolio_url"),
        evidence_quote=personal_info_data.get("evidence_quote"),
    )

    # Parse professional summary
    summary_data = data.get("professional_summary")
    professional_summary = None
    if summary_data and summary_data.get("text"):
        professional_summary = ProfessionalSummary(
            text=summary_data.get("text"),
            evidence_quote=summary_data.get("evidence_quote"),
        )

    # Parse work experience
    work_experience = []
    for exp_data in data.get("work_experience", []):
        if exp_data.get("role") and exp_data.get("company"):
            work_experience.append(WorkExperience(
                role=exp_data["role"],
                company=exp_data["company"],
                start_date=exp_data.get("start_date"),
                end_date=exp_data.get("end_date"),
                is_current=exp_data.get("is_current", False),
                location=exp_data.get("location"),
                responsibilities=exp_data.get("responsibilities", []),
                evidence_quote=exp_data.get("evidence_quote", ""),
            ))

    # Parse education
    education = []
    for edu_data in data.get("education", []):
        if edu_data.get("degree") and edu_data.get("institution"):
            education.append(Education(
                degree=edu_data["degree"],
                field_of_study=edu_data.get("field_of_study"),
                institution=edu_data["institution"],
                start_date=edu_data.get("start_date"),
                end_date=edu_data.get("end_date"),
                gpa=edu_data.get("gpa"),
                honors=edu_data.get("honors"),
                evidence_quote=edu_data.get("evidence_quote", ""),
            ))

    # Parse skills
    skills = []
    for skill_data in data.get("skills", []):
        if skill_data.get("skills"):
            skills.append(SkillCategory(
                category=skill_data.get("category"),
                skills=skill_data["skills"],
                evidence_quote=skill_data.get("evidence_quote"),
            ))

    # Parse projects
    projects = []
    for proj_data in data.get("projects", []):
        if proj_data.get("name"):
            projects.append(Project(
                name=proj_data["name"],
                description=proj_data.get("description"),
                technologies=proj_data.get("technologies", []),
                url=proj_data.get("url"),
                date=proj_data.get("date"),
                evidence_quote=proj_data.get("evidence_quote", ""),
            ))

    # Parse certifications
    certifications = []
    for cert_data in data.get("certifications", []):
        if cert_data.get("name"):
            certifications.append(Certification(
                name=cert_data["name"],
                issuer=cert_data.get("issuer"),
                date=cert_data.get("date"),
                credential_id=cert_data.get("credential_id"),
                evidence_quote=cert_data.get("evidence_quote", ""),
            ))

    # Parse languages
    languages = []
    for lang_data in data.get("languages", []):
        if lang_data.get("language"):
            languages.append(Language(
                language=lang_data["language"],
                proficiency=lang_data.get("proficiency"),
                evidence_quote=lang_data.get("evidence_quote"),
            ))

    # Build final structured CV
    return StructuredCV(
        personal_info=personal_info,
        professional_summary=professional_summary,
        work_experience=work_experience,
        education=education,
        skills=skills,
        projects=projects,
        certifications=certifications,
        languages=languages,
        extraction_warnings=data.get("extraction_warnings", []),
    )


# Convenience function for testing
def extract_from_file(file_path: str) -> StructuredCV:
    """
    Extract CV facts from a text file.

    Args:
        file_path: Path to a text file containing CV content

    Returns:
        StructuredCV: Validated structured CV data
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        cv_text = f.read()
    return extract_cv_facts(cv_text)

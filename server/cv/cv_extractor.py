"""
CV Evaluation Pipeline - Step 1: LLM Fact Extractor

Extracts structured facts from raw CV text using an LLM.
Only explicit information is extracted - no inference or guessing.
Each extracted item includes verbatim evidence quotes from the CV.
"""

import json
import logging
from typing import Optional

from openai import OpenAI

from server.config import settings
from server.utils.prompts import load_prompt_template
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


# Load prompts from files
try:
    EXTRACTOR_SYSTEM_PROMPT = load_prompt_template("cv_extractor_system")
    EXTRACTION_PROMPT_TEMPLATE = load_prompt_template("cv_extractor_template")
except FileNotFoundError as e:
    raise RuntimeError(
        "Missing prompt templates. Ensure server/prompts/*.txt is packaged and deployed."
    ) from e


def create_openai_client() -> OpenAI:
    """Create OpenAI client with settings from config"""
    return OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


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
    
    model = model or settings.openai_model
    client = create_openai_client()
    
    logger.info(f"Extracting CV facts using model: {model}")
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EXTRACTOR_SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_PROMPT_TEMPLATE.format(cv_text=raw_cv_text)},
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            response_format={"type": "json_object"},
        )
        
        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("LLM returned empty response")
        
        # Parse JSON response
        extracted_data = json.loads(response_text)
        
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



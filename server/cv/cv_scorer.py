"""
CV Evaluation Pipeline - Step 3: LLM Scorer

Evaluates the CV based on structured data and derived features.
Produces scores on multiple dimensions with justifications.

IMPORTANT: The scorer ONLY uses the structured CV and derived features.
It does NOT re-interpret the raw CV text.
"""

import json
import logging
from typing import Optional, Dict, Any

from server.utils.llm import call_llm_sync
from server.utils.prompts import load_prompt_template
from server.cv.cv_schemas import (
    StructuredCV,
    DerivedFeatures,
    CVScores,
    ScoreDimension,
)

logger = logging.getLogger(__name__)


# Load prompts from files
SCORER_SYSTEM_PROMPT = load_prompt_template("cv_scorer_system")
SCORING_PROMPT_TEMPLATE = load_prompt_template("cv_scorer_template")


# ============================================================================
# CV Scoring Functions
# ============================================================================


def score_cv(
    structured_cv: StructuredCV,
    derived_features: DerivedFeatures,
    model: Optional[str] = None,
    vlm_request: Optional[Dict[str, Any]] = None
) -> CVScores:
    """
    Score a CV based on structured data and derived features.
    
    Args:
        structured_cv: The structured CV from Step 1
        derived_features: The computed features from Step 2
        model: Optional model override (defaults to settings.openai_model)
        vlm_request: Optional VLM request (not used in scoring, for API consistency)
    
    Returns:
        CVScores: Complete evaluation scores with justifications
    
    Raises:
        ValueError: If scoring fails
    """
    
    logger.info(f"Scoring CV using model: {model}")
    
    # Convert to JSON for the prompt
    structured_cv_json = structured_cv.model_dump_json(indent=2, exclude={'extraction_timestamp'})
    derived_features_json = derived_features.model_dump_json(indent=2, exclude={'validation_timestamp'})
    
    try:
        result = call_llm_sync(
            prompt=SCORING_PROMPT_TEMPLATE.format(
                structured_cv_json=structured_cv_json,
                derived_features_json=derived_features_json,
            ),
            system_content=SCORER_SYSTEM_PROMPT,
            temperature=0.3,  # Slightly higher than extractor for more nuanced evaluation
            max_tokens=3000,
            parse_json=True,
            model=model,
            response_format={"type": "json_object"},
        )
        
        scores_data = result["data"]
        
        # Convert to Pydantic model with validation
        cv_scores = _parse_scores_data(scores_data)
        
        logger.info(f"CV scored: overall={cv_scores.overall_score}, "
                   f"strengths={len(cv_scores.strengths)}, "
                   f"recommendations={len(cv_scores.recommendations)}")
        
        return cv_scores
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"LLM returned invalid JSON: {e}")
    except Exception as e:
        logger.error(f"CV scoring failed: {e}")
        raise ValueError(f"CV scoring failed: {e}")


def _parse_scores_data(data: dict) -> CVScores:
    """
    Parse scoring JSON data into validated Pydantic model.
    """
    
    def parse_dimension(dim_data: dict) -> ScoreDimension:
        """Parse a single dimension score"""
        return ScoreDimension(
            score=dim_data.get("score", 0),
            justification=dim_data.get("justification", "No justification provided"),
            evidence=dim_data.get("evidence", []),
        )
    
    return CVScores(
        overall_score=data.get("overall_score", 0),
        overall_summary=data.get("overall_summary", "No summary provided"),
        
        completeness=parse_dimension(data.get("completeness", {})),
        experience_quality=parse_dimension(data.get("experience_quality", {})),
        skills_relevance=parse_dimension(data.get("skills_relevance", {})),
        impact_evidence=parse_dimension(data.get("impact_evidence", {})),
        clarity=parse_dimension(data.get("clarity", {})),
        consistency=parse_dimension(data.get("consistency", {})),
        
        strengths=data.get("strengths", []),
        weaknesses=data.get("weaknesses", []),
        missing_info=data.get("missing_info", []),
        red_flags=data.get("red_flags", []),
        recommendations=data.get("recommendations", []),
    )


def score_from_dicts(
    structured_cv_dict: dict,
    derived_features_dict: dict,
    model: Optional[str] = None
) -> CVScores:
    """
    Score CV from dictionary representations (e.g., loaded from JSON).
    
    Args:
        structured_cv_dict: Dictionary representation of StructuredCV
        derived_features_dict: Dictionary representation of DerivedFeatures
        model: Optional model override
    
    Returns:
        CVScores: Evaluation scores
    """
    cv = StructuredCV.model_validate(structured_cv_dict)
    features = DerivedFeatures.model_validate(derived_features_dict)
    return score_cv(cv, features, model)



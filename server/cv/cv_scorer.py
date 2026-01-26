"""
CV Evaluation Pipeline - Step 3: LLM Scorer

Evaluates the CV based on structured data and derived features.
Produces scores on multiple dimensions with justifications.

IMPORTANT: The scorer ONLY uses the structured CV and derived features.
It does NOT re-interpret the raw CV text.
"""

import json
import logging
from typing import Optional

from server.utils.openai_client import create_openai_client
from server.cv.cv_schemas import (
    StructuredCV,
    DerivedFeatures,
    CVScores,
    ScoreDimension,
)

logger = logging.getLogger(__name__)

# System prompt for the scorer LLM
SCORER_SYSTEM_PROMPT = """You are a professional CV evaluator. Your task is to score and evaluate a CV based ONLY on the structured data and computed features provided.

CRITICAL RULES:
1. Base ALL evaluations strictly on the provided structured CV data and derived features
2. Do NOT make assumptions about information not present in the data
3. Every score and claim must be justified with evidence from the input data
4. Be fair and objective - focus on what IS present, not what could be
5. Scores are 0-100 where:
   - 0-20: Very Poor - Critical issues or major gaps
   - 21-40: Below Average - Significant weaknesses
   - 41-60: Average - Meets basic expectations
   - 61-80: Good - Above average with some strengths
   - 81-100: Excellent - Outstanding quality

SCORING DIMENSIONS:
1. Completeness: Are all important sections present and filled?
2. Experience Quality: Quality, relevance, and progression of work experience
3. Skills Relevance: Breadth, specificity, and organization of skills
4. Impact Evidence: Presence of quantified achievements and results
5. Clarity: Structure, organization, and readability signals
6. Consistency: Timeline coherence, logical progression, no red flags

OUTPUT: Return a valid JSON object with scores, justifications, and feedback."""


SCORING_PROMPT_TEMPLATE = """Evaluate this CV based on the structured data and derived features below.

## STRUCTURED CV DATA:
```json
{structured_cv_json}
```

## DERIVED FEATURES (Computed Signals):
```json
{derived_features_json}
```

## YOUR TASK:
Provide a comprehensive evaluation as a JSON object with this structure:

{{
    "overall_score": <0-100>,
    "overall_summary": "Brief 2-3 sentence summary of the CV quality",
    
    "completeness": {{
        "score": <0-100>,
        "justification": "Explain the score based on missing_sections, has_* flags",
        "evidence": ["Quote specific data points supporting this score"]
    }},
    
    "experience_quality": {{
        "score": <0-100>,
        "justification": "Evaluate based on experience_count, tenure, responsibilities quality",
        "evidence": ["Evidence from work_experience data"]
    }},
    
    "skills_relevance": {{
        "score": <0-100>,
        "justification": "Evaluate based on skills_count, organization, specificity",
        "evidence": ["Evidence from skills data"]
    }},
    
    "impact_evidence": {{
        "score": <0-100>,
        "justification": "Evaluate based on quantified_results_count, quantified_examples",
        "evidence": ["Quote actual quantified results found"]
    }},
    
    "clarity": {{
        "score": <0-100>,
        "justification": "Evaluate organization, section structure, professional summary",
        "evidence": ["Evidence about structure and clarity"]
    }},
    
    "consistency": {{
        "score": <0-100>,
        "justification": "Evaluate based on timeline_gaps, timeline_overlaps, date_issues",
        "evidence": ["Evidence about timeline consistency"]
    }},
    
    "strengths": ["List 3-5 key strengths based on the data"],
    "weaknesses": ["List 3-5 areas for improvement"],
    "missing_info": ["List important missing information"],
    "red_flags": ["List any concerns (job hopping, gaps, inconsistencies) or empty if none"],
    "recommendations": ["List 3-5 actionable improvement suggestions"]
}}

Return ONLY the JSON object, no additional text."""


# ============================================================================
# CV Scoring Functions
# ============================================================================


def score_cv(
    structured_cv: StructuredCV,
    derived_features: DerivedFeatures,
    model: Optional[str] = None
) -> CVScores:
    """
    Score a CV based on structured data and derived features.
    
    Args:
        structured_cv: The structured CV from Step 1
        derived_features: The computed features from Step 2
        model: Optional model override (defaults to settings.openai_model)
    
    Returns:
        CVScores: Complete evaluation scores with justifications
    
    Raises:
        ValueError: If scoring fails
    """
    model = model or settings.openai_model
    client = create_openai_client()
    
    logger.info(f"Scoring CV using model: {model}")
    
    # Convert to JSON for the prompt
    structured_cv_json = structured_cv.model_dump_json(indent=2, exclude={'extraction_timestamp'})
    derived_features_json = derived_features.model_dump_json(indent=2, exclude={'validation_timestamp'})
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SCORER_SYSTEM_PROMPT},
                {"role": "user", "content": SCORING_PROMPT_TEMPLATE.format(
                    structured_cv_json=structured_cv_json,
                    derived_features_json=derived_features_json,
                )},
            ],
            temperature=0.3,  # Slightly higher than extractor for more nuanced evaluation
            response_format={"type": "json_object"},
        )
        
        response_text = response.choices[0].message.content
        if not response_text:
            raise ValueError("LLM returned empty response")
        
        # Parse JSON response
        scores_data = json.loads(response_text)
        
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



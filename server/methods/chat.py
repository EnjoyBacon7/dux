import logging
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from server.config import settings
from server.utils.llm import call_llm_async, call_llm_sync, extract_response_content, parse_json_response

logger = logging.getLogger(__name__)

# ============================================================================
# Deprecated: Old functions kept for backwards compatibility
# ============================================================================
# These are now delegated to the unified LLM interface in server.utils.llm
# They are maintained here for backwards compatibility with existing code.


def get_openai_client(base_url: Optional[str] = None, api_key: Optional[str] = None):
    """
    Deprecated: Use server.utils.openai_client.create_openai_client() instead.

    This function is kept for backwards compatibility only.
    """
    from server.utils.openai_client import create_openai_client
    return create_openai_client()


# ============================================================================
# LLM Core Functionality
# ============================================================================


# ============================================================================
# Input Validation Utilities
# ============================================================================


def _load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    prompts_dir = Path(__file__).parent.parent / "prompts"
    template_path = prompts_dir / f"{template_name}.txt"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")


def _validate_cv_text(cv_text: str) -> None:
    """
    Validate that CV text is provided and non-empty.

    Args:
        cv_text: CV text to validate

    Raises:
        ValueError: If CV text is empty or None
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a valid CV first.")


def _validate_job_offers(job_offers: List[Dict[str, Any]]) -> None:
    """
    Validate that job offers list is provided and non-empty.

    Args:
        job_offers: Job offers list to validate

    Raises:
        ValueError: If job offers list is empty or None
    """
    if not job_offers or len(job_offers) == 0:
        raise ValueError("No job offers provided to rank.")


# ============================================================================
# France Travail Job Search API
# ============================================================================


def create_ft_parameters_prompt(cv_text: str, preferences: Optional[str] = None) -> str:
    """
    Create a prompt for identifying France Travail API search parameters.

    Generates an LLM prompt that analyzes the CV and user preferences
    to recommend optimal France Travail API search parameters.

    Args:
        cv_text: User's CV text
        preferences: Optional user preferences or job requirements

    Returns:
        Formatted prompt for the LLM
    """
    try:
        base_prompt = _load_prompt_template("FT_search")
    except FileNotFoundError:
        logger.warning("FT_search template not found, using fallback")
        base_prompt = """You are a job search parameter optimizer for the France Travail API.
        
Generate optimal search parameters for a user's job search based on their CV and preferences.
Return a JSON object with parameters like motsCles, codeROME, region, typeContrat, etc.
Only return the JSON object, no additional text."""

    # Build the full prompt
    prompt = base_prompt + f"\n\n## User Information\n\nCV:\n{cv_text}"

    if preferences:
        prompt += f"\n\nUser Preferences/Query:\n{preferences}"

    return prompt


async def identify_ft_parameters(
    cv_text: str,
    preferences: Optional[str] = None
) -> Dict[str, Any]:
    """
    Identify optimal France Travail API search parameters from CV.

    Uses an LLM to analyze the CV and user preferences, then returns
    recommended search parameters for the France Travail API.

    Args:
        cv_text: User's CV text
        preferences: Optional user job preferences/requirements

    Returns:
        Dict with keys:
        - success: bool (True on success)
        - parameters: Recommended API parameters as dict
        - model: Model name used
        - usage: Token usage statistics

    Raises:
        ValueError: If CV is empty or LLM call fails
    """
    _validate_cv_text(cv_text)

    try:
        prompt = create_ft_parameters_prompt(cv_text, preferences)
        result = await call_llm_async(
            prompt=prompt,
            system_content="You are an expert job search optimizer specializing in France Travail API parameters. You output only valid JSON objects with no additional text or explanation.",
            temperature=0.5,
            max_tokens=2000,
            parse_json=True,
            json_array=False
        )

        parameters = result["data"]
        # France Travail aggregates keyword tokens with AND; drop motsCles to avoid over-filtering.
        if isinstance(parameters, dict) and "motsCles" in parameters:
            parameters.pop("motsCles", None)

        return {
            "success": True,
            "parameters": parameters,
            "model": result["model"],
            "usage": result["usage"]
        }
    except Exception as e:
        logger.error(f"Unexpected error in FT parameters identification: {str(e)}")
        raise ValueError(f"FT parameters identification failed: {str(e)}")


# ============================================================================
# Job Offer Ranking API
# ============================================================================


def _format_job_offers_for_analysis(job_offers: List[Dict[str, Any]]) -> str:
    """
    Format job offers into a readable text representation for LLM analysis.

    Args:
        job_offers: List of job offer dictionaries from France Travail API

    Returns:
        Formatted job offers as text
    """
    offers_text = ""
    for i, offer in enumerate(job_offers, 1):
        offers_text += f"\n{i}. {offer.get('intitule', 'Unknown Position')}  - {offer.get(
            'entreprise_nom', 'Unknown Company')} \n"
        offers_text += f"   Location: {offer.get('lieuTravail_libelle', 'N/A')}\n"
        offers_text += f"   Contract: {offer.get('typeContratLibelle', 'N/A')}\n"
        offers_text += f"   Description: {offer.get('description', 'N/A')[:200]}...\n"
        offers_text += f"   Salary: {offer.get('salaire_libelle', 'N/A')}\n"
    return offers_text


def create_job_ranking_prompt(
    cv_text: str,
    job_offers: List[Dict[str, Any]],
    preferences: Optional[str] = None,
    top_k: int = 5
) -> str:
    """
    Create a prompt for ranking and scoring job offers.

    Args:
        cv_text: User's CV text
        job_offers: List of job offer dictionaries
        preferences: Optional user preferences
        top_k: Number of top offers to return

    Returns:
        Formatted prompt for the LLM
    """
    template = _load_prompt_template("job_ranking")
    offers_text = _format_job_offers_for_analysis(job_offers)

    preferences_section = ""
    if preferences:
        preferences_section = f"\n## USER'S PREFERENCES\n\n{preferences}\n"

    return template.format(
        cv_text=cv_text,
        preferences=preferences_section,
        offers_text=offers_text,
        top_k=top_k
    )


async def rank_job_offers(
    cv_text: str,
    job_offers: List[Dict[str, Any]],
    preferences: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Rank and score job offers based on CV and preferences.

    Uses an LLM to analyze provided job offers against the user's CV
    and preferences, returning ranked offers with match scores and reasoning.

    Args:
        cv_text: User's CV text
        job_offers: List of job offer dictionaries from France Travail API
        preferences: Optional user job preferences/requirements
        top_k: Number of top offers to return (default: 5)

    Returns:
        Dict with keys:
        - success: bool (True on success)
        - ranked_offers: List of ranked job offer dicts with scores
        - total_offers_analyzed: int (total offers provided)
        - top_offers_returned: int (actual top offers returned)
        - model: Model name used
        - usage: Token usage statistics

    Raises:
        ValueError: If CV or job offers are empty, or LLM call fails
    """
    _validate_cv_text(cv_text)
    _validate_job_offers(job_offers)

    try:
        prompt = create_job_ranking_prompt(cv_text, job_offers, preferences, top_k)
        result = await call_llm_async(
            prompt=prompt,
            system_content="You are an expert job matching analyst. Analyze CVs and job offers to identify the best matches. Return only valid JSON with no additional text.",
            temperature=0.5,
            max_tokens=2000,
            parse_json=True,
            json_array=True
        )

        ranked_offers = result["data"]
        return {
            "success": True,
            "ranked_offers": ranked_offers,
            "total_offers_analyzed": len(job_offers),
            "top_offers_returned": min(top_k, len(ranked_offers)),
            "model": result["model"],
            "usage": result["usage"]
        }

    except Exception as e:
        logger.error(f"Unexpected error in job ranking: {str(e)}")
        raise ValueError(f"Job ranking failed: {str(e)}")

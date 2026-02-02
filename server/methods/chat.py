import logging
import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from server.config import settings
from server.utils.llm import call_llm_async, call_llm_sync, extract_response_content, parse_json_response
from openai import OpenAI, APIError
from server.thread_pool import run_blocking_in_executor
from server.utils.prompts import load_prompt_template
from server.methods.FT_job_search import search_france_travail
from server.models import User, OptimalOffer

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
    api_key = api_key or settings.openai_api_key
    base_url = base_url or settings.openai_base_url
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in environment variables")

    return OpenAI(api_key=api_key, base_url=base_url)


# ============================================================================
# Response Extraction and Parsing Utilities
# ============================================================================


def _extract_response_content(choice: Any) -> str:
    """
    Extract content from API response choice, handling reasoning models.

    Args:
        choice: Response choice object from OpenAI API

    Returns:
        str: Extracted content

    Raises:
        ValueError: If no valid content found in response
    """
    content = choice.message.content

    # Handle reasoning models that put content in reasoning_content
    if content is None:
        if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
            content = choice.message.reasoning_content
            logger.info("Using reasoning_content from message")
        elif hasattr(choice, 'provider_specific_fields'):
            fields = choice.provider_specific_fields
            if isinstance(fields, dict) and 'reasoning_content' in fields:
                content = fields['reasoning_content']
                logger.info("Using reasoning_content from provider_specific_fields")

        if content is None:
            logger.error(f"Content is None. Finish reason: {choice.finish_reason}")
            if choice.finish_reason == "length":
                raise ValueError(
                    "Response was cut off due to max_tokens limit. Try increasing max_tokens or shortening your query."
                )
            elif choice.finish_reason == "content_filter":
                raise ValueError("Response was filtered by content policy")
            else:
                raise ValueError(f"No content in response (finish_reason: {choice.finish_reason})")

    if not content:
        raise ValueError("Empty response from LLM")

    return content


def _parse_json_response(content: str, json_array: bool = False) -> Dict[str, Any] | List[Any]:
    """
    Parse JSON from LLM response, extracting JSON from surrounding text if needed.

    Args:
        content: Response content string
        json_array: Whether to extract JSON array (vs object)

    Returns:
        Parsed JSON object or array

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        if json_array:
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
        else:
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            return json.loads(json_str)
        else:
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {content}")
        raise ValueError(f"Invalid JSON in LLM response: {str(e)}")


def _build_usage_dict(response: Any) -> Dict[str, int]:
    """Build usage statistics dictionary from API response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        logger.warning("LLM response missing usage; defaulting token counts to zero.")
        return {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
    }


# ============================================================================
# LLM Core Functionality
# ============================================================================


# ============================================================================
# Input Validation Utilities
# ============================================================================




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


def create_ft_parameters_prompt(cv_text: str, preferences: Optional[str] = None, matching_context: Optional[str] = None) -> str:
    """
    Create a prompt for identifying France Travail API search parameters.

    Generates an LLM prompt that analyzes the CV and user preferences
    to recommend optimal France Travail API search parameters.

    Args:
        cv_text: User's CV text
        preferences: Optional user preferences or job requirements
        matching_context: Optional additional matching context from user

    Returns:
        Formatted prompt for the LLM
    """
    try:
        base_prompt = load_prompt_template("FT_search")
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
    
    if matching_context and matching_context.strip():
        prompt += f"\n\nADDITIONAL USER CONTEXT:\n{matching_context}"

    return prompt


async def identify_ft_parameters(
    cv_text: str,
    preferences: Optional[str] = None,
    matching_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Identify optimal France Travail API search parameters from CV.

    Uses an LLM to analyze the CV and user preferences, then returns
    recommended search parameters for the France Travail API.

    Args:
        cv_text: User's CV text
        preferences: Optional user job preferences/requirements
        matching_context: Optional additional matching context from user

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
        prompt = create_ft_parameters_prompt(cv_text, preferences, matching_context)
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
    matching_context: Optional[str] = None,
    top_k: int = 5
) -> str:
    """
    Create a prompt for ranking and scoring job offers.

    Args:
        cv_text: User's CV text
        job_offers: List of job offer dictionaries
        preferences: Optional user preferences
        matching_context: Optional additional matching context from user
        top_k: Number of top offers to return

    Returns:
        Formatted prompt for the LLM
    """
    try:
        template = load_prompt_template("job_ranking")
    except FileNotFoundError:
        logger.warning("job_ranking template not found, using fallback")
        template = """You are a job matching and ranking expert.

Analyze the provided job offers and rank them based on how well they match the user's CV and preferences.

## USER'S CV

{cv_text}

{preferences}{matching_context}

## JOB OFFERS TO RANK

{offers_text}

## YOUR TASK

Rank and score the top {top_k} job offers that best match the user's profile.
Return a JSON object with ranked offers, scores, and match reasons.
Only return the JSON object, no additional text."""
    
    offers_text = _format_job_offers_for_analysis(job_offers)

    preferences_section = ""
    if preferences:
        preferences_section = f"\n## USER'S PREFERENCES\n\n{preferences}\n"
    
    matching_context_section = ""
    if matching_context and matching_context.strip():
        matching_context_section = f"\n## ADDITIONAL USER CONTEXT\n\n{matching_context}\n"

    return template.format(
        cv_text=cv_text,
        preferences=preferences_section,
        matching_context=matching_context_section,
        offers_text=offers_text,
        top_k=top_k
    )


async def rank_job_offers(
    cv_text: str,
    job_offers: List[Dict[str, Any]],
    preferences: Optional[str] = None,
    matching_context: Optional[str] = None,
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
        matching_context: Optional additional matching context from user
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
        prompt = create_job_ranking_prompt(cv_text, job_offers, preferences, matching_context, top_k)
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


# ============================================================================
# Optimal Offers Cache Management
# ============================================================================


async def get_optimal_offers_with_cache(
    current_user: User,
    db: Session,
    ft_parameters: dict,
    preferences: Optional[str] = None,
    top_k: int = 5,
    cache_hours: int = 24
) -> Dict[str, Any]:
    """
    Get optimal job offers, using cache if available and fresh.

    Checks if cached offers exist and are less than cache_hours old.
    If cache is valid, returns cached results. Otherwise, fetches new offers
    from France Travail API, ranks them with LLM, and saves to database.

    Args:
        current_user: Current authenticated user
        db: Database session
        ft_parameters: France Travail search parameters
        preferences: Optional user preferences for ranking
        top_k: Number of top offers to return
        cache_hours: Number of hours before cache is considered stale

    Returns:
        dict: Ranked job offers with match scores, reasoning, and cache status

    Raises:
        ValueError: If no offers found
        Exception: If ranking or database operations fail
    """
    # Check cache first
    try:
        cached_offers = db.query(OptimalOffer).filter(
            OptimalOffer.user_id == current_user.id
        ).order_by(OptimalOffer.position).all()

        if cached_offers:
            # Check if cache is fresh
            most_recent = max(cached_offers, key=lambda o: o.updated_at or o.created_at)
            last_updated = most_recent.updated_at or most_recent.created_at
            cache_age = datetime.now(last_updated.tzinfo) - last_updated

            if cache_age < timedelta(hours=cache_hours):
                # Cache is fresh, return cached results
                # Return offers with job_id for frontend to fetch full data
                offers_data = []
                for o in cached_offers:
                    offer_dict = {
                        "job_id": o.job_id,
                        "position": o.position,
                        "score": o.score,
                        "match_reasons": o.match_reasons,
                        "concerns": o.concerns,
                    }
                    offers_data.append(offer_dict)

                return {
                    "success": True,
                    "offers": offers_data,
                    "count": len(offers_data),
                    "cached": True,
                    "cache_age_hours": round(cache_age.total_seconds() / 3600, 1)
                }
    except Exception as e:
        logger.warning(f"Error checking cache: {str(e)}, proceeding with fresh search")

    # Cache is stale or missing, fetch new offers in thread pool
    # Run France Travail API call in thread pool to avoid blocking other clients
    # Add timeout to prevent scheduler from hanging
    try:
        offers = await asyncio.wait_for(
            run_blocking_in_executor(
                search_france_travail,
                ft_parameters or {},
                50
            ),
            timeout=300  # 5 minute timeout for API search
        )
    except asyncio.TimeoutError:
        logger.error(
            f"Timeout searching France Travail API for user {current_user.id} - took longer than 5 minutes"
        )
        raise ValueError("Timeout searching job offers from France Travail API")

    if not offers:
        raise ValueError("No job offers found from France Travail API with the provided parameters")

    # Rank the offers using LLM (also in thread pool)
    # Add timeout for LLM ranking
    try:
        result = await asyncio.wait_for(
            rank_job_offers(
                current_user.cv_text,
                offers,
                preferences=preferences,
                matching_context=current_user.matching_context,
                top_k=top_k
            ),
            timeout=300  # 5 minute timeout for LLM ranking
        )
    except asyncio.TimeoutError:
        logger.error(
            f"Timeout ranking job offers for user {current_user.id} - LLM took longer than 5 minutes"
        )
        raise ValueError("Timeout ranking job offers - LLM service took too long")

    # Save optimal offers to database (delete old ones first)
    db.query(OptimalOffer).filter(OptimalOffer.user_id == current_user.id).delete()

    ranked_offers = result.get("ranked_offers", [])
    # Map ranked offers to get job IDs from full job data using position (1-indexed)
    offers_with_data = []
    for offer in ranked_offers:
        position = offer.get("position", 0)
        # Position is 1-indexed, so subtract 1 to get the correct offer from the list
        job_data = offers[position - 1] if 0 < position <= len(offers) else None
        job_id = job_data.get("id") if job_data else None

        # Skip offers with invalid positions or missing job_id to avoid DB constraint violations
        if not job_id:
            logger.warning(f"Skipping offer with invalid position {position} or missing job_id")
            continue

        db_offer = OptimalOffer(
            user_id=current_user.id,
            position=position,
            job_id=job_id,
            score=offer.get("score", 0),
            match_reasons=offer.get("match_reasons", []),
            concerns=offer.get("concerns", []),
        )
        db.add(db_offer)

        # Build simplified OptimalOffer for response
        offer_with_data = {
            "job_id": job_id,
            "position": position,
            "score": offer.get("score", 0),
            "match_reasons": offer.get("match_reasons", []),
            "concerns": offer.get("concerns", []),
        }
        offers_with_data.append(offer_with_data)

    db.commit()

    # Add cache status and offers to result
    result["cached"] = False
    result["offers"] = offers_with_data

    return result

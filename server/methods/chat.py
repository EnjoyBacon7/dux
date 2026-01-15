import logging
import json
from typing import Optional
from pathlib import Path
from openai import OpenAI, APIError
from server.config import settings

logger = logging.getLogger(__name__)


def get_openai_client(base_url: Optional[str] = None, api_key: Optional[str] = None) -> OpenAI:
    """
    Get OpenAI client with configured API key and optional base_url

    Args:
        base_url: Optional custom base URL (defaults to settings.openai_base_url)
        api_key: Optional custom API key (defaults to settings.openai_api_key)
    """
    api_key = api_key or settings.openai_api_key
    base_url = base_url or settings.openai_base_url

    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured in environment variables")

    return OpenAI(api_key=api_key, base_url=base_url)


def create_profile_match_prompt(cv_text: str, user_query: Optional[str] = None) -> str:
    """
    Create a prompt for profile matching using CV text
    """
    prompt = f"""You are a professional job matching assistant. 
    
I have a user's CV with the following information:

---
{cv_text}
---

"""

    if user_query:
        prompt += f"The user's request: {user_query}\n\n"

    prompt += """Please analyze this CV and provide insights on:
1. Key strengths and skills
2. Relevant job matches based on experience
3. Recommendations for career development
4. Matching with job opportunities

Be concise and actionable in your response."""

    return prompt


async def match_profile(
    cv_text: str,
    user_query: Optional[str] = None
) -> dict:
    """
    Use LLM to match and analyze user profile based on CV

    Args:
        cv_text: Extracted text from CV
        user_query: Optional user query/preferences

    Returns:
        dict: LLM response with analysis and matches
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a valid CV first.")

    try:
        prompt = create_profile_match_prompt(cv_text, user_query)
        result = await _call_llm(
            prompt=prompt,
            system_content="You are an expert career advisor and job matching specialist.",
            temperature=0.7,
            max_tokens=8000  # Increased from 2000 to avoid cutoffs
        )

        return {
            "success": True,
            "analysis": result["data"],
            "model": result["model"],
            "usage": result["usage"]
        }
    except Exception as e:
        logger.error(f"Unexpected error in profile matching: {str(e)}")
        raise ValueError(f"Profile matching failed: {str(e)}")


async def _call_llm(
    prompt: str,
    system_content: str,
    temperature: float = 0.7,
    max_tokens: int = 4000,
    parse_json: bool = False,
    json_array: bool = False
) -> dict:
    """
    Generic LLM call handler for common API interaction patterns.

    Args:
        prompt: User message content
        system_content: System message content
        temperature: Model temperature parameter
        max_tokens: Maximum tokens for response
        parse_json: Whether to parse response as JSON
        json_array: Whether to extract JSON array (vs object)

    Returns:
        dict: Response data with success flag, content/parameters, model info, and usage stats
    """
    model = settings.openai_model

    try:
        client = get_openai_client()

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        if not response.choices or len(response.choices) == 0:
            logger.error("No choices returned from LLM")
            raise ValueError("No response from LLM")

        choice = response.choices[0]
        content = choice.message.content

        # Handle reasoning models
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
                        "Response was cut off due to max_tokens limit. Try increasing max_tokens or shortening your query.")
                elif choice.finish_reason == "content_filter":
                    raise ValueError("Response was filtered by content policy")
                else:
                    raise ValueError(f"No content in response (finish_reason: {choice.finish_reason})")

        if not content:
            raise ValueError("Empty response from LLM")

        result_data = content

        # Parse JSON if requested
        if parse_json:
            try:
                if json_array:
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                else:
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    result_data = json.loads(json_str)
                else:
                    result_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {content}")
                raise ValueError(f"Invalid JSON in LLM response: {str(e)}")

        return {
            "success": True,
            "data": result_data,
            "model": model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }

    except APIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise ValueError(f"LLM service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in LLM call: {str(e)}")
        raise


def _load_ft_search_prompt() -> str:
    """Load the France Travail search optimization prompt template"""
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "FT_search.txt"
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"FT_search.txt prompt not found at {prompt_path}")
        return ""


def create_ft_parameters_prompt(cv_text: str, preferences: Optional[str] = None) -> str:
    """
    Create a prompt for identifying France Travail API search parameters based on CV and preferences

    Args:
        cv_text: User's CV text
        preferences: Optional user preferences/query

    Returns:
        Complete prompt for the LLM
    """
    base_prompt = _load_ft_search_prompt()

    if not base_prompt:
        # Fallback if template not found
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
) -> dict:
    """
    Use LLM to identify optimal France Travail API search parameters based on CV and preferences

    Args:
        cv_text: User's CV text
        preferences: Optional user job preferences/query

    Returns:
        dict: Identified search parameters and metadata
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a valid CV first.")

    try:
        prompt = create_ft_parameters_prompt(cv_text, preferences)
        result = await _call_llm(
            prompt=prompt,
            system_content="You are an expert job search optimizer specializing in France Travail API parameters. You output only valid JSON objects with no additional text or explanation.",
            temperature=0.5,  # Lower temperature for more consistent parameter generation
            max_tokens=4000,
            parse_json=True,
            json_array=False
        )

        return {
            "success": True,
            "parameters": result["data"],
            "model": result["model"],
            "usage": result["usage"]
        }
    except Exception as e:
        logger.error(f"Unexpected error in FT parameters identification: {str(e)}")
        raise ValueError(f"FT parameters identification failed: {str(e)}")


async def rank_job_offers(
    cv_text: str,
    job_offers: list,
    preferences: Optional[str] = None,
    top_k: int = 5
) -> dict:
    """
    Use LLM to rank and score job offers based on CV and preferences.

    Args:
        cv_text: User's CV text
        job_offers: List of job offer dictionaries from France Travail API
        preferences: Optional user job preferences/query
        top_k: Number of top offers to return (default: 5)

    Returns:
        dict: Ranked job offers with scores and reasoning
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a valid CV first.")

    if not job_offers or len(job_offers) == 0:
        raise ValueError("No job offers provided to rank.")

    model = settings.openai_model

    # Format job offers for analysis
    offers_text = ""
    for i, offer in enumerate(job_offers, 1):
        offers_text += f"\n{i}. {offer.get('intitule', 'Unknown Position')}  - {offer.get(
            'entreprise_nom', 'Unknown Company')} \n"
        offers_text += f"   Location: {offer.get('lieuTravail_libelle', 'N/A')}\n"
        offers_text += f"   Contract: {offer.get('typeContratLibelle', 'N/A')}\n"
        offers_text += f"   Description: {offer.get('description', 'N/A')[:200]}...\n"
        offers_text += f"   Salary: {offer.get('salaire_libelle', 'N/A')}\n"

    prompt = f"""
        You are a professional job matching expert. Analyze the following CV and job offers, then rank them by relevance and match quality.

USER'S CV:
---
        {cv_text} 
---

"""

    if preferences:
        prompt += f"USER'S PREFERENCES: {preferences}\n\n"

    prompt += f"""AVAILABLE JOB OFFERS:
---
{offers_text}
---

Analyze each offer against the CV and preferences. Score each on a scale of 0-100 based on:
1. Skills match (alignment of required skills with CV)
2. Experience level match (seniority and years of experience)
3. Location fit (proximity and user preferences)
4. Contract type alignment (CDI/CDD/etc preferences)
5. Salary expectations (if mentioned)
6. Career progression (does it advance the user's career goals)
7. Company culture fit (based on CV history)

Return a JSON array with the top {top_k} offers, each containing:
- position: offer number
- title: job title
- company: company name
- location: work location
- score: overall match score (0-100)
- match_reasons: brief list of 2-3 key reasons why this is a good match
- concerns: any potential concerns or mismatches (if any)

IMPORTANT: Return ONLY the JSON array, no other text or explanation."""

    try:
        result = await _call_llm(
            prompt=prompt,
            system_content="You are an expert job matching analyst. Analyze CVs and job offers to identify the best matches. Return only valid JSON with no additional text.",
            temperature=0.5,
            max_tokens=4000,
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

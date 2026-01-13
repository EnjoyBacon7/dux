import logging
from typing import Optional
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
    user_query: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> dict:
    """
    Use LLM to match and analyze user profile based on CV
    
    Args:
        cv_text: Extracted text from CV
        user_query: Optional user query/preferences
        model: Optional model name (defaults to settings.openai_model)
        base_url: Optional base URL (defaults to settings.openai_base_url)
        api_key: Optional API key (defaults to settings.openai_api_key)
        
    Returns:
        dict: LLM response with analysis and matches
    """
    if not cv_text or not cv_text.strip():
        raise ValueError("CV text is empty. Please upload a valid CV first.")
    
    model = model or settings.openai_model
    
    try:
        client = get_openai_client(base_url=base_url, api_key=api_key)
        prompt = create_profile_match_prompt(cv_text, user_query)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert career advisor and job matching specialist."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        analysis = response.choices[0].message.content
        
        return {
            "success": True,
            "analysis": analysis,
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
        logger.error(f"Unexpected error in profile matching: {str(e)}")
        raise ValueError(f"Profile matching failed: {str(e)}")

"""
LinkedIn OAuth integration
"""
import secrets
from typing import Dict, Optional
from urllib.parse import urlencode
import httpx
from fastapi import HTTPException

from server.config import settings


# In-memory store for OAuth state (in production, use Redis or database)
oauth_states: Dict[str, dict] = {}


def generate_authorization_url() -> str:
    """
    Generate LinkedIn OAuth authorization URL for login/signup

    Returns:
        LinkedIn authorization URL
    """
    # Generate a random state parameter for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state for validation in callback
    oauth_states[state] = {
        'created_at': secrets.token_urlsafe(16)  # Simple timestamp placeholder
    }

    # LinkedIn OAuth parameters
    params = {
        'response_type': 'code',
        'client_id': settings.linkedin_client_id,
        'redirect_uri': settings.linkedin_redirect_uri,
        'state': state,
        'scope': 'openid profile'  # OpenID Connect scopes
    }

    authorization_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return authorization_url


async def exchange_code_for_token(code: str) -> str:
    """
    Exchange authorization code for access token

    Args:
        code: The authorization code from LinkedIn

    Returns:
        Access token

    Raises:
        HTTPException: If token exchange fails
    """
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': settings.linkedin_redirect_uri,
        'client_id': settings.linkedin_client_id,
        'client_secret': settings.linkedin_client_secret
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

        if response.status_code != 200:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get('error_description', error_json.get('error', error_detail))
            except Exception:
                pass
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to exchange code for token: {error_detail}"
            )

        token_data = response.json()
        return token_data['access_token']


async def get_linkedin_profile(access_token: str) -> Dict[str, Optional[str]]:
    """
    Retrieve user profile from LinkedIn API

    Args:
        access_token: LinkedIn access token

    Returns:
        Dictionary with profile data (first_name, last_name, title, profile_picture, linkedin_id)

    Raises:
        HTTPException: If profile retrieval fails
    """
    profile_url = "https://api.linkedin.com/v2/userinfo"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(profile_url, headers=headers)

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to retrieve LinkedIn profile")

        profile_data = response.json()

        # Extract relevant fields
        return {
            'first_name': profile_data.get('given_name'),
            'last_name': profile_data.get('family_name'),
            'title': None,  # LinkedIn API v2 doesn't provide job title in basic profile
            'profile_picture': profile_data.get('picture'),
            'linkedin_id': profile_data.get('sub')  # LinkedIn user ID
        }


def validate_state(state: str) -> bool:
    """
    Validate OAuth state parameter

    Args:
        state: The state parameter from OAuth callback

    Returns:
        True if valid, False otherwise
    """
    if state not in oauth_states:
        return False

    oauth_states.pop(state)  # Remove state after validation
    return True

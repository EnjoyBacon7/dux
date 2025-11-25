from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from server.database import get_db_session
from server.config import settings
from server.models import User
from server.methods.passkey_auth import (
    get_passkey_register_options,
    verify_passkey_registration,
    get_passkey_login_options,
    verify_passkey_login,
    PasskeyRegisterOptionsRequest,
    PasskeyRegisterVerifyRequest,
    PasskeyLoginOptionsRequest,
    PasskeyLoginVerifyRequest
)
from server.methods.password_auth import (
    register_user_with_password,
    login_user_with_password,
    PasswordRegisterRequest,
    PasswordLoginRequest
)

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def apply_rate_limit(limit: str):
    """
    Conditionally apply rate limiting decorator.
    Only applies rate limits if rate_limit_enabled is True in settings.

    Args:
        limit: Rate limit string (e.g., "5/minute")

    Returns:
        Decorator function
    """
    def decorator(func):
        if settings.rate_limit_enabled:
            return limiter.limit(limit)(func)
        return func
    return decorator


# Password Authentication Endpoints

@router.post("/register", summary="Register with password")
@apply_rate_limit("5/minute")
async def password_register(
    data: PasswordRegisterRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Register a new user with username and password."""
    return await register_user_with_password(data, db)


@router.post("/login", summary="Login with password")
@apply_rate_limit("10/minute")
async def password_login(
    data: PasswordLoginRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Authenticate user with username and password."""
    return await login_user_with_password(data, request, db)


# Passkey Authentication Endpoints

@router.post("/passkey/register-options", summary="Get passkey registration options")
@apply_rate_limit("5/minute")
async def passkey_register_options(
    data: PasskeyRegisterOptionsRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Get WebAuthn registration options for creating a new passkey."""
    return await get_passkey_register_options(data, db)


@router.post("/passkey/register-verify", summary="Verify passkey registration")
@apply_rate_limit("5/minute")
async def passkey_register_verify(
    data: PasskeyRegisterVerifyRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Verify and store a new passkey credential."""
    return await verify_passkey_registration(data, db)


@router.post("/passkey/login-options", summary="Get passkey login options")
@apply_rate_limit("10/minute")
async def passkey_login_options(
    data: PasskeyLoginOptionsRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Get WebAuthn authentication options for passkey login."""
    return await get_passkey_login_options(data, db)


@router.post("/passkey/login-verify", summary="Verify passkey login")
@apply_rate_limit("10/minute")
async def passkey_login_verify(
    data: PasskeyLoginVerifyRequest,
    request: Request,
    db: Session = Depends(get_db_session)
):
    """Verify a passkey authentication attempt."""
    return await verify_passkey_login(data, request, db)


# Session Management Endpoints

@router.get("/me", summary="Get current user")
async def get_current_user(request: Request, db: Session = Depends(get_db_session)):
    """Get the currently logged-in user's information."""
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user.username,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "title": user.title,
        "profile_picture": user.profile_picture
    }


@router.post("/logout", summary="Logout")
async def logout(request: Request):
    """Log out the current user by clearing the session."""
    request.session.clear()
    return {"success": True, "message": "Logged out successfully"}


# LinkedIn OAuth Endpoints

@router.get("/linkedin/authorize", summary="Initiate LinkedIn OAuth")
@apply_rate_limit("10/minute")
async def linkedin_authorize(request: Request):
    """
    Generate LinkedIn OAuth authorization URL for login/signup.
    No authentication required - this is used to authenticate with LinkedIn.
    """
    from server.methods.linkedin_oauth import generate_authorization_url

    # Generate authorization URL (no user_id needed)
    authorization_url = generate_authorization_url()

    return {"authorization_url": authorization_url}


@router.post("/linkedin/callback", summary="LinkedIn OAuth callback")
@apply_rate_limit("10/minute")
async def linkedin_callback(request: Request, db: Session = Depends(get_db_session)):
    """
    Handle LinkedIn OAuth callback for login/signup.
    Creates new user or logs in existing user based on LinkedIn profile.
    """
    from server.methods.linkedin_oauth import (
        exchange_code_for_token,
        get_linkedin_profile,
        validate_state
    )

    # Get code and state from request body
    body = await request.json()
    code = body.get("code")
    state = body.get("state")

    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is required")

    if not state:
        raise HTTPException(status_code=400, detail="State parameter is required")

    # Validate state for CSRF protection
    if not validate_state(state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        # Exchange code for access token
        access_token = await exchange_code_for_token(code)

        # Get LinkedIn profile data
        profile_data = await get_linkedin_profile(access_token)

        linkedin_id = profile_data.get('linkedin_id')
        if not linkedin_id:
            raise HTTPException(status_code=400, detail="LinkedIn profile ID not found")

        # Check if user exists with this LinkedIn ID
        user = db.query(User).filter(User.linkedin_id == linkedin_id).first()

        if user:
            # Existing user - log them in
            request.session["username"] = user.username
            message = "Logged in successfully"
        else:
            # New user - create account
            # Generate username from LinkedIn profile
            base_username = profile_data.get('first_name', '').lower() + profile_data.get('last_name', '').lower()
            base_username = ''.join(c for c in base_username if c.isalnum())

            # Ensure username is unique
            username = base_username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1

            # Create new user
            user = User(
                username=username,
                linkedin_id=linkedin_id,
                first_name=profile_data.get('first_name'),
                last_name=profile_data.get('last_name'),
                profile_picture=profile_data.get('profile_picture'),
                password_hash=None  # No password for LinkedIn-only users
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Log the new user in
            request.session["username"] = user.username
            message = "Account created and logged in successfully"

        return {
            "success": True,
            "message": message,
            "user": {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "profile_picture": user.profile_picture
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to authenticate with LinkedIn: {str(e)}")

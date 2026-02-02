from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from server.database import get_db_session
from server.config import settings
from server.models import User
from server.utils.dependencies import get_current_user
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
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get the currently logged-in user's information."""
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "title": current_user.title,
        "profile_picture": current_user.profile_picture,
        "profile_setup_completed": current_user.profile_setup_completed or False,
        "cv_filename": current_user.cv_filename,
        "matching_context": current_user.matching_context
    }


@router.post("/logout", summary="Logout")
async def logout(request: Request):
    """Log out the current user by clearing the session."""
    request.session.clear()
    return {"success": True, "message": "Logged out successfully"}


@router.post("/password/setup", summary="Setup password for account")
@apply_rate_limit("5/minute")
async def setup_password(request: Request, db: Session = Depends(get_db_session)):
    """
    Add a password to an account that doesn't have one (e.g., LinkedIn-only accounts).
    Requires authentication.
    """
    from server.validators import validate_password
    from passlib.hash import argon2

    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.password_hash:
        raise HTTPException(status_code=400, detail="Password already set for this account")

    body = await request.json()
    password = body.get("password")

    if not password:
        raise HTTPException(status_code=400, detail="Password is required")

    # Validate password
    is_valid, error_message = validate_password(password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    # Hash and set password
    user.password_hash = argon2.hash(password)
    db.commit()

    # Update session to ensure user_id is set
    request.session["user_id"] = user.id

    return {
        "success": True,
        "message": "Password set successfully"
    }


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

        # If a user is already authenticated, link LinkedIn instead of creating a new account
        session_username = request.session.get("username")
        if session_username:
            session_user = db.query(User).filter(User.username == session_username).first()

            # Session could be stale (user deleted); in that case continue with normal flow
            if session_user:
                if session_user.linkedin_id:
                    raise HTTPException(status_code=400, detail="LinkedIn already linked to this account")

                existing_user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
                if existing_user and existing_user.id != session_user.id:
                    raise HTTPException(
                        status_code=400, detail="This LinkedIn account is already linked to another user")

                session_user.linkedin_id = linkedin_id
                if not session_user.first_name and profile_data.get('first_name'):
                    session_user.first_name = profile_data['first_name']
                if not session_user.last_name and profile_data.get('last_name'):
                    session_user.last_name = profile_data['last_name']
                if not session_user.profile_picture and profile_data.get('profile_picture'):
                    session_user.profile_picture = profile_data['profile_picture']

                db.commit()
                db.refresh(session_user)

                request.session["username"] = session_user.username
                request.session["user_id"] = session_user.id

                return {
                    "success": True,
                    "message": "LinkedIn linked successfully",
                    "user": {
                        "username": session_user.username,
                        "first_name": session_user.first_name,
                        "last_name": session_user.last_name,
                        "profile_picture": session_user.profile_picture
                    }
                }

        # Check if user exists with this LinkedIn ID
        user = db.query(User).filter(User.linkedin_id == linkedin_id).first()

        if user:
            # Existing user - log them in
            request.session["username"] = user.username
            request.session["user_id"] = user.id
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
                password_hash=None,  # No password for LinkedIn-only users
                profile_setup_completed=True  # LinkedIn users skip profile setup
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Log the new user in
            request.session["username"] = user.username
            request.session["user_id"] = user.id
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


@router.get("/methods", summary="Get user's authentication methods")
async def get_auth_methods(request: Request, db: Session = Depends(get_db_session)):
    """
    Get which authentication methods the current user has configured.
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check which auth methods are configured
    has_password = user.password_hash is not None
    has_passkey = len(user.passkey_credentials) > 0
    has_linkedin = user.linkedin_id is not None

    return {
        "hasPassword": has_password,
        "hasPasskey": has_passkey,
        "hasLinkedIn": has_linkedin
    }


@router.get("/linkedin/link", summary="Link LinkedIn to existing account")
@apply_rate_limit("10/minute")
async def linkedin_link(request: Request, db: Session = Depends(get_db_session)):
    """
    Generate LinkedIn OAuth URL for linking LinkedIn to an existing account.
    User must be authenticated.
    """
    from server.methods.linkedin_oauth import generate_authorization_url

    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.linkedin_id:
        raise HTTPException(status_code=400, detail="LinkedIn already linked to this account")

    authorization_url = generate_authorization_url()
    return {"authorization_url": authorization_url}


@router.post("/linkedin/link/callback", summary="LinkedIn link callback")
@apply_rate_limit("10/minute")
async def linkedin_link_callback(request: Request, db: Session = Depends(get_db_session)):
    """
    Handle LinkedIn OAuth callback for linking to existing account.
    """
    from server.methods.linkedin_oauth import (
        exchange_code_for_token,
        get_linkedin_profile,
        validate_state
    )

    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.linkedin_id:
        raise HTTPException(status_code=400, detail="LinkedIn already linked to this account")

    body = await request.json()
    code = body.get("code")
    state = body.get("state")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state parameter")

    if not validate_state(state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        access_token = await exchange_code_for_token(code)
        profile_data = await get_linkedin_profile(access_token)

        linkedin_id = profile_data.get('linkedin_id')
        if not linkedin_id:
            raise HTTPException(status_code=400, detail="LinkedIn profile ID not found")

        # Check if LinkedIn ID is already linked to another account
        existing_user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=400, detail="This LinkedIn account is already linked to another user")

        # Link LinkedIn to current user
        user.linkedin_id = linkedin_id
        if not user.first_name and profile_data.get('first_name'):
            user.first_name = profile_data['first_name']
        if not user.last_name and profile_data.get('last_name'):
            user.last_name = profile_data['last_name']
        if not user.profile_picture and profile_data.get('profile_picture'):
            user.profile_picture = profile_data['profile_picture']

        db.commit()

        return {
            "success": True,
            "message": "LinkedIn linked successfully",
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
        raise HTTPException(status_code=500, detail=f"Failed to link LinkedIn: {str(e)}")


# Debug Endpoint

@router.get("/debug/user-info", summary="Get all user debug information")
async def get_user_debug_info(request: Request, db: Session = Depends(get_db_session)):
    """
    Get all user information for debugging purposes.
    Returns comprehensive user data including auth methods, credentials, and login history.
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get passkey credentials
    passkeys = []
    for credential in user.passkey_credentials:
        passkeys.append({
            "id": credential.id,
            "credential_id": credential.credential_id[:16] + "...",
            "sign_count": credential.sign_count,
            "transports": credential.transports,
            "created_at": credential.created_at.isoformat() if credential.created_at else None,
            "last_used_at": credential.last_used_at.isoformat() if credential.last_used_at else None
        })

    # Get recent login attempts (last 10)
    recent_logins = []
    for attempt in sorted(user.login_attempts, key=lambda x: x.attempted_at, reverse=True)[:10]:
        recent_logins.append({
            "id": attempt.id,
            "success": attempt.success,
            "ip_address": attempt.ip_address,
            "user_agent": attempt.user_agent,
            "attempted_at": attempt.attempted_at.isoformat() if attempt.attempted_at else None
        })

    return {
        "user_info": {
            "id": user.id,
            "username": user.username,
            "has_password": bool(user.password_hash),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "is_active": user.is_active,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "title": user.title,
            "profile_picture": user.profile_picture,
            "linkedin_id": user.linkedin_id,
            "failed_login_attempts": user.failed_login_attempts,
            "locked_until": user.locked_until.isoformat() if user.locked_until else None
        },
        "passkey_credentials": passkeys,
        "recent_login_attempts": recent_logins,
        "session_info": {
            "username": request.session.get("username"),
            "session_keys": list(request.session.keys())
        }
    }


@router.delete("/account", summary="Delete user account")
@apply_rate_limit("3/hour")
async def delete_account(request: Request, db: Session = Depends(get_db_session)):
    """
    Delete the current user's account permanently.
    This action cannot be undone and will remove all associated data.
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Delete user (cascade will handle related records)
        db.delete(user)
        db.commit()

        # Clear session
        request.session.clear()

        return {
            "success": True,
            "message": "Account deleted successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")


@router.patch("/profile", summary="Update user profile")
@apply_rate_limit("30/minute")
async def update_user_profile(
    request: Request,
    db: Session = Depends(get_db_session),
    background_tasks: BackgroundTasks = None
):
    """
    Update user profile information.
    Supports updating: first_name, last_name, title, matching_context, etc.
    When matching_context is updated, triggers optimal offers regeneration.
    """
    from fastapi import BackgroundTasks as BT
    if background_tasks is None:
        background_tasks = BT()
    
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        body = await request.json()

        # Track if matching_context changed
        matching_context_changed = (
            "matching_context" in body and 
            body["matching_context"] != user.matching_context
        )

        # Update allowed fields
        allowed_fields = {
            "first_name",
            "last_name",
            "title",
            "matching_context",
            "headline",
            "summary",
            "location",
            "industry"
        }

        for field in allowed_fields:
            if field in body:
                setattr(user, field, body[field])

        db.commit()

        result = {
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "title": user.title,
                "matching_context": user.matching_context
            }
        }

        # Trigger optimal offers regeneration if matching_context changed and user has CV
        if matching_context_changed and user.cv_text:
            from server.scheduler import generate_optimal_offers_for_user
            from server.database import SessionLocal
            import logging
            logger = logging.getLogger(__name__)

            def generate_offers_task():
                """Background task to regenerate optimal offers after matching context update."""
                import asyncio
                db_session = SessionLocal()
                try:
                    asyncio.run(generate_optimal_offers_for_user(user.id, db_session))
                    logger.info(f"Optimal offers regeneration triggered for user {user.id} after matching_context update")
                except Exception as e:
                    logger.error(f"Error regenerating optimal offers for user {user.id}: {str(e)}")
                finally:
                    db_session.close()

            background_tasks.add_task(generate_offers_task)
            result["optimal_offers_status"] = "regenerating"

        return result
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")

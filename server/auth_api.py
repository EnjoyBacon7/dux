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

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Password Authentication
@router.post("/register", summary="Register with password")
@limiter.limit("5/minute")
async def password_register(data: PasswordRegisterRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Register a new user with username and password.

    Args:
        data: Contains username and password

    Returns:
        dict: Registration result
    """
    try:
        return await register_user_with_password(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@router.post("/login", summary="Login with password")
@limiter.limit("10/minute")
async def password_login(data: PasswordLoginRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Authenticate user with username and password.

    Args:
        data: Contains username and password

    Returns:
        dict: Authentication result with user info
    """
    try:
        return await login_user_with_password(data, request, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# Passkey Authentication
@router.post("/passkey/register-options", summary="Get passkey registration options")
@limiter.limit("5/minute")
async def passkey_register_options(data: PasskeyRegisterOptionsRequest, request: Request,
                                   db: Session = Depends(get_db_session)):
    """
    Get WebAuthn registration options for creating a new passkey.

    Args:
        data: Contains username

    Returns:
        dict: WebAuthn registration options
    """
    try:
        return await get_passkey_register_options(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate registration options: {str(e)}")


@router.post("/passkey/register-verify", summary="Verify passkey registration")
@limiter.limit("5/minute")
async def passkey_register_verify(data: PasskeyRegisterVerifyRequest, request: Request,
                                  db: Session = Depends(get_db_session)):
    """
    Verify and store a new passkey credential.

    Args:
        data: Contains username and credential data

    Returns:
        dict: Registration result
    """
    try:
        return await verify_passkey_registration(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Passkey registration verification failed: {str(e)}")


@router.post("/passkey/login-options", summary="Get passkey login options")
@limiter.limit("10/minute")
async def passkey_login_options(
        data: PasskeyLoginOptionsRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Get WebAuthn authentication options for passkey login.

    Args:
        data: Contains username

    Returns:
        dict: WebAuthn authentication options
    """
    try:
        return await get_passkey_login_options(data, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate login options: {str(e)}")


@router.post("/passkey/login-verify", summary="Verify passkey login")
@limiter.limit("10/minute")
async def passkey_login_verify(
        data: PasskeyLoginVerifyRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Verify a passkey authentication attempt.

    Args:
        data: Contains username and credential data

    Returns:
        dict: Authentication result
    """
    try:
        return await verify_passkey_login(data, request, db)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Passkey login verification failed: {str(e)}")


# Session Management
@router.get("/me", summary="Get current user")
async def get_current_user(request: Request, db: Session = Depends(get_db_session)):
    """
    Get the currently logged-in user's information.

    Returns:
        dict: User info if logged in, otherwise 401
    """
    try:
        if "username" not in request.session:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Fetch full user data from database
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user data: {str(e)}")


@router.post("/logout", summary="Logout")
async def logout(request: Request):
    """
    Log out the current user by clearing the session.

    Returns:
        dict: Logout success message
    """
    try:
        request.session.clear()
        return {"success": True, "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

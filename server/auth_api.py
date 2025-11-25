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
    """
    return await register_user_with_password(data, db)


@router.post("/login", summary="Login with password")
@limiter.limit("10/minute")
async def password_login(data: PasswordLoginRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Authenticate user with username and password.
    """
    return await login_user_with_password(data, request, db)


# Passkey Authentication
@router.post("/passkey/register-options", summary="Get passkey registration options")
@limiter.limit("5/minute")
async def passkey_register_options(data: PasskeyRegisterOptionsRequest, request: Request,
                                   db: Session = Depends(get_db_session)):
    """
    Get WebAuthn registration options for creating a new passkey.
    """
    return await get_passkey_register_options(data, db)


@router.post("/passkey/register-verify", summary="Verify passkey registration")
@limiter.limit("5/minute")
async def passkey_register_verify(data: PasskeyRegisterVerifyRequest, request: Request,
                                  db: Session = Depends(get_db_session)):
    """
    Verify and store a new passkey credential.
    """
    return await verify_passkey_registration(data, db)


@router.post("/passkey/login-options", summary="Get passkey login options")
@limiter.limit("10/minute")
async def passkey_login_options(data: PasskeyLoginOptionsRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Get WebAuthn authentication options for passkey login.
    """
    return await get_passkey_login_options(data, db)


@router.post("/passkey/login-verify", summary="Verify passkey login")
@limiter.limit("10/minute")
async def passkey_login_verify(data: PasskeyLoginVerifyRequest, request: Request, db: Session = Depends(get_db_session)):
    """
    Verify a passkey authentication attempt.
    """
    return await verify_passkey_login(data, request, db)


# Session Management
@router.get("/me", summary="Get current user")
async def get_current_user(request: Request, db: Session = Depends(get_db_session)):
    """
    Get the currently logged-in user's information.
    """
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
    """
    Log out the current user by clearing the session.
    """
    request.session.clear()
    return {"success": True, "message": "Logged out successfully"}

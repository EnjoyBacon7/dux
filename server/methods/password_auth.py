"""
Password-based authentication methods.

Provides user registration and login functionality using username/password
authentication with security features like account lockout and login attempt tracking.
"""

from typing import Dict, Any

from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.hash import argon2
from datetime import datetime, timedelta, timezone

from server.database import get_db_session
from server.models import User, LoginAttempt
from server.config import settings
from server.validators import validate_username, validate_password

# ============================================================================
# Request Models
# ============================================================================


class PasswordRegisterRequest(BaseModel):
    """Request body for password registration endpoint."""
    username: str
    password: str


class PasswordLoginRequest(BaseModel):
    """Request body for password login endpoint."""
    username: str
    password: str


# ============================================================================
# Security Helpers
# ============================================================================


def _perform_timing_attack_prevention() -> None:
    """
    Dummy password hash to prevent timing attacks.

    Even when a user doesn't exist, we perform a hash operation
    to maintain consistent timing across success and failure paths.
    """
    argon2.hash("dummy_password_to_prevent_timing_attack")


def _check_account_lockout(user: User) -> None:
    """
    Check if user account is locked and clear lockout if expired.

    Args:
        user: The user to check

    Raises:
        HTTPException: If account is currently locked
    """
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        time_remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(
            status_code=429,
            detail=f"Account is temporarily locked. Try again in {time_remaining} minutes."
        )

    # Clear lockout if time has passed
    if user.locked_until and user.locked_until <= datetime.now(timezone.utc):
        user.locked_until = None
        user.failed_login_attempts = 0


def _handle_failed_login(user: User, db: Session) -> None:
    """
    Handle failed login attempt including account lockout.

    Args:
        user: The user with failed login
        db: Database session

    Raises:
        HTTPException: If account becomes locked
    """
    user.failed_login_attempts += 1

    # Lock account if too many failed attempts
    if user.failed_login_attempts >= settings.max_login_attempts:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.lockout_duration_minutes)
        db.commit()
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Account locked for {settings.lockout_duration_minutes} minutes."
        )
    db.commit()


def _handle_successful_login(user: User, req: Request, db: Session) -> None:
    """
    Handle successful login including session setup and failed attempts reset.

    Args:
        user: The authenticated user
        req: FastAPI request object for session
        db: Database session
    """
    # Reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # Regenerate session to prevent session fixation
    req.session.clear()
    req.session["user_id"] = user.id
    req.session["username"] = user.username
    req.session["authenticated_at"] = datetime.now(timezone.utc).isoformat()


# ============================================================================
# Registration and Login Methods
# ============================================================================


async def register_user_with_password(
    request: PasswordRegisterRequest,
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Register a new user with username and password.

    Validates username and password strength, then creates a new user
    with an argon2-hashed password.

    Args:
        request: PasswordRegisterRequest with username and password
        db: Database session

    Returns:
        dict: Success message with username

    Raises:
        HTTPException: If validation fails or username already exists
    """
    username = request.username.strip() if request.username else ""
    password = request.password if request.password else ""

    # Validate username
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Check if user already exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Validate password strength
    is_valid, error_msg = validate_password(
        password,
        min_length=settings.password_min_length,
        require_uppercase=settings.password_require_uppercase,
        require_lowercase=settings.password_require_lowercase,
        require_digit=settings.password_require_digit,
        require_special=settings.password_require_special
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Create new user with hashed password
    new_user = User(username=username, password_hash=argon2.hash(password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "success": True,
        "message": "User registered successfully",
        "username": username
    }


async def login_user_with_password(
    request: PasswordLoginRequest,
    req: Request,
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Authenticate user with username and password.

    Validates credentials, handles account lockout, records login attempts,
    and establishes session on successful authentication.

    Args:
        request: PasswordLoginRequest with username and password
        req: FastAPI request object for session and client info
        db: Database session

    Returns:
        dict: Success message with username

    Raises:
        HTTPException: If validation fails, credentials invalid, or account locked
    """
    username = request.username.strip() if request.username else ""
    password = request.password if request.password else ""

    # Validate username format
    is_valid, error_msg = validate_username(username)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    # Get user from database
    user = db.query(User).filter(User.username == username).first()

    # Check password (or dummy hash to prevent timing attacks)
    password_valid = False
    if user:
        _check_account_lockout(user)

        # Verify password if user has one
        if user.password_hash:
            password_valid = argon2.verify(password, user.password_hash)
    else:
        # Dummy hash to prevent timing attacks
        _perform_timing_attack_prevention()

    # Record login attempt
    if user:
        attempt = LoginAttempt(
            user_id=user.id,
            success=password_valid,
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent", "")
        )
        db.add(attempt)

    # Handle failed login
    if not password_valid or not user:
        if user:
            _handle_failed_login(user, db)

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login
    _handle_successful_login(user, req, db)

    return {
        "success": True,
        "message": "Login successful",
        "username": username
    }

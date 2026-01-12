from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.hash import argon2
from datetime import datetime, timedelta, timezone

from server.database import get_db_session
from server.models import User, LoginAttempt
from server.config import settings
from server.validators import validate_username, validate_password


class PasswordRegisterRequest(BaseModel):
    username: str
    password: str


class PasswordLoginRequest(BaseModel):
    username: str
    password: str


async def register_user_with_password(request: PasswordRegisterRequest, db: Session = Depends(get_db_session)):
    """
    Register a new user with username and password
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


async def login_user_with_password(request: PasswordLoginRequest, req: Request, db: Session = Depends(get_db_session)):
    """
    Authenticate user with username and password
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
        # Check if account is locked
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
            db.commit()

        # Verify password if user has one
        if user.password_hash:
            password_valid = argon2.verify(password, user.password_hash)
    else:
        # Dummy hash to prevent timing attacks
        argon2.hash("dummy_password_to_prevent_timing_attack")

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
            user.failed_login_attempts += 1

            # Lock account if too many failed attempts
            if user.failed_login_attempts >= settings.max_login_attempts:
                user.locked_until = datetime.utcnow() + timedelta(minutes=settings.lockout_duration_minutes)
                db.commit()
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many failed login attempts. Account locked for {settings.lockout_duration_minutes} minutes."
                )
            db.commit()

        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Successful login - reset failed attempts
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # Regenerate session to prevent session fixation
    req.session.clear()
    req.session["user_id"] = user.id
    req.session["username"] = user.username
    req.session["authenticated_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "success": True,
        "message": "Login successful",
        "username": username
    }

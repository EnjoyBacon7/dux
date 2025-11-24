from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from passlib.hash import argon2
from datetime import datetime, timedelta

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
    try:
        username = request.username
        password = request.password

        # Validate username
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
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

        # Hash password with Argon2
        password_hash = argon2.hash(password)

        # Create new user
        new_user = User(
            username=username,
            password_hash=password_hash
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "success": True,
            "message": "User registered successfully",
            "username": username
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


async def login_user_with_password(request: PasswordLoginRequest, req: Request, db: Session = Depends(get_db_session)):
    """
    Authenticate user with username and password
    """
    try:
        username = request.username
        password = request.password

        # Get user from database
        user = db.query(User).filter(User.username == username).first()

        # Use timing-safe comparison by always checking password even if user doesn't exist
        # This prevents username enumeration through timing attacks
        password_valid = False
        account_locked = False

        if user:
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                account_locked = True
                time_remaining = (user.locked_until - datetime.utcnow()).seconds // 60
                raise HTTPException(
                    status_code=429,
                    detail=f"Account is temporarily locked. Try again in {time_remaining} minutes."
                )

            # Clear lockout if time has passed
            if user.locked_until and user.locked_until <= datetime.utcnow():
                user.locked_until = None
                user.failed_login_attempts = 0
                db.commit()

            # Check if user has a password set
            if user.password_hash:
                password_valid = argon2.verify(password, user.password_hash)
        else:
            # Perform dummy hash to prevent timing attacks
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

            # Generic error message to prevent username enumeration
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()

        # Regenerate session to prevent session fixation
        old_session = dict(req.session)
        req.session.clear()

        # Set new session
        req.session["user_id"] = user.id
        req.session["username"] = user.username
        req.session["authenticated_at"] = datetime.utcnow().isoformat()

        return {
            "success": True,
            "message": "Login successful",
            "username": username
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

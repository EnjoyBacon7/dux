"""
Shared FastAPI dependencies used across routers.

Provides common dependency functions for authentication, database access, etc.
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from server.database import get_db_session
from server.models import User


def get_current_user(request: Request, db: Session = Depends(get_db_session)) -> User:
    """
    Dependency to extract and validate the current authenticated user from session.

    Used across routers to ensure endpoints are only accessible to authenticated users.

    Args:
        request: FastAPI request object containing session
        db: Database session

    Returns:
        User: The currently authenticated user

    Raises:
        HTTPException: If user is not authenticated or not found in database
    """
    if "username" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(User).filter(User.username == request.session["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

"""
API routers package.

This package contains specialized routers for different API functionalities:
- chat_router: LLM-powered profile matching and chat
- profile_router: User profile management and CV upload
- jobs_router: Job search integration with France Travail API
"""

from . import chat_router, profile_router, jobs_router, metiers_router

__all__ = ["chat_router", "profile_router", "jobs_router", "metiers_router"]

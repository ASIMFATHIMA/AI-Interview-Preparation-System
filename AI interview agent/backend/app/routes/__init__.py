"""
API route definitions and endpoints package.
"""
from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router
from app.routes.resume import router as resume_router
from app.routes.resume_parsed import router as resume_parsed_router

__all__ = [
    "auth_router",
    "profile_router",
    "resume_router",
    "resume_parsed_router",
]

"""API v1 routes"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import and include routers
from app.api.v1 import auth, users, skills, projects, applications, offers, matches

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(applications.router, prefix="", tags=["applications"])
api_router.include_router(offers.router, prefix="", tags=["offers"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])


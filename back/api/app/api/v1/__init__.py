"""API v1 routes"""
from fastapi import APIRouter

# Create main API router
api_router = APIRouter()

# Import and include routers
from app.api.v1 import auth, users, skills, projects, applications, offers, matches, me, group_chats

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(offers.router, prefix="/offers", tags=["offers"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(me.router, prefix="/me", tags=["me"])
api_router.include_router(group_chats.router, prefix="/group-chats", tags=["group-chats"])


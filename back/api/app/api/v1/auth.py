"""Authentication endpoints"""
import logging
from typing import Optional
import urllib.parse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.database import get_db
from app.core.security import create_access_token
from app.core.deps import get_current_user
from app.services.github_service import GitHubService
from app.models.user import User, OAuthAccount
from app.models.audit import AuditLog
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _generate_unique_handle(db: Session, base_handle: str) -> str:
    """
    Generate a unique user handle by appending an incrementing suffix when necessary.

    Args:
        db: Database session
        base_handle: Preferred handle (typically GitHub login)

    Returns:
        Unique handle string
    """
    candidate = base_handle
    suffix = 1

    while db.query(User.id).filter(User.handle == candidate).first():
        candidate = f"{base_handle}-{suffix}"
        suffix += 1

    return candidate


def _locate_existing_user(
    db: Session,
    github_login: str,
    primary_email: Optional[str]
) -> Optional[User]:
    """
    Attempt to locate an existing user that should be linked to the GitHub account.

    Args:
        db: Database session
        github_login: GitHub username
        primary_email: Primary GitHub email (may be None)

    Returns:
        Existing user instance or None
    """
    if primary_email:
        user = db.query(User).filter(User.email == primary_email).first()
        if user:
            return user

    return db.query(User).filter(User.github_login == github_login).first()


@router.get("/github/login")
async def github_login(state: Optional[str] = Query(None)):
    """
    Redirect to GitHub OAuth authorization page
    
    Args:
        state: Optional state parameter for CSRF protection
    
    Returns:
        Redirect to GitHub authorization URL
    """
    auth_url = GitHubService.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_callback(
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback
    
    Args:
        code: Authorization code from GitHub
        state: Optional state parameter
        db: Database session
    
    Returns:
        JWT token and user information
    """
    try:
        # Exchange code for access token
        token_data = await GitHubService.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from GitHub"
            )
        
        # Get user info from GitHub
        github_user = await GitHubService.get_user_info(access_token)
        github_id = str(github_user["id"])
        github_login = github_user["login"]
        
        # Get user emails
        emails = await GitHubService.get_user_emails(access_token)
        primary_email = next(
            (email["email"] for email in emails if email.get("primary")),
            None
        )
        
        # Check if OAuth account exists
        oauth_account = db.query(OAuthAccount).filter(
            OAuthAccount.provider == "github",
            OAuthAccount.provider_account_id == github_id
        ).first()

        if oauth_account:
            # Existing OAuth link: refresh token & user metadata
            user = oauth_account.user
            oauth_account.access_token = access_token
        else:
            # Either reuse an existing user (matched by email/github_login) or create a new one
            user = _locate_existing_user(db, github_login=github_login, primary_email=primary_email)

            if user:
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider="github",
                    provider_account_id=github_id,
                    access_token=access_token
                )
                db.add(oauth_account)
            else:
                handle = _generate_unique_handle(db, github_login)
                user = User(
                    handle=handle,
                    email=primary_email,
                    avatar_url=github_user.get("avatar_url"),
                    bio=github_user.get("bio"),
                    github_login=github_login
                )
                db.add(user)
                db.flush()

                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider="github",
                    provider_account_id=github_id,
                    access_token=access_token
                )
                db.add(oauth_account)

        # Harmonise user profile with the latest GitHub data
        user.github_login = github_login
        user.avatar_url = github_user.get("avatar_url")
        if github_user.get("bio"):
            user.bio = github_user.get("bio")
        if primary_email and (user.email is None):
            user.email = primary_email
        user.updated_at = datetime.utcnow()

        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="LOGIN",
            resource="auth",
            payload={"provider": "github", "github_login": github_login}
        )
        db.add(audit_log)
        try:
            db.commit()
        except IntegrityError as commit_error:
            db.rollback()
            logger.exception(
                "GitHub OAuth commit failed",
                extra={
                    "github_login": github_login,
                    "github_id": github_id,
                    "primary_email": primary_email
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Failed to reconcile GitHub account with existing user data"
            ) from commit_error

        db.refresh(user)

        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})

        FRONTEND_PROFILE_URL = "http://localhost:5500/public/profile.html"

        # トークンをURLハッシュ（#）として渡す準備
        fragment_data = {
            "access_token": jwt_token,
            "token_type": "bearer",
        }

        # データをURLエンコード
        fragment_string = urllib.parse.urlencode(fragment_data)

        redirect_url = f"{FRONTEND_PROFILE_URL}#{fragment_string}"
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "GitHub OAuth unexpected error",
            extra={
                "github_login": github_user.get("login") if 'github_user' in locals() else None
            }
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Current user information
    """
    return UserResponse.from_orm(current_user)


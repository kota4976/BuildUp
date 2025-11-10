"""Authentication endpoints"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
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


@router.get("/github/callback", response_model=TokenResponse)
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
            # Update existing OAuth account
            oauth_account.access_token = access_token
            user = oauth_account.user
            
            # Update user info
            user.github_login = github_login
            user.avatar_url = github_user.get("avatar_url")
            if primary_email and not user.email:
                user.email = primary_email
            user.updated_at = datetime.utcnow()
        else:
            # Create new user
            user = User(
                handle=github_login,
                email=primary_email,
                avatar_url=github_user.get("avatar_url"),
                bio=github_user.get("bio"),
                github_login=github_login
            )
            db.add(user)
            db.flush()
            
            # Create OAuth account
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider="github",
                provider_account_id=github_id,
                access_token=access_token
            )
            db.add(oauth_account)
        
        # Create audit log
        audit_log = AuditLog(
            user_id=user.id,
            action="LOGIN",
            resource="auth",
            payload={"provider": "github", "github_login": github_login}
        )
        db.add(audit_log)
        
        db.commit()
        db.refresh(user)
        
        # Create JWT token
        jwt_token = create_access_token(data={"sub": str(user.id)})
        
        return TokenResponse(
            access_token=jwt_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth error: {str(e)}")
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


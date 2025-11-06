"""GitHub OAuth service"""
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings


class GitHubService:
    """Service for GitHub OAuth and API interactions"""
    
    GITHUB_OAUTH_URL = "https://github.com/login/oauth"
    GITHUB_API_URL = "https://api.github.com"
    
    @staticmethod
    def get_authorization_url(state: Optional[str] = None) -> str:
        """
        Get GitHub OAuth authorization URL
        
        Args:
            state: Optional state parameter for CSRF protection
        
        Returns:
            Authorization URL
        """
        params = {
            "client_id": settings.github_client_id,
            "redirect_uri": settings.github_redirect_uri,
            "scope": "read:user user:email"
        }
        
        if state:
            params["state"] = state
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{GitHubService.GITHUB_OAUTH_URL}/authorize?{query_string}"
    
    @staticmethod
    async def exchange_code_for_token(code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from GitHub
        
        Returns:
            Token response from GitHub
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GitHubService.GITHUB_OAUTH_URL}/access_token",
                data={
                    "client_id": settings.github_client_id,
                    "client_secret": settings.github_client_secret,
                    "code": code,
                    "redirect_uri": settings.github_redirect_uri
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        Get GitHub user information
        
        Args:
            access_token: GitHub access token
        
        Returns:
            User information from GitHub
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.GITHUB_API_URL}/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_emails(access_token: str) -> list:
        """
        Get GitHub user email addresses
        
        Args:
            access_token: GitHub access token
        
        Returns:
            List of user email addresses
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.GITHUB_API_URL}/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_repos(access_token: str, username: str) -> list:
        """
        Get user's public repositories
        
        Args:
            access_token: GitHub access token
            username: GitHub username
        
        Returns:
            List of repositories
        
        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GitHubService.GITHUB_API_URL}/users/{username}/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                },
                params={
                    "sort": "updated",
                    "per_page": 100
                }
            )
            response.raise_for_status()
            return response.json()


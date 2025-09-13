"""
Google OAuth service for M32 Business Intelligence Copilot.
Handles Google authentication flow and user verification.
"""

import json
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from google.auth.exceptions import GoogleAuthError

from core.config import settings


class GoogleOAuthService:
    """Service for handling Google OAuth authentication."""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
            "prompt": "select_account",
            "state": state,
        }
        
        return f"{self.auth_url}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and ID tokens.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dict containing tokens and user info
            
        Raises:
            GoogleAuthError: If token exchange fails
        """
        token_data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.token_url, data=token_data)
                response.raise_for_status()
                tokens = response.json()
                
                if "error" in tokens:
                    raise GoogleAuthError(f"Token exchange failed: {tokens['error']}")
                
                return tokens
                
            except httpx.HTTPError as e:
                raise GoogleAuthError(f"HTTP error during token exchange: {str(e)}")
            except Exception as e:
                raise GoogleAuthError(f"Unexpected error during token exchange: {str(e)}")
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            Dict containing user information
            
        Raises:
            GoogleAuthError: If user info retrieval fails
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.userinfo_url, headers=headers)
                response.raise_for_status()
                user_info = response.json()
                
                if "error" in user_info:
                    raise GoogleAuthError(f"User info retrieval failed: {user_info['error']}")
                
                return user_info
                
            except httpx.HTTPError as e:
                raise GoogleAuthError(f"HTTP error during user info retrieval: {str(e)}")
            except Exception as e:
                raise GoogleAuthError(f"Unexpected error during user info retrieval: {str(e)}")
    
    def verify_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            id_token_str: Google ID token string
            
        Returns:
            Dict containing verified user information
            
        Raises:
            GoogleAuthError: If token verification fails
        """
        try:
            # Verify real Google ID token
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.client_id
            )
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise GoogleAuthError('Invalid token issuer')
            
            return idinfo
            
        except ValueError as e:
            raise GoogleAuthError(f"Invalid ID token: {str(e)}")
        except Exception as e:
            raise GoogleAuthError(f"Token verification failed: {str(e)}")
    
    async def authenticate_user(self, code: str) -> Dict[str, Any]:
        """
        Complete authentication flow: exchange code for tokens and get user info.
        
        Args:
            code: Authorization code from Google
            
        Returns:
            Dict containing user information and tokens
            
        Raises:
            GoogleAuthError: If authentication fails
        """
        # Exchange code for tokens
        tokens = await self.exchange_code_for_tokens(code)
        
        # Get user info using access token
        user_info = await self.get_user_info(tokens["access_token"])
        
        # Also verify ID token if present
        if "id_token" in tokens:
            id_token_info = self.verify_id_token(tokens["id_token"])
            # Merge information, prioritizing ID token data
            user_info.update(id_token_info)
        
        return {
            "user_info": user_info,
            "tokens": tokens
        }


# Global service instance
google_oauth_service = GoogleOAuthService()

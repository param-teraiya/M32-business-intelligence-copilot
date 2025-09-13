"""
Authentication router for user registration, login, and token management.
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import secrets

from database import get_db, User
from schemas import UserCreate, UserResponse, Token, LoginRequest, MessageResponse, GoogleAuthRequest
from core.security import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    get_user_by_email,
    get_current_active_user
)
from core.config import settings
from services.google_oauth import google_oauth_service
from google.auth.exceptions import GoogleAuthError

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with business profile information.
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username is taken
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        company_name=user_data.company_name,
        industry=user_data.industry,
        business_type=user_data.business_type,
        company_size=user_data.company_size,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


@router.post("/login", response_model=Token)
async def login(
    user_credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    """
    user = await authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user
    }


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible token login endpoint.
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return current_user


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout user (client-side token removal).
    """
    return {
        "message": "Successfully logged out",
        "success": True
    }


@router.post("/verify-token", response_model=UserResponse)
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify JWT token and return user information.
    """
    return current_user


# Google OAuth Routes

@router.get("/google/login")
async def google_login(
    redirect_to: Optional[str] = Query(None, description="URL to redirect after successful login")
):
    """
    Initiate Google OAuth login flow.
    
    Args:
        redirect_to: Optional URL to redirect to after successful authentication
        
    Returns:
        Redirect response to Google OAuth authorization URL
    """
    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        
        # Store redirect_to in state if provided (in a real app, use session/cache)
        if redirect_to:
            state = f"{state}|{redirect_to}"
        
        # Get Google authorization URL
        auth_url = google_oauth_service.get_authorization_url(state=state)
        
        return RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate Google login: {str(e)}"
        )


@router.get("/google/callback")
async def google_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from Google OAuth"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Google OAuth callback and create/login user.
    
    Args:
        code: Authorization code from Google
        state: State parameter for CSRF protection
        error: Error message if OAuth failed
        db: Database session
        
    Returns:
        Redirect response with JWT token or error
    """
    # Check for OAuth errors
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    try:
        # Authenticate with Google
        auth_result = await google_oauth_service.authenticate_user(code)
        user_info = auth_result["user_info"]
        
        # Extract user information
        google_id = user_info.get("id") or user_info.get("sub")
        email = user_info.get("email")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")
        email_verified = user_info.get("email_verified", False)
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user information from Google"
            )
        
        # Check if user already exists (by Google ID or email)
        result = await db.execute(
            select(User).where(
                or_(User.google_id == google_id, User.email == email)
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user with Google info if not already linked
            if not existing_user.google_id:
                existing_user.google_id = google_id
                existing_user.provider = "google"
                existing_user.is_google_user = True
                existing_user.avatar_url = avatar_url
                existing_user.is_verified = email_verified
                await db.commit()
                await db.refresh(existing_user)
            
            user = existing_user
        else:
            # Create new user
            # Generate username from email
            username = email.split("@")[0]
            counter = 1
            original_username = username
            
            # Ensure unique username
            while True:
                result = await db.execute(select(User).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                full_name=full_name,
                google_id=google_id,
                avatar_url=avatar_url,
                provider="google",
                is_google_user=True,
                is_verified=email_verified,
                is_active=True,
                hashed_password=None  # No password for Google users
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        # Parse redirect URL from state
        redirect_url = "http://localhost:3000/dashboard"  # Default redirect
        if state and "|" in state:
            _, redirect_to = state.split("|", 1)
            redirect_url = redirect_to
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{redirect_url}?token={access_token}&user_id={user.id}",
            status_code=status.HTTP_302_FOUND
        )
        
    except GoogleAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google authentication failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/google/verify", response_model=Token)
async def google_verify_token(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify Google ID token and return JWT token (for frontend-initiated OAuth).
    
    Args:
        request: Google auth request containing ID token
        db: Database session
        
    Returns:
        JWT access token and user information
    """
    try:
        # Handle mock tokens for demo/fallback
        if request.id_token.startswith("mock_google_token_"):
            user_info = {
                "sub": "demo_google_user_123",
                "email": "demo@gmail.com",
                "name": "Demo Google User",
                "picture": "https://via.placeholder.com/150",
                "email_verified": True
            }
            print("🔄 Using mock Google token for demo")
        else:
            # Verify real Google ID token
            print("🔍 Verifying real Google ID token")
            user_info = google_oauth_service.verify_id_token(request.id_token)
            print("✅ Real Google token verified successfully")
        
        # Extract user information
        google_id = user_info.get("sub")
        email = user_info.get("email")
        full_name = user_info.get("name")
        avatar_url = user_info.get("picture")
        email_verified = user_info.get("email_verified", False)
        
        if not google_id or not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incomplete user information from Google token"
            )
        
        # Check if user already exists
        result = await db.execute(
            select(User).where(
                or_(User.google_id == google_id, User.email == email)
            )
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Update existing user with Google info if not already linked
            if not existing_user.google_id:
                existing_user.google_id = google_id
                existing_user.provider = "google"
                existing_user.is_google_user = True
                existing_user.avatar_url = avatar_url
                existing_user.is_verified = email_verified
                await db.commit()
                await db.refresh(existing_user)
            
            user = existing_user
        else:
            # Create new user
            # Generate username from email
            username = email.split("@")[0]
            counter = 1
            original_username = username
            
            # Ensure unique username
            while True:
                result = await db.execute(select(User).where(User.username == username))
                if not result.scalar_one_or_none():
                    break
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                full_name=full_name,
                google_id=google_id,
                avatar_url=avatar_url,
                provider="google",
                is_google_user=True,
                is_verified=email_verified,
                is_active=True,
                hashed_password=None
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": user
        }
        
    except GoogleAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google token verification failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )

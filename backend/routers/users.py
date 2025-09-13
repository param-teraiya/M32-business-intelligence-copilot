"""
Users router for profile management and business context.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, User
from schemas import UserResponse, UserUpdate, BusinessContext, MessageResponse
from core.security import get_current_active_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information.
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user profile and business information.
    """
    # Update user fields
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    if profile_data.company_name is not None:
        current_user.company_name = profile_data.company_name
    if profile_data.industry is not None:
        current_user.industry = profile_data.industry
    if profile_data.business_type is not None:
        current_user.business_type = profile_data.business_type
    if profile_data.company_size is not None:
        current_user.company_size = profile_data.company_size
    
    await db.commit()
    await db.refresh(current_user)
    
    return current_user


@router.get("/business-context", response_model=BusinessContext)
async def get_business_context(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get user's business context information.
    """
    return {
        "company_name": current_user.company_name,
        "industry": current_user.industry,
        "business_type": current_user.business_type,
        "company_size": current_user.company_size
    }


@router.put("/business-context", response_model=BusinessContext)
async def update_business_context(
    context_data: BusinessContext,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user's business context information.
    """
    # Update business context fields
    if context_data.company_name is not None:
        current_user.company_name = context_data.company_name
    if context_data.industry is not None:
        current_user.industry = context_data.industry
    if context_data.business_type is not None:
        current_user.business_type = context_data.business_type
    if context_data.company_size is not None:
        current_user.company_size = context_data.company_size
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "company_name": current_user.company_name,
        "industry": current_user.industry,
        "business_type": current_user.business_type,
        "company_size": current_user.company_size
    }


@router.delete("/account", response_model=MessageResponse)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user account (soft delete - deactivate).
    """
    current_user.is_active = False
    await db.commit()
    
    return {
        "message": "Account successfully deactivated",
        "success": True
    }

"""
Financial profile management endpoints
"""

from typing import Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.financial_profile import (
    FinancialProfileCreate,
    FinancialProfileResponse,
    FinancialProfileUpdate
)
from app.services.financial_profile_service import FinancialProfileService

router = APIRouter()


@router.post("", response_model=FinancialProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_profile(
    profile_data: FinancialProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create financial profile for current user
    """
    profile_service = FinancialProfileService(db)
    
    # Check if profile already exists
    existing_profile = await profile_service.get_by_user_id(current_user.id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Financial profile already exists for this user"
        )
    
    profile = await profile_service.create_profile(current_user.id, profile_data)
    return profile


@router.get("/me", response_model=FinancialProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get financial profile for current user
    """
    profile_service = FinancialProfileService(db)
    profile = await profile_service.get_by_user_id(current_user.id)
    
    if not profile:
        raise NotFoundError("Financial profile not found")
    
    return profile


@router.put("/me", response_model=FinancialProfileResponse)
async def update_current_user_profile(
    profile_update: FinancialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update financial profile for current user
    """
    profile_service = FinancialProfileService(db)
    profile = await profile_service.update_profile(current_user.id, profile_update)
    
    if not profile:
        raise NotFoundError("Financial profile not found")
    
    return profile


@router.delete("/me")
async def delete_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete financial profile for current user
    """
    profile_service = FinancialProfileService(db)
    success = await profile_service.delete_profile(current_user.id)
    
    if not success:
        raise NotFoundError("Financial profile not found")
    
    return {"message": "Financial profile deleted successfully"}


@router.get("/analysis")
async def get_financial_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get detailed financial analysis based on current profile
    """
    profile_service = FinancialProfileService(db)
    analysis = await profile_service.get_financial_analysis(current_user.id)
    
    if not analysis:
        raise NotFoundError("Financial profile not found")
    
    return analysis
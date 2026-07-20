"""
Financial goals management endpoints
"""

from typing import Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter()


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new financial goal
    """
    goal_service = GoalService(db)
    goal = await goal_service.create_goal(current_user.id, goal_data)
    return goal


@router.get("", response_model=List[GoalResponse])
async def get_user_goals(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = Query(None, description="Filter by goal status"),
    goal_type: Optional[str] = Query(None, description="Filter by goal type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all goals for current user with optional filters
    """
    goal_service = GoalService(db)
    goals = await goal_service.get_user_goals(
        current_user.id,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        goal_type=goal_type
    )
    return goals


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific goal by ID
    """
    goal_service = GoalService(db)
    goal = await goal_service.get_goal(goal_id, current_user.id)
    
    if not goal:
        raise NotFoundError("Goal not found")
    
    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update existing goal
    """
    goal_service = GoalService(db)
    goal = await goal_service.update_goal(goal_id, current_user.id, goal_update)
    
    if not goal:
        raise NotFoundError("Goal not found")
    
    return goal


@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete goal
    """
    goal_service = GoalService(db)
    success = await goal_service.delete_goal(goal_id, current_user.id)
    
    if not success:
        raise NotFoundError("Goal not found")
    
    return {"message": "Goal deleted successfully"}


@router.post("/{goal_id}/contribute")
async def add_contribution(
    goal_id: UUID,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Add contribution to goal
    """
    goal_service = GoalService(db)
    goal = await goal_service.add_contribution(goal_id, current_user.id, amount)
    
    if not goal:
        raise NotFoundError("Goal not found")
    
    return goal


@router.get("/{goal_id}/progress")
async def get_goal_progress(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get detailed progress analysis for goal
    """
    goal_service = GoalService(db)
    progress = await goal_service.get_goal_progress(goal_id, current_user.id)
    
    if not progress:
        raise NotFoundError("Goal not found")
    
    return progress


@router.get("/summary/dashboard")
async def get_goals_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get goals dashboard summary
    """
    goal_service = GoalService(db)
    dashboard = await goal_service.get_goals_dashboard(current_user.id)
    return dashboard
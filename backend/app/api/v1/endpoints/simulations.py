"""
Financial simulation endpoints for Monte Carlo and scenario analysis
"""

from typing import Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import NotFoundError, SimulationError
from app.models.user import User
from app.schemas.simulation import (
    SimulationCreate,
    SimulationResponse,
    SimulationUpdate,
    MonteCarloRequest,
    ScenarioAnalysisRequest
)
from app.services.simulation_service import SimulationService

router = APIRouter()


@router.post("", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    simulation_data: SimulationCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Create a new financial simulation
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.create_simulation(current_user.id, simulation_data)
    
    # Run simulation in background
    background_tasks.add_task(
        simulation_service.run_simulation,
        simulation.id
    )
    
    return simulation


@router.post("/monte-carlo", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def run_monte_carlo_simulation(
    request: MonteCarloRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Run Monte Carlo simulation for retirement planning
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.create_monte_carlo_simulation(current_user.id, request)
    
    # Run simulation in background
    background_tasks.add_task(
        simulation_service.run_monte_carlo,
        simulation.id,
        request
    )
    
    return simulation


@router.post("/scenario-analysis", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def run_scenario_analysis(
    request: ScenarioAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Run scenario analysis with different market conditions
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.create_scenario_analysis(current_user.id, request)
    
    # Run simulation in background
    background_tasks.add_task(
        simulation_service.run_scenario_analysis,
        simulation.id,
        request
    )
    
    return simulation


@router.get("", response_model=List[SimulationResponse])
async def get_user_simulations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get all simulations for current user
    """
    simulation_service = SimulationService(db)
    simulations = await simulation_service.get_user_simulations(
        current_user.id, skip=skip, limit=limit
    )
    return simulations


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(
    simulation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Get specific simulation by ID
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.get_simulation(simulation_id, current_user.id)
    
    if not simulation:
        raise NotFoundError("Simulation not found")
    
    return simulation


@router.put("/{simulation_id}", response_model=SimulationResponse)
async def update_simulation(
    simulation_id: UUID,
    simulation_update: SimulationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Update simulation metadata
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.update_simulation(
        simulation_id, current_user.id, simulation_update
    )
    
    if not simulation:
        raise NotFoundError("Simulation not found")
    
    return simulation


@router.delete("/{simulation_id}")
async def delete_simulation(
    simulation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Delete simulation
    """
    simulation_service = SimulationService(db)
    success = await simulation_service.delete_simulation(simulation_id, current_user.id)
    
    if not success:
        raise NotFoundError("Simulation not found")
    
    return {"message": "Simulation deleted successfully"}


@router.post("/{simulation_id}/rerun", response_model=SimulationResponse)
async def rerun_simulation(
    simulation_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Rerun existing simulation with same parameters
    """
    simulation_service = SimulationService(db)
    simulation = await simulation_service.get_simulation(simulation_id, current_user.id)
    
    if not simulation:
        raise NotFoundError("Simulation not found")
    
    # Create new simulation with same parameters
    new_simulation = await simulation_service.clone_simulation(simulation_id, current_user.id)
    
    # Run simulation in background
    background_tasks.add_task(
        simulation_service.run_simulation,
        new_simulation.id
    )
    
    return new_simulation
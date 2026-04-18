from fastapi import APIRouter

from ..models import SimulationRequest, SimulationResult
from ..simulator import run_simulation

router = APIRouter(prefix="/simulator", tags=["simulator"])


@router.post("/retirement", response_model=SimulationResult)
def retirement(req: SimulationRequest) -> SimulationResult:
    return run_simulation(req)

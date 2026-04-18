from fastapi import APIRouter, HTTPException

from ..models import Persona
from ..personas import get_persona, list_personas

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("")
def personas_index() -> list[Persona]:
    return list_personas()


@router.get("/{persona_id}")
def persona_detail(persona_id: str) -> Persona:
    p = get_persona(persona_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_id}' not found")
    return p

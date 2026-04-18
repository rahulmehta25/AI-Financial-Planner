from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "plaid_configured": settings.plaid_configured,
        "anthropic_configured": settings.anthropic_configured,
        "model": settings.anthropic_model,
    }

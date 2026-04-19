"""Monthly financial briefing endpoint.

Designed to be invoked by Cloud Scheduler on the first of each month (or on
demand). The handler walks every user, summarizes the trailing 30 days of
transactions, renders an audio briefing via ElevenLabs, and records a row in
the `briefings` table so the frontend can render the history.

Auth: requires header `X-Scheduler-Secret` to match the `SCHEDULER_SHARED_SECRET`
env var. Cloud Scheduler sets a custom header when it hits the endpoint.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional

import httpx
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from ..db import get_session_factory


router = APIRouter(prefix="/briefings", tags=["briefings"])
log = logging.getLogger(__name__)

SCHEDULER_SHARED_SECRET = os.environ.get("SCHEDULER_SHARED_SECRET", "")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get(
    "ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB"
)
ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
GCS_BUCKET = os.environ.get("AIFP_BRIEFING_BUCKET", "aifp-briefings-us-east1")


class BriefingSummary(BaseModel):
    user_id: str
    display_name: Optional[str]
    inflow_total: Decimal
    outflow_total: Decimal
    net: Decimal
    top_categories: List[dict]
    narration_text: str
    audio_gs_url: Optional[str] = None


def _summarize(rows: list[dict]) -> dict:
    inflow = sum((r["amount"] for r in rows if r["amount"] > 0), Decimal(0))
    outflow = sum((-r["amount"] for r in rows if r["amount"] < 0), Decimal(0))

    by_cat: dict[str, Decimal] = {}
    for r in rows:
        if r["amount"] >= 0:
            continue
        cats = r.get("category") or ["uncategorized"]
        key = cats[0] if isinstance(cats, list) and cats else str(cats)
        by_cat[key] = by_cat.get(key, Decimal(0)) + -r["amount"]
    top = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "inflow_total": inflow,
        "outflow_total": outflow,
        "net": inflow - outflow,
        "top_categories": [{"category": c, "total": float(v)} for c, v in top],
    }


def _draft_narration(display_name: Optional[str], s: dict) -> str:
    name = display_name or "there"
    top = ", ".join(
        f"{c['category']} at {_fmt_money(c['total'])}" for c in s["top_categories"]
    ) or "no category standouts"
    return (
        f"Hi {name}, here is your monthly briefing. "
        f"You brought in {_fmt_money(float(s['inflow_total']))} "
        f"and spent {_fmt_money(float(s['outflow_total']))}, "
        f"leaving a net of {_fmt_money(float(s['net']))}. "
        f"Your biggest spend areas were {top}."
    )


def _fmt_money(value: float) -> str:
    return f"${value:,.2f}"


async def _render_mp3(text_body: str) -> bytes:
    if not ELEVENLABS_API_KEY:
        raise RuntimeError("ELEVENLABS_API_KEY not set")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload = {
        "text": text_body,
        "model_id": ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(url, headers=headers, json=payload)
        res.raise_for_status()
        return res.content


def _upload_gcs(blob_name: str, data: bytes) -> str:
    from google.cloud import storage  # type: ignore

    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_string(data, content_type="audio/mpeg")
    return f"gs://{GCS_BUCKET}/{blob_name}"


@router.post("/run-monthly", response_model=list[BriefingSummary])
async def run_monthly(
    x_scheduler_secret: str = Header(default=""),
    dry_run: bool = False,
) -> list[BriefingSummary]:
    """Cloud Scheduler entrypoint for the monthly briefing."""
    if SCHEDULER_SHARED_SECRET and x_scheduler_secret != SCHEDULER_SHARED_SECRET:
        raise HTTPException(status_code=401, detail="invalid scheduler secret")

    window_end = datetime.now(timezone.utc)
    window_start = window_end - timedelta(days=30)

    session_factory = get_session_factory()
    results: list[BriefingSummary] = []

    async with session_factory() as session:
        users = await session.execute(
            text("SELECT id, display_name FROM users")
        )
        user_rows = users.fetchall()

        for user in user_rows:
            user_id = user[0]
            display_name = user[1]

            tx_res = await session.execute(
                text(
                    """
                    SELECT t.amount, t.category
                      FROM transactions t
                      JOIN accounts a ON a.id = t.account_id
                     WHERE a.user_id = :user_id
                       AND t.date >= :start
                       AND t.date <= :end
                    """
                ),
                {
                    "user_id": user_id,
                    "start": window_start.date(),
                    "end": window_end.date(),
                },
            )
            rows = [
                {"amount": r[0], "category": r[1]}
                for r in tx_res.fetchall()
            ]
            summary = _summarize(rows)
            narration = _draft_narration(display_name, summary)

            audio_gs_url: Optional[str] = None
            if not dry_run and ELEVENLABS_API_KEY:
                try:
                    mp3 = await _render_mp3(narration)
                    blob_name = (
                        f"{user_id}/{window_end.strftime('%Y-%m')}-briefing.mp3"
                    )
                    audio_gs_url = _upload_gcs(blob_name, mp3)
                    await session.execute(
                        text(
                            """
                            INSERT INTO briefings (user_id, period_start, period_end,
                                narration_text, audio_gs_url, inflow_total, outflow_total, net_total)
                            VALUES (:user_id, :ps, :pe, :nt, :url, :inf, :out, :net)
                            """
                        ),
                        {
                            "user_id": user_id,
                            "ps": window_start,
                            "pe": window_end,
                            "nt": narration,
                            "url": audio_gs_url,
                            "inf": summary["inflow_total"],
                            "out": summary["outflow_total"],
                            "net": summary["net"],
                        },
                    )
                except Exception:
                    log.exception("briefing render failed for user %s", user_id)

            results.append(
                BriefingSummary(
                    user_id=str(user_id),
                    display_name=display_name,
                    inflow_total=summary["inflow_total"],
                    outflow_total=summary["outflow_total"],
                    net=summary["net"],
                    top_categories=summary["top_categories"],
                    narration_text=narration,
                    audio_gs_url=audio_gs_url,
                )
            )

        if not dry_run:
            await session.commit()

    return results

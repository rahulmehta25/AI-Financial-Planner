"""Claude-grounded advisor. Grounds on persona accounts/transactions/goals, with tool access to the Monte Carlo simulator."""

from __future__ import annotations

import json
from typing import Any

from .config import get_settings
from .models import (
    ChatRequest,
    ChatResponse,
    Persona,
    SimulationRequest,
    ToolCallTrace,
)
from .personas import get_persona, liquid_assets, total_debt
from .simulator import run_simulation


SYSTEM_PROMPT = """You are a financial planning assistant for a portfolio demo. You always ground your answers in the user's actual accounts, goals, and transactions, which are provided in the context block below.

Rules:
- If the user asks a forward-looking question about whether they can afford something, retire on time, or survive a shock, call the run_retirement_simulation tool with reasonable inputs derived from the context.
- Quote the user's own numbers back to them when explaining. Use plain English. No hedging boilerplate.
- Do not give tax, legal, or specific investment advice. This is an educational portfolio demo.
- Keep replies under 180 words unless the user explicitly asks for more depth.
"""


SIMULATOR_TOOL = {
    "name": "run_retirement_simulation",
    "description": (
        "Monte Carlo retirement simulator. Returns p10/p50/p90 final portfolio values and the probability "
        "the user's assets last through the horizon. Call this for any 'what if' or 'can I afford' question."
    ),
    "input_schema": {
        "type": "object",
        "required": ["current_assets", "annual_contribution", "current_age", "retirement_age", "annual_spending_in_retirement"],
        "properties": {
            "current_assets": {"type": "number", "description": "Liquid investable assets today"},
            "annual_contribution": {"type": "number"},
            "current_age": {"type": "integer"},
            "retirement_age": {"type": "integer"},
            "annual_spending_in_retirement": {"type": "number"},
            "expected_return": {"type": "number", "default": 0.07},
            "return_volatility": {"type": "number", "default": 0.15},
            "inflation": {"type": "number", "default": 0.025},
            "horizon_years": {"type": "integer", "default": 40},
            "num_trials": {"type": "integer", "default": 10000},
            "income_shock_months": {"type": "integer", "default": 0, "description": "Months of lost income in year one"},
        },
    },
}


def _persona_context_block(p: Persona) -> str:
    lines = [
        f"Persona: {p.name}, age {p.age}.",
        f"Backstory: {p.backstory}",
        f"Annual income: ${p.annual_income:,.0f}. Annual spending: ${p.annual_spending:,.0f}. Savings rate: {p.savings_rate:.0%}.",
        f"Target retirement age: {p.retirement_age}.",
        f"Liquid investable assets: ${liquid_assets(p):,.0f}. Total debt: ${total_debt(p):,.0f}.",
        "",
        "Accounts:",
    ]
    for a in p.accounts:
        lines.append(f"  - {a.name} ({a.type}): ${a.balance:,.0f}")
    if p.goals:
        lines.append("")
        lines.append("Goals:")
        for g in p.goals:
            target = f" by {g.target_date}" if g.target_date else ""
            lines.append(f"  - {g.kind}: ${g.target_amount:,.0f}{target} {g.notes}".rstrip())
    if p.transactions:
        lines.append("")
        lines.append("Recent transactions:")
        for t in p.transactions[-8:]:
            lines.append(f"  - {t.date} {t.description} ({t.category}): ${t.amount:,.2f}")
    return "\n".join(lines)


def _stub_reply(persona: Persona, user_msg: str) -> ChatResponse:
    annual_contribution = persona.annual_income * persona.savings_rate
    req = SimulationRequest(
        current_assets=liquid_assets(persona),
        annual_contribution=annual_contribution,
        current_age=persona.age,
        retirement_age=persona.retirement_age,
        annual_spending_in_retirement=persona.annual_spending * 0.8,
        horizon_years=min(60, 100 - persona.age),
    )
    result = run_simulation(req)
    trace = ToolCallTrace(
        tool="run_retirement_simulation",
        input=req.model_dump(),
        output={
            "p10_final": result.p10_final,
            "p50_final": result.p50_final,
            "p90_final": result.p90_final,
            "success_probability": result.success_probability,
        },
    )
    reply = (
        f"(Anthropic API key not configured, returning a grounded stub.)\n\n"
        f"Based on {persona.name}'s numbers, here's the simulator output:\n"
        f"- Median final portfolio: ${result.p50_final:,.0f}\n"
        f"- 10th percentile: ${result.p10_final:,.0f}\n"
        f"- 90th percentile: ${result.p90_final:,.0f}\n"
        f"- Probability of never running out: {result.success_probability:.0%}\n\n"
        f"Set ANTHROPIC_API_KEY in .env to get a full Claude-generated answer to: \"{user_msg}\""
    )
    return ChatResponse(
        reply=reply,
        tool_calls=[trace],
        grounded_on=["accounts", "goals", "transactions"],
        anthropic_live=False,
    )


def _run_tool(name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    if name != "run_retirement_simulation":
        return {"error": f"Unknown tool: {name}"}
    req = SimulationRequest(**tool_input)
    result = run_simulation(req)
    return {
        "p10_final": result.p10_final,
        "p50_final": result.p50_final,
        "p90_final": result.p90_final,
        "success_probability": result.success_probability,
        "num_trials": result.num_trials,
        "horizon_years": result.horizon_years,
    }


def respond(request: ChatRequest) -> ChatResponse:
    persona = get_persona(request.persona_id)
    if persona is None:
        return ChatResponse(reply=f"Unknown persona: {request.persona_id}", grounded_on=[], anthropic_live=False)

    settings = get_settings()
    user_msg = request.messages[-1].content if request.messages else ""

    if not settings.anthropic_configured:
        return _stub_reply(persona, user_msg)

    import anthropic

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    context = _persona_context_block(persona)
    system = SYSTEM_PROMPT + "\n\n---\nUser context:\n" + context

    history: list[dict[str, Any]] = [
        {"role": m.role, "content": m.content} for m in request.messages
    ]

    traces: list[ToolCallTrace] = []
    final_text = ""
    for _ in range(4):
        resp = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system,
            tools=[SIMULATOR_TOOL],
            messages=history,
        )
        if resp.stop_reason == "tool_use":
            assistant_blocks: list[dict[str, Any]] = []
            tool_results: list[dict[str, Any]] = []
            for block in resp.content:
                bd = block.model_dump() if hasattr(block, "model_dump") else dict(block)
                assistant_blocks.append(bd)
                if bd.get("type") == "tool_use":
                    tool_name = bd["name"]
                    tool_input = bd.get("input", {})
                    output = _run_tool(tool_name, tool_input)
                    traces.append(ToolCallTrace(tool=tool_name, input=tool_input, output=output))
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": bd["id"],
                        "content": json.dumps(output),
                    })
            history.append({"role": "assistant", "content": assistant_blocks})
            history.append({"role": "user", "content": tool_results})
            continue

        pieces: list[str] = []
        for block in resp.content:
            bd = block.model_dump() if hasattr(block, "model_dump") else dict(block)
            if bd.get("type") == "text":
                pieces.append(bd.get("text", ""))
        final_text = "\n".join(pieces).strip()
        break

    return ChatResponse(
        reply=final_text or "(Claude returned no text.)",
        tool_calls=traces,
        grounded_on=["accounts", "goals", "transactions"],
        anthropic_live=True,
    )

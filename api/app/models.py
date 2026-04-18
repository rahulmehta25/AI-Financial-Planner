from typing import Literal, Optional
from pydantic import BaseModel, Field


class Account(BaseModel):
    id: str
    name: str
    type: Literal["checking", "savings", "brokerage", "retirement", "credit", "mortgage", "auto"]
    balance: float
    institution: str = "Plaid Sandbox"


class Transaction(BaseModel):
    id: str
    account_id: str
    date: str
    amount: float
    category: str
    description: str


class Goal(BaseModel):
    id: str
    kind: Literal["retirement", "house", "debt_payoff", "emergency_fund"]
    target_amount: float
    target_date: Optional[str] = None
    notes: str = ""


class Persona(BaseModel):
    id: str
    name: str
    age: int
    annual_income: float
    annual_spending: float
    savings_rate: float = Field(ge=0, le=1)
    retirement_age: int
    accounts: list[Account]
    transactions: list[Transaction] = []
    goals: list[Goal] = []
    backstory: str


class SimulationRequest(BaseModel):
    current_assets: float = Field(ge=0, description="Sum of invested and savings assets today")
    annual_contribution: float = Field(ge=0, description="Dollars added per year")
    current_age: int = Field(ge=18, le=100)
    retirement_age: int = Field(ge=18, le=100)
    annual_spending_in_retirement: float = Field(ge=0)
    expected_return: float = Field(default=0.07, ge=-0.2, le=0.3, description="Annual mean nominal return")
    return_volatility: float = Field(default=0.15, ge=0, le=0.6, description="Annual stdev")
    inflation: float = Field(default=0.025, ge=-0.05, le=0.2)
    horizon_years: int = Field(default=40, ge=1, le=80)
    num_trials: int = Field(default=10_000, ge=100, le=50_000)
    income_shock_months: int = Field(default=0, ge=0, le=60, description="Months of lost income during year 1")


class SimulationResult(BaseModel):
    p10_final: float
    p50_final: float
    p90_final: float
    success_probability: float = Field(description="Fraction of trials where assets never hit zero after retirement")
    median_path: list[float]
    p10_path: list[float]
    p90_path: list[float]
    num_trials: int
    horizon_years: int


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    persona_id: str
    messages: list[ChatMessage]


class ToolCallTrace(BaseModel):
    tool: str
    input: dict
    output: dict


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallTrace] = []
    grounded_on: list[str] = Field(default_factory=list, description="Types of context the advisor referenced")
    anthropic_live: bool = False

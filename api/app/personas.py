"""Hardcoded persona data for portfolio demos. No PII; everything is fictional."""

from .models import Account, Goal, Persona, Transaction


def _txn(idx: int, account_id: str, date: str, amount: float, category: str, desc: str) -> Transaction:
    return Transaction(id=f"txn_{account_id}_{idx}", account_id=account_id, date=date, amount=amount, category=category, description=desc)


_young_saver = Persona(
    id="young_saver",
    name="Maya Chen",
    age=25,
    annual_income=125_000,
    annual_spending=52_000,
    savings_rate=0.35,
    retirement_age=60,
    backstory=(
        "Software engineer two years out of college. Lives with a roommate in Seattle, "
        "no debt, maxes out 401k match, wants to retire early but has never modeled it."
    ),
    accounts=[
        Account(id="ys_checking", name="Everyday Checking", type="checking", balance=8_400),
        Account(id="ys_savings", name="High Yield Savings", type="savings", balance=12_000),
        Account(id="ys_brokerage", name="Index Brokerage", type="brokerage", balance=18_500),
        Account(id="ys_401k", name="Employer 401k", type="retirement", balance=34_200),
    ],
    goals=[
        Goal(id="ys_ret", kind="retirement", target_amount=1_800_000, target_date="2061-01-01", notes="Wants to retire at 60"),
        Goal(id="ys_ef", kind="emergency_fund", target_amount=20_000, notes="Targeting six months of expenses"),
    ],
    transactions=[
        _txn(1, "ys_checking", "2026-04-01", -1_850, "rent", "Monthly rent"),
        _txn(2, "ys_checking", "2026-04-05", -420, "groceries", "Trader Joes"),
        _txn(3, "ys_checking", "2026-04-10", -80, "transport", "Transit card reload"),
        _txn(4, "ys_checking", "2026-04-15", 4_800, "income", "Biweekly paycheck"),
        _txn(5, "ys_brokerage", "2026-04-15", -1_500, "investment", "VTSAX buy"),
    ],
)


_mid_career = Persona(
    id="mid_career",
    name="Jordan Ramirez",
    age=38,
    annual_income=195_000,
    annual_spending=142_000,
    savings_rate=0.18,
    retirement_age=65,
    backstory=(
        "Product manager with a spouse and two kids in the Bay Area. 401k is healthy but the mortgage "
        "is tight and daycare costs are real. Wants to know if the current trajectory is enough."
    ),
    accounts=[
        Account(id="mc_checking", name="Joint Checking", type="checking", balance=14_700),
        Account(id="mc_savings", name="Joint Savings", type="savings", balance=46_000),
        Account(id="mc_brokerage", name="Taxable Brokerage", type="brokerage", balance=92_500),
        Account(id="mc_401k", name="401k", type="retirement", balance=182_300),
        Account(id="mc_roth", name="Roth IRA", type="retirement", balance=61_400),
        Account(id="mc_mortgage", name="Primary Mortgage", type="mortgage", balance=-612_000),
        Account(id="mc_auto", name="Auto Loan", type="auto", balance=-18_400),
    ],
    goals=[
        Goal(id="mc_ret", kind="retirement", target_amount=3_500_000, target_date="2053-01-01"),
        Goal(id="mc_house", kind="house", target_amount=120_000, notes="Possible move to a bigger place"),
    ],
    transactions=[
        _txn(1, "mc_checking", "2026-04-01", -4_100, "housing", "Mortgage payment"),
        _txn(2, "mc_checking", "2026-04-03", -2_800, "childcare", "Daycare"),
        _txn(3, "mc_checking", "2026-04-07", -950, "groceries", "Grocery run"),
        _txn(4, "mc_checking", "2026-04-15", 6_400, "income", "Biweekly paycheck"),
        _txn(5, "mc_brokerage", "2026-04-16", -1_000, "investment", "VTI buy"),
    ],
)


_pre_retiree = Persona(
    id="pre_retiree",
    name="Linda Whitaker",
    age=58,
    annual_income=165_000,
    annual_spending=95_000,
    savings_rate=0.22,
    retirement_age=63,
    backstory=(
        "Senior analyst. Kids are out of the house, mortgage is paid off. Deciding between retiring at 63 "
        "or working two more years to pad the portfolio. Wants to stress test a market downturn."
    ),
    accounts=[
        Account(id="pr_checking", name="Checking", type="checking", balance=26_000),
        Account(id="pr_savings", name="Savings", type="savings", balance=85_000),
        Account(id="pr_brokerage", name="Taxable Brokerage", type="brokerage", balance=410_000),
        Account(id="pr_401k", name="401k", type="retirement", balance=720_000),
        Account(id="pr_roth", name="Roth IRA", type="retirement", balance=145_000),
    ],
    goals=[
        Goal(id="pr_ret", kind="retirement", target_amount=2_400_000, target_date="2031-01-01", notes="Aiming for 63 if possible"),
    ],
    transactions=[
        _txn(1, "pr_checking", "2026-04-02", -850, "utilities", "Power + water"),
        _txn(2, "pr_checking", "2026-04-06", -420, "groceries", "Market basket"),
        _txn(3, "pr_checking", "2026-04-15", 5_200, "income", "Biweekly paycheck"),
        _txn(4, "pr_brokerage", "2026-04-18", -2_500, "investment", "Dividend reinvest"),
    ],
)


PERSONAS: dict[str, Persona] = {
    p.id: p for p in [_young_saver, _mid_career, _pre_retiree]
}


def list_personas() -> list[Persona]:
    return list(PERSONAS.values())


def get_persona(persona_id: str) -> Persona | None:
    return PERSONAS.get(persona_id)


def liquid_assets(p: Persona) -> float:
    keep = {"savings", "brokerage", "retirement"}
    return sum(a.balance for a in p.accounts if a.type in keep and a.balance > 0)


def total_debt(p: Persona) -> float:
    return -sum(a.balance for a in p.accounts if a.balance < 0)

"""Monte Carlo retirement simulator. Pure NumPy, no external services."""

import numpy as np

from .models import SimulationRequest, SimulationResult


def run_simulation(req: SimulationRequest) -> SimulationResult:
    rng = np.random.default_rng(seed=42)

    years = req.horizon_years
    trials = req.num_trials

    returns = rng.normal(loc=req.expected_return, scale=req.return_volatility, size=(trials, years))
    real_returns = (1 + returns) / (1 + req.inflation) - 1

    years_to_retire = max(0, req.retirement_age - req.current_age)

    balances = np.full(trials, float(req.current_assets))
    paths = np.zeros((trials, years + 1))
    paths[:, 0] = balances

    income_shock_fraction = min(1.0, req.income_shock_months / 12.0)
    first_year_contrib = req.annual_contribution * (1 - income_shock_fraction)

    for y in range(years):
        grown = balances * (1 + real_returns[:, y])
        if y < years_to_retire:
            contrib = first_year_contrib if y == 0 else req.annual_contribution
            balances = grown + contrib
        else:
            balances = grown - req.annual_spending_in_retirement
            balances = np.maximum(balances, 0)
        paths[:, y + 1] = balances

    final = paths[:, -1]
    post_retirement_paths = paths[:, years_to_retire:]
    never_broke = np.all(post_retirement_paths > 0, axis=1) if post_retirement_paths.size else np.ones(trials, dtype=bool)

    p10, p50, p90 = np.percentile(final, [10, 50, 90])
    median_path = np.percentile(paths, 50, axis=0).tolist()
    p10_path = np.percentile(paths, 10, axis=0).tolist()
    p90_path = np.percentile(paths, 90, axis=0).tolist()

    return SimulationResult(
        p10_final=float(p10),
        p50_final=float(p50),
        p90_final=float(p90),
        success_probability=float(np.mean(never_broke)),
        median_path=median_path,
        p10_path=p10_path,
        p90_path=p90_path,
        num_trials=trials,
        horizon_years=years,
    )

from app.models import SimulationRequest
from app.simulator import run_simulation


def test_simulation_ordering_and_shape():
    req = SimulationRequest(
        current_assets=100_000,
        annual_contribution=20_000,
        current_age=30,
        retirement_age=65,
        annual_spending_in_retirement=60_000,
        horizon_years=50,
        num_trials=2_000,
    )
    res = run_simulation(req)
    assert res.p10_final <= res.p50_final <= res.p90_final
    assert 0.0 <= res.success_probability <= 1.0
    assert len(res.median_path) == res.horizon_years + 1
    assert res.num_trials == 2_000


def test_income_shock_reduces_first_year_contribution():
    base = SimulationRequest(
        current_assets=50_000,
        annual_contribution=30_000,
        current_age=30,
        retirement_age=65,
        annual_spending_in_retirement=50_000,
        horizon_years=40,
        num_trials=1_500,
    )
    shocked = base.model_copy(update={"income_shock_months": 12})
    assert run_simulation(shocked).p50_final <= run_simulation(base).p50_final

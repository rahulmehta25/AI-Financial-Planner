import type { SimulationResult } from "../api-client";

type Input = {
  current_assets: number;
  annual_contribution: number;
  current_age: number;
  retirement_age: number;
  annual_spending_in_retirement: number;
  horizon_years?: number;
  num_trials?: number;
  income_shock_months?: number;
};

function normal(mean = 0, std = 1): number {
  const u = 1 - Math.random();
  const v = 1 - Math.random();
  return mean + std * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function runClientSimulation(i: Input): SimulationResult {
  const horizon = i.horizon_years ?? Math.min(60, 100 - i.current_age);
  const trials = i.num_trials ?? 10_000;
  const meanReturn = 0.07;
  const stdReturn = 0.15;
  const yearsToRetire = Math.max(1, i.retirement_age - i.current_age);
  const shockYears = (i.income_shock_months ?? 0) / 12;

  const finals: number[] = [];
  const pathsByYear: number[][] = Array.from({ length: horizon + 1 }, () => []);

  for (let t = 0; t < trials; t++) {
    let balance = i.current_assets;
    pathsByYear[0].push(balance);
    const effectiveContribYears = Math.max(0, yearsToRetire - shockYears);
    for (let y = 1; y <= horizon; y++) {
      const r = normal(meanReturn, stdReturn);
      balance *= 1 + r;
      if (y <= yearsToRetire && y > shockYears) {
        balance += i.annual_contribution;
      }
      if (y > yearsToRetire) {
        balance -= i.annual_spending_in_retirement;
      }
      balance = Math.max(0, balance);
      pathsByYear[y].push(balance);
    }
    finals.push(balance);
    // Suppress unused-var warning for symmetry
    void effectiveContribYears;
  }

  finals.sort((a, b) => a - b);
  const q = (p: number) => finals[Math.min(finals.length - 1, Math.floor(finals.length * p))];
  const pct = (values: number[], p: number) => {
    const s = [...values].sort((a, b) => a - b);
    return s[Math.min(s.length - 1, Math.floor(s.length * p))];
  };

  return {
    p10_final: q(0.1),
    p50_final: q(0.5),
    p90_final: q(0.9),
    success_probability: finals.filter((f) => f > 0).length / finals.length,
    median_path: pathsByYear.map((v) => pct(v, 0.5)),
    p10_path: pathsByYear.map((v) => pct(v, 0.1)),
    p90_path: pathsByYear.map((v) => pct(v, 0.9)),
    num_trials: trials,
    horizon_years: horizon,
  };
}

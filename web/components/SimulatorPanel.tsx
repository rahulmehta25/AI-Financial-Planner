"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type Persona, type SimulationResult } from "@/app/api-client";
import { runClientSimulation } from "@/app/lib/client-monte-carlo";
import { money } from "@/app/lib/format";

function liquidAssets(p: Persona) {
  return p.accounts
    .filter((a) => ["savings", "brokerage", "retirement"].includes(a.type) && a.balance > 0)
    .reduce((s, a) => s + a.balance, 0);
}

export function SimulatorPanel({ persona }: { persona: Persona }) {
  const [shock, setShock] = useState(0);
  const [retirementAge, setRetirementAge] = useState(persona.retirement_age);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRetirementAge(persona.retirement_age);
    setShock(0);
    setResult(null);
    setError(null);
  }, [persona.id, persona.retirement_age]);

  const assets = useMemo(() => liquidAssets(persona), [persona]);
  const contribution = Math.round(persona.annual_income * persona.savings_rate);

  async function runIt() {
    setLoading(true);
    setError(null);
    const input = {
      current_assets: assets,
      annual_contribution: contribution,
      current_age: persona.age,
      retirement_age: retirementAge,
      annual_spending_in_retirement: Math.round(persona.annual_spending * 0.8),
      horizon_years: Math.min(60, 100 - persona.age),
      num_trials: 10_000,
      income_shock_months: shock,
    };
    try {
      const res = await api.runSimulation(input);
      setResult(res);
    } catch {
      setResult(runClientSimulation(input));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="max-w-xl space-y-2">
        <h3 className="font-display text-2xl font-medium tracking-tight">Monte Carlo retirement</h3>
        <p className="text-sm leading-relaxed text-muted">
          <span className="num text-ink">{money(assets)}</span> invested and{" "}
          <span className="num text-ink">{money(contribution)}</span> per year. 10,000 trials at 7% mean, 15% stdev.
        </p>
      </div>

      <form
        className="mt-10 space-y-8"
        onSubmit={(e) => {
          e.preventDefault();
          void runIt();
        }}
      >
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2">
          <label className="block space-y-2">
            <span className="text-sm font-medium text-ink">Retirement age</span>
            <input
              type="number"
              value={retirementAge}
              min={persona.age + 1}
              max={85}
              onChange={(e) => setRetirementAge(Number(e.target.value))}
              className="field max-w-[8rem] num"
            />
            <span className="block text-xs text-muted">Must be after age {persona.age}.</span>
          </label>
          <label className="block space-y-2">
            <span className="flex items-center justify-between text-sm font-medium text-ink">
              Income shock
              <span className="num text-xs font-normal text-muted">{shock} months</span>
            </span>
            <input
              type="range"
              min={0}
              max={24}
              value={shock}
              onChange={(e) => setShock(Number(e.target.value))}
              className="slider mt-4"
            />
            <span className="block text-xs text-muted">Months with no contributions before retirement.</span>
          </label>
        </div>

        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? "Running 10,000 trials..." : "Run simulation"}
        </button>
      </form>

      {error && <p className="mt-6 text-sm text-[#9b4a45]">{error}</p>}

      {!result && !loading && (
        <p className="mt-12 max-w-md border-t border-line pt-8 text-sm leading-relaxed text-muted">
          Set retirement age and any income shock, then run the simulation to see percentile paths.
        </p>
      )}

      {result && (
        <div className="rise mt-14 space-y-12">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">
              Chance of never running out
            </p>
            <p className="num mt-3 text-6xl font-medium tracking-tight text-ink md:text-7xl">
              {Math.round(result.success_probability * 100)}%
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 border-t border-line pt-10 sm:grid-cols-3 sm:gap-0">
            <Stat label="P10 final" value={money(result.p10_final)} />
            <Stat label="P50 final" value={money(result.p50_final)} featured />
            <Stat label="P90 final" value={money(result.p90_final)} last />
          </div>
          <PathChart result={result} />
        </div>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  featured,
  last,
}: {
  label: string;
  value: string;
  featured?: boolean;
  last?: boolean;
}) {
  return (
    <div className={`border-t border-line pt-6 sm:border-t-0 sm:pt-0 ${!last ? "sm:border-r sm:pr-8" : ""} ${featured ? "sm:px-8" : "sm:pr-8"}`}>
      <div className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">{label}</div>
      <div className="num mt-3 text-xl text-ink">{value}</div>
    </div>
  );
}

function PathChart({ result }: { result: SimulationResult }) {
  const { p10_path, median_path, p90_path, horizon_years } = result;
  const max = Math.max(...p90_path) || 1;
  const W = 640;
  const H = 240;
  const pad = { l: 64, r: 16, t: 16, b: 32 };
  const innerW = W - pad.l - pad.r;
  const innerH = H - pad.t - pad.b;
  const N = median_path.length;
  const x = (i: number) => pad.l + (i / Math.max(1, N - 1)) * innerW;
  const y = (v: number) => pad.t + innerH - (v / max) * innerH;

  const toPath = (arr: number[]) =>
    arr
      .map((v, i) => `${x(i)},${y(v)}`)
      .map((pt, i) => (i === 0 ? `M${pt}` : `L${pt}`))
      .join(" ");

  const band = [
    ...p10_path.map((v, i) => `${x(i)},${y(v)}`),
    ...[...p90_path].reverse().map((v, i) => `${x(N - 1 - i)},${y(v)}`),
  ].join(" ");

  const ticks = [0, 0.5, 1];

  return (
    <div className="space-y-4 border-t border-line pt-10">
      <div className="flex flex-wrap items-center gap-5 text-xs text-muted">
        <Legend swatch="#9b4a45" dashed label="P10" />
        <Legend swatch="#4a6756" label="Median" />
        <Legend swatch="#7a7368" dashed label="P90" />
        <span>Shaded band is the 10 to 90 range.</span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="h-56 w-full" role="img" aria-label="Retirement path percentiles">
        {ticks.map((t) => {
          const value = max * t;
          const yy = y(value);
          return (
            <g key={t}>
              <line x1={pad.l} x2={W - pad.r} y1={yy} y2={yy} stroke="#e2d9cc" strokeWidth={1} />
              <text x={pad.l - 8} y={yy + 4} textAnchor="end" className="fill-muted" fontSize="11">
                {t === 0 ? "$0" : money(value)}
              </text>
            </g>
          );
        })}
        <text x={pad.l} y={H - 8} className="fill-muted" fontSize="11">
          Now
        </text>
        <text x={W - pad.r} y={H - 8} textAnchor="end" className="fill-muted" fontSize="11">
          +{horizon_years} yrs
        </text>
        <polygon points={band} fill="rgba(36, 31, 25, 0.06)" />
        <path d={toPath(p10_path)} fill="none" stroke="#9b4a45" strokeWidth={1.25} strokeDasharray="4,3" />
        <path d={toPath(median_path)} fill="none" stroke="#4a6756" strokeWidth={2} />
        <path d={toPath(p90_path)} fill="none" stroke="#7a7368" strokeWidth={1.25} strokeDasharray="4,3" />
      </svg>
    </div>
  );
}

function Legend({ swatch, label, dashed }: { swatch: string; label: string; dashed?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        className="inline-block w-5"
        style={{
          borderTop: dashed ? `1.5px dashed ${swatch}` : `1.5px solid ${swatch}`,
        }}
      />
      {label}
    </span>
  );
}

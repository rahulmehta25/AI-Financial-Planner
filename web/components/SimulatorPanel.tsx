"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type Persona, type SimulationResult } from "@/app/api-client";

const fmt = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

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

  useEffect(() => setRetirementAge(persona.retirement_age), [persona.id, persona.retirement_age]);

  const assets = useMemo(() => liquidAssets(persona), [persona]);
  const contribution = Math.round(persona.annual_income * persona.savings_rate);

  async function runIt() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runSimulation({
        current_assets: assets,
        annual_contribution: contribution,
        current_age: persona.age,
        retirement_age: retirementAge,
        annual_spending_in_retirement: Math.round(persona.annual_spending * 0.8),
        horizon_years: Math.min(60, 100 - persona.age),
        num_trials: 10_000,
        income_shock_months: shock,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-semibold">Monte Carlo retirement</h3>
          <p className="text-sm text-muted">
            {fmt(assets)} invested, {fmt(contribution)}/yr, 10,000 trials, 7% mean / 15% stdev
          </p>
        </div>
        <button
          onClick={runIt}
          disabled={loading}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-indigo-600 disabled:opacity-60"
        >
          {loading ? "Running..." : "Run simulation"}
        </button>
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <label className="flex items-center gap-3">
          <span className="w-44 text-muted">Retirement age</span>
          <input
            type="number"
            value={retirementAge}
            min={persona.age + 1}
            max={85}
            onChange={(e) => setRetirementAge(Number(e.target.value))}
            className="w-24 rounded-md border border-slate-200 px-2 py-1"
          />
        </label>
        <label className="flex items-center gap-3">
          <span className="w-44 text-muted">Income shock (months)</span>
          <input
            type="range"
            min={0}
            max={24}
            value={shock}
            onChange={(e) => setShock(Number(e.target.value))}
            className="flex-1"
          />
          <span className="w-8 text-right font-mono">{shock}</span>
        </label>
      </div>

      {error && <p className="mt-4 text-sm text-rose-600">{error}</p>}

      {result && (
        <div className="mt-6">
          <div className="grid grid-cols-3 gap-3 text-center">
            <Stat label="P10 final" value={fmt(result.p10_final)} tone="rose" />
            <Stat label="P50 final" value={fmt(result.p50_final)} tone="accent" />
            <Stat label="P90 final" value={fmt(result.p90_final)} tone="emerald" />
          </div>
          <p className="mt-3 text-sm text-muted">
            Probability of never running out:{" "}
            <span className="font-semibold text-ink">{Math.round(result.success_probability * 100)}%</span>
          </p>
          <PathChart result={result} />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone: "rose" | "accent" | "emerald" }) {
  const toneClass = {
    rose: "bg-rose-50 text-rose-700",
    accent: "bg-indigo-50 text-indigo-700",
    emerald: "bg-emerald-50 text-emerald-700",
  }[tone];
  return (
    <div className={`rounded-lg px-3 py-3 ${toneClass}`}>
      <div className="text-xs uppercase tracking-wide opacity-70">{label}</div>
      <div className="mt-1 font-mono text-base">{value}</div>
    </div>
  );
}

function PathChart({ result }: { result: SimulationResult }) {
  const { p10_path, median_path, p90_path } = result;
  const max = Math.max(...p90_path) || 1;
  const W = 600;
  const H = 200;
  const N = median_path.length;

  const toPath = (arr: number[]) =>
    arr
      .map((v, i) => `${(i / (N - 1)) * W},${H - (v / max) * H}`)
      .map((pt, i) => (i === 0 ? `M${pt}` : `L${pt}`))
      .join(" ");

  const band = [
    ...p10_path.map((v, i) => `${(i / (N - 1)) * W},${H - (v / max) * H}`),
    ...[...p90_path].reverse().map((v, i) => `${((N - 1 - i) / (N - 1)) * W},${H - (v / max) * H}`),
  ].join(" ");

  return (
    <div className="mt-4 overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-48">
        <polygon points={band} fill="rgba(79,70,229,0.12)" />
        <path d={toPath(p10_path)} fill="none" stroke="#f43f5e" strokeWidth={1.5} strokeDasharray="3,3" />
        <path d={toPath(median_path)} fill="none" stroke="#4f46e5" strokeWidth={2} />
        <path d={toPath(p90_path)} fill="none" stroke="#10b981" strokeWidth={1.5} strokeDasharray="3,3" />
      </svg>
      <p className="text-xs text-muted">Dashed: p10 / p90. Solid: median. Band shows the 10-90 range.</p>
    </div>
  );
}

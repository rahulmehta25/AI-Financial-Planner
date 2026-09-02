"use client";

import type { Persona } from "@/app/api-client";

const money = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

function netWorth(p: Persona) {
  return p.accounts.reduce((sum, account) => sum + account.balance, 0);
}

export function PersonaPicker({
  personas,
  selectedId,
  onSelect,
}: {
  personas: Persona[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
      {personas.map((p) => {
        const active = p.id === selectedId;
        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            className={`card p-6 text-left transition ${
              active
                ? "border-accent shadow-card ring-2 ring-accent/20"
                : "hover:border-slate-300 hover:shadow-card"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold tracking-tight">{p.name}</h3>
                <p className="mt-1 text-xs text-muted">Age {p.age}, retire at {p.retirement_age}</p>
              </div>
              <span className="shrink-0 rounded-full bg-slate-50 px-2.5 py-1 font-mono text-xs text-ink">
                {money(netWorth(p))}
              </span>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted">{p.backstory}</p>
            <div className="mt-5 flex flex-wrap gap-2 text-xs">
              <Metric label="Income" value={`${Math.round(p.annual_income / 1000)}k`} />
              <Metric label="Savings" value={`${Math.round(p.savings_rate * 100)}%`} />
              <Metric label="Spend" value={`${Math.round(p.annual_spending / 1000)}k`} />
            </div>
          </button>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-full bg-slate-50 px-2.5 py-1 text-muted">
      <span className="mr-1.5 uppercase tracking-wide">{label}</span>
      <span className="font-medium text-ink">{value}</span>
    </span>
  );
}

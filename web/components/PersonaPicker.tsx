"use client";

import type { Persona } from "@/app/api-client";
import { money } from "@/app/lib/format";

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
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
      {personas.map((p) => {
        const active = p.id === selectedId;
        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            aria-pressed={active}
            className={`card p-7 text-left transition ${
              active
                ? "border-accent shadow-lift ring-1 ring-accent/30"
                : "hover:border-accent/30 hover:shadow-lift"
            }`}
          >
            <p className="text-xs tracking-wide text-muted">
              Age {p.age}, retire at {p.retirement_age}
            </p>
            <h3 className="mt-2 font-display text-2xl font-medium tracking-tight">{p.name}</h3>
            <p className="mt-6 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Net worth</p>
            <p className="num mt-1 text-3xl font-medium tracking-tight text-ink">{money(netWorth(p))}</p>
            <p className="mt-5 text-sm leading-relaxed text-muted">{p.backstory}</p>
            <div className="mt-6 flex flex-wrap gap-2 text-xs">
              <Metric label="Income" value={money(p.annual_income)} />
              <Metric label="Savings" value={`${Math.round(p.savings_rate * 100)}%`} />
              <Metric label="Spend" value={money(p.annual_spending)} />
            </div>
          </button>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <span className="rounded-full bg-sage-wash/70 px-2.5 py-1 text-muted">
      <span className="mr-1.5 uppercase tracking-[0.12em]">{label}</span>
      <span className="num font-medium text-ink">{value}</span>
    </span>
  );
}

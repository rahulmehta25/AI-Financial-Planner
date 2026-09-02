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
    <div className="grid grid-cols-1 md:grid-cols-3">
      {personas.map((p, i) => {
        const active = p.id === selectedId;
        return (
          <button
            key={p.id}
            type="button"
            onClick={() => onSelect(p.id)}
            aria-pressed={active}
            className={`rise py-10 text-left transition md:py-2 md:pr-10 ${
              i > 0 ? "border-t border-line md:border-l md:border-t-0 md:pl-10" : ""
            } ${active ? "shadow-[inset_0_-2px_0_0_var(--accent)]" : "hover:shadow-[inset_0_-1px_0_0_var(--ink)]"}`}
            style={{ animationDelay: `${0.06 * i}s` }}
          >
            <p className="text-xs tracking-wide text-muted">
              Age {p.age}, retire at {p.retirement_age}
            </p>
            <h3 className="mt-2 font-display text-2xl font-medium tracking-tight">{p.name}</h3>
            <p className="mt-8 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Net worth</p>
            <p className="num mt-1 text-3xl font-medium tracking-tight text-ink">{money(netWorth(p))}</p>
            <p className="mt-5 text-sm leading-relaxed text-muted">{p.backstory}</p>
            <dl className="mt-8 grid grid-cols-3 gap-3 text-xs">
              <Metric label="Income" value={money(p.annual_income)} />
              <Metric label="Savings" value={`${Math.round(p.savings_rate * 100)}%`} />
              <Metric label="Spend" value={money(p.annual_spending)} />
            </dl>
          </button>
        );
      })}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="uppercase tracking-[0.12em] text-muted">{label}</dt>
      <dd className="num mt-1 font-medium text-ink">{value}</dd>
    </div>
  );
}

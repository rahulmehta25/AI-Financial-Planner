"use client";

import { useEffect, useState } from "react";
import { api, type Persona } from "./api-client";
import { PersonaPicker } from "@/components/PersonaPicker";
import { AccountsTable } from "@/components/AccountsTable";
import { SimulatorPanel } from "@/components/SimulatorPanel";
import { AdvisorChat } from "@/components/AdvisorChat";
import staticPersonas from "./personas.json";

type Health = {
  ok: boolean;
  plaid_configured: boolean;
  anthropic_configured: boolean;
  model: string;
};

export default function Page() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.personas(), api.health()])
      .then(([ps, h]) => {
        setPersonas(ps);
        setHealth(h);
        setSelectedId(ps[0]?.id ?? null);
      })
      .catch(() => {
        const ps = staticPersonas as unknown as Persona[];
        setPersonas(ps);
        setHealth({ ok: true, plaid_configured: false, anthropic_configured: false, model: "demo" });
        setSelectedId(ps[0]?.id ?? null);
      })
      .finally(() => setLoading(false));
  }, []);

  const selected = personas.find((p) => p.id === selectedId) ?? null;

  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1.5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-accent">Portfolio demo</p>
            <h1 className="text-2xl font-semibold tracking-tight">AI Financial Planner</h1>
            <p className="max-w-xl text-sm leading-relaxed text-muted">
              Claude grounded on real account data, with a Monte Carlo retirement tool.
            </p>
          </div>
          {health && (
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <Badge ok={health.plaid_configured} label="Plaid" />
              <Badge ok={health.anthropic_configured} label="Anthropic" />
            </div>
          )}
        </div>
      </header>

      <div className="mx-auto max-w-6xl space-y-10 px-6 py-10">
        {error && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {error}. Start the API with <code className="font-mono">make api</code>.
          </div>
        )}

        <section className="space-y-4">
          <div className="space-y-1">
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">Choose a persona</h2>
            <p className="text-sm text-muted">Accounts, goals, and spending load with the profile. Nothing here is financial advice.</p>
          </div>
          {loading ? <PersonaSkeleton /> : <PersonaPicker personas={personas} selectedId={selectedId} onSelect={setSelectedId} />}
        </section>

        {selected && (
          <>
            <section className="grid grid-cols-1 items-start gap-8 lg:grid-cols-2">
              <AccountsTable accounts={selected.accounts} goals={selected.goals} />
              <SimulatorPanel persona={selected} />
            </section>
            <section>
              <AdvisorChat key={selected.id} personaId={selected.id} />
            </section>
          </>
        )}

        <footer className="border-t border-slate-200/80 pt-8 text-xs leading-relaxed text-muted">
          Portfolio demo. Plaid sandbox only. Nothing here is financial advice.
        </footer>
      </div>
    </main>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${
        ok ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-muted"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-slate-400"}`} />
      {label}: {ok ? "live" : "mock"}
    </span>
  );
}

function PersonaSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-5 md:grid-cols-3" aria-hidden>
      {[0, 1, 2].map((i) => (
        <div key={i} className="card h-44 animate-pulse bg-slate-100" />
      ))}
    </div>
  );
}

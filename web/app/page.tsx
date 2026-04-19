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
      });
  }, []);

  const selected = personas.find((p) => p.id === selectedId) ?? null;

  return (
    <main className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">AI Financial Planner</h1>
            <p className="text-sm text-muted">Claude grounded on real account data, with a Monte Carlo tool.</p>
          </div>
          {health && (
            <div className="flex items-center gap-2 text-xs">
              <Badge ok={health.plaid_configured} label="Plaid" />
              <Badge ok={health.anthropic_configured} label="Anthropic" />
            </div>
          )}
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-8 space-y-8">
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            {error}. Start the API with <code className="font-mono">make api</code>.
          </div>
        )}

        <section>
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted">Choose a persona</h2>
          <PersonaPicker personas={personas} selectedId={selectedId} onSelect={setSelectedId} />
        </section>

        {selected && (
          <>
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <AccountsTable accounts={selected.accounts} />
              <SimulatorPanel persona={selected} />
            </section>
            <section>
              <AdvisorChat personaId={selected.id} />
            </section>
          </>
        )}

        <footer className="pt-6 text-xs text-muted">
          Portfolio demo. Plaid sandbox only. Nothing here is financial advice.
        </footer>
      </div>
    </main>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`rounded-full px-2 py-0.5 ${
        ok ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-muted"
      }`}
    >
      {label}: {ok ? "live" : "mock"}
    </span>
  );
}

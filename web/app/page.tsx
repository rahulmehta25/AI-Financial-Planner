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

const PILLARS = [
  {
    kicker: "01",
    title: "Grounded",
    body: "Accounts, goals, and spending load with the person you select. The advisor cites balances, not slogans.",
  },
  {
    kicker: "02",
    title: "Ranged",
    body: "Ten thousand trials. Percentiles you can read. A forecast that stays honest about uncertainty.",
  },
  {
    kicker: "03",
    title: "Quiet",
    body: "Sage on linen. Numbers you can trust. No tickers, no neon, no chrome competing with the work.",
  },
];

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
        setError(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const selected = personas.find((p) => p.id === selectedId) ?? null;

  return (
    <main className="min-h-screen">
      <a className="skip-link" href="#studio">
        Skip to planner
      </a>

      <header className="sticky top-0 z-30 border-b border-line/80 bg-paper/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
          <a href="#top" className="flex items-center gap-3 no-underline">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent" aria-hidden>
              <span className="block h-2.5 w-4 rounded-sm bg-paper" />
            </span>
            <span className="text-sm font-medium tracking-tight text-ink">AI Financial Planner</span>
          </a>
          <div className="flex items-center gap-3">
            <a href="#studio" className="hidden text-sm text-muted transition hover:text-ink sm:inline">
              Studio
            </a>
            {health && (
              <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
                <Badge ok={health.plaid_configured} label="Plaid" />
                <Badge ok={health.anthropic_configured} label="Anthropic" />
              </div>
            )}
          </div>
        </div>
      </header>

      <section id="top" className="relative overflow-hidden">
        <div
          className="pointer-events-none absolute -right-24 top-8 h-80 w-80 rounded-full bg-sage/25 blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -left-16 bottom-0 h-56 w-56 rounded-full bg-paper-deep blur-2xl"
          aria-hidden
        />
        <div className="mx-auto max-w-6xl px-6 pb-20 pt-16 md:pb-28 md:pt-24">
          <p className="eyebrow">Private planning studio</p>
          <h1 className="mt-5 max-w-4xl font-display text-5xl font-medium leading-[0.95] tracking-tightest text-ink sm:text-6xl md:text-7xl">
            The shape of a life
            <span className="block italic text-accent">in numbers.</span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-relaxed text-ink-soft md:text-xl">
            Claude reads the accounts. Monte Carlo draws the horizon. A calm studio for portfolio walkthroughs,
            not a trading floor.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-4">
            <a href="#studio" className="btn-primary">
              Choose a life
            </a>
            <a href="#horizon" className="btn-ghost">
              Run a projection
            </a>
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-card/60">
        <div className="mx-auto grid max-w-6xl grid-cols-1 gap-10 px-6 py-16 md:grid-cols-3 md:gap-12 md:py-20">
          {PILLARS.map((pillar) => (
            <article key={pillar.kicker} className="max-w-sm">
              <p className="num text-xs tracking-[0.18em] text-sage">{pillar.kicker}</p>
              <h2 className="mt-3 font-display text-3xl font-medium tracking-tight">{pillar.title}</h2>
              <p className="mt-4 text-sm leading-relaxed text-muted md:text-[15px]">{pillar.body}</p>
            </article>
          ))}
        </div>
      </section>

      <div id="studio" className="mx-auto max-w-6xl space-y-20 px-6 py-16 md:py-24">
        {error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            {error}. Start the API with <code className="font-num">make api</code>.
          </div>
        )}

        <section className="space-y-6">
          <div className="max-w-2xl space-y-3">
            <p className="eyebrow">Choose a life</p>
            <h2 className="section-title">Three people. Three ledgers.</h2>
            <p className="text-base leading-relaxed text-muted">
              Accounts, goals, and spending load with the profile. Nothing here is financial advice.
            </p>
          </div>
          {loading ? <PersonaSkeleton /> : <PersonaPicker personas={personas} selectedId={selectedId} onSelect={setSelectedId} />}
        </section>

        {selected && (
          <>
            <section className="space-y-6">
              <div className="max-w-2xl space-y-3">
                <p className="eyebrow">The ledger</p>
                <h2 className="section-title">{selected.name.split(" ")[0]}&apos;s books</h2>
                <p className="text-base leading-relaxed text-muted">
                  Plaid sandbox balances for this persona, with the goals those balances are meant to serve.
                </p>
              </div>
              <AccountsTable accounts={selected.accounts} goals={selected.goals} />
            </section>

            <section id="horizon" className="space-y-6">
              <div className="max-w-2xl space-y-3">
                <p className="eyebrow">The horizon</p>
                <h2 className="section-title">
                  What the next <em className="italic text-accent">decades</em> might hold
                </h2>
                <p className="text-base leading-relaxed text-muted">
                  Ten thousand paths. A success rate you can read across the room. Ranges, not a single number
                  dressed as certainty.
                </p>
              </div>
              <SimulatorPanel persona={selected} />
            </section>

            <section className="space-y-6">
              <div className="max-w-2xl space-y-3">
                <p className="eyebrow">The advisor</p>
                <h2 className="section-title">Ask in the context of the books</h2>
                <p className="text-base leading-relaxed text-muted">
                  Grounded on accounts, goals, and transactions for {selected.name}.
                </p>
              </div>
              <AdvisorChat key={selected.id} personaId={selected.id} />
            </section>
          </>
        )}
      </div>

      <footer className="border-t border-line bg-card/40">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-12 text-sm leading-relaxed text-muted md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-display text-lg text-ink">AI Financial Planner</p>
            <p className="mt-2 max-w-md">
              Portfolio demo. Plaid sandbox only. Nothing here is financial advice.
            </p>
          </div>
          <p className="text-xs">Built as a quiet studio, not a market terminal.</p>
        </div>
      </footer>
    </main>
  );
}

function Badge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 ${
        ok ? "bg-sage-wash text-accent" : "bg-paper-deep text-muted"
      }`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-accent" : "bg-muted/70"}`} />
      {label}: {ok ? "live" : "mock"}
    </span>
  );
}

function PersonaSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-3" aria-hidden>
      {[0, 1, 2].map((i) => (
        <div key={i} className="card h-64 animate-pulse bg-paper-deep/80" />
      ))}
    </div>
  );
}

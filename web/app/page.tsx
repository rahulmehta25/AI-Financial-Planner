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
    body: "Warm paper. Numbers you can trust. No tickers, no neon, no chrome competing with the work.",
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
    <main className="min-h-screen bg-paper">
      <a className="skip-link" href="#studio">
        Skip to planner
      </a>

      <header className="sticky top-0 z-30 border-b border-line bg-paper/90 backdrop-blur-md">
        <div className="shell flex items-center justify-between gap-6 py-5">
          <a href="#top" className="font-display text-lg tracking-tight text-ink no-underline">
            AI Financial Planner
          </a>
          <div className="flex items-center gap-6">
            <a href="#studio" className="link hidden text-sm text-ink-soft sm:inline">
              Studio
            </a>
            {health && (
              <div className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 text-xs text-muted">
                <Badge ok={health.plaid_configured} label="Plaid" />
                <Badge ok={health.anthropic_configured} label="Anthropic" />
              </div>
            )}
          </div>
        </div>
      </header>

      <section id="top" className="band band-paper">
        <div className="shell pb-24 pt-20 md:pb-32 md:pt-28">
          <p className="eyebrow rise">Private planning studio</p>
          <h1 className="rise rise-d1 mt-6 max-w-4xl font-display text-5xl font-medium leading-[0.95] tracking-tightest text-ink sm:text-6xl md:text-7xl">
            The shape of a life
            <span className="block italic text-accent">in numbers.</span>
          </h1>
          <p className="rise rise-d2 mt-8 max-w-xl text-lg leading-relaxed text-ink-soft md:text-xl">
            Claude reads the accounts. Monte Carlo draws the horizon. A calm studio for portfolio walkthroughs,
            not a trading floor.
          </p>
          <div className="rise rise-d3 mt-10 flex flex-wrap items-baseline gap-8">
            <a href="#studio" className="btn-primary">
              Choose a life
            </a>
            <a href="#horizon" className="link text-sm text-ink-soft">
              Run a projection
            </a>
          </div>
        </div>
      </section>

      <section className="band band-sand">
        <div className="shell grid grid-cols-1 gap-12 py-20 md:grid-cols-3 md:gap-16 md:py-24">
          {PILLARS.map((pillar, i) => (
            <article
              key={pillar.kicker}
              className={`rise max-w-sm ${i > 0 ? "border-t border-line pt-10 md:border-l md:border-t-0 md:pl-12 md:pt-0" : ""}`}
              style={{ animationDelay: `${0.08 * i}s` }}
            >
              <p className="num text-xs tracking-[0.18em] text-muted">{pillar.kicker}</p>
              <h2 className="mt-3 font-display text-3xl font-medium tracking-tight">{pillar.title}</h2>
              <p className="mt-4 text-[15px] leading-relaxed text-muted">{pillar.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="studio" className="band band-paper">
        <div className="shell space-y-12 py-20 md:py-24">
          {error && (
            <p className="text-sm text-[#9b4a45]">
              {error}. Start the API with <code className="num">make api</code>.
            </p>
          )}
          <div className="rise max-w-2xl space-y-4">
            <p className="eyebrow">Choose a life</p>
            <h2 className="section-title">Three people. Three ledgers.</h2>
            <p className="text-base leading-relaxed text-muted">
              Accounts, goals, and spending load with the profile. Nothing here is financial advice.
            </p>
          </div>
          {loading ? <PersonaSkeleton /> : <PersonaPicker personas={personas} selectedId={selectedId} onSelect={setSelectedId} />}
        </div>
      </section>

      {selected && (
        <>
          <section className="band band-sand">
            <div className="shell space-y-12 py-20 md:py-24">
              <div className="rise max-w-2xl space-y-4">
                <p className="eyebrow">The ledger</p>
                <h2 className="section-title">{selected.name.split(" ")[0]}&apos;s books</h2>
                <p className="text-base leading-relaxed text-muted">
                  Plaid sandbox balances for this persona, with the goals those balances are meant to serve.
                </p>
              </div>
              <AccountsTable accounts={selected.accounts} goals={selected.goals} />
            </div>
          </section>

          <section id="horizon" className="band band-paper">
            <div className="shell space-y-12 py-20 md:py-24">
              <div className="rise max-w-2xl space-y-4">
                <p className="eyebrow">The horizon</p>
                <h2 className="section-title">
                  What the next <em className="italic">decades</em> might hold
                </h2>
                <p className="text-base leading-relaxed text-muted">
                  Ten thousand paths. A success rate you can read across the room. Ranges, not a single number
                  dressed as certainty.
                </p>
              </div>
              <SimulatorPanel persona={selected} />
            </div>
          </section>

          <section className="band band-sand">
            <div className="shell space-y-12 py-20 md:py-24">
              <div className="rise max-w-2xl space-y-4">
                <p className="eyebrow">The advisor</p>
                <h2 className="section-title">Ask in the context of the books</h2>
                <p className="text-base leading-relaxed text-muted">
                  Grounded on accounts, goals, and transactions for {selected.name}.
                </p>
              </div>
              <AdvisorChat key={selected.id} personaId={selected.id} />
            </div>
          </section>
        </>
      )}

      <footer className="band band-paper border-t border-line">
        <div className="shell flex flex-col gap-4 py-16 text-sm leading-relaxed text-muted md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-display text-xl text-ink">AI Financial Planner</p>
            <p className="mt-3 max-w-md">
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
    <span>
      {label}: {ok ? "live" : "mock"}
    </span>
  );
}

function PersonaSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-10 md:grid-cols-3" aria-hidden>
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-48 animate-pulse border-b border-line bg-sand/80 md:border-b-0" />
      ))}
    </div>
  );
}

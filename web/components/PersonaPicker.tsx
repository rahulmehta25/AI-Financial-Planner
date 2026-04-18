"use client";

import type { Persona } from "@/app/api-client";

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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {personas.map((p) => {
        const active = p.id === selectedId;
        return (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            className={`text-left rounded-xl border p-5 transition ${
              active
                ? "border-accent bg-white shadow-md"
                : "border-slate-200 bg-white hover:border-slate-300"
            }`}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{p.name}</h3>
              <span className="text-xs text-muted">age {p.age}</span>
            </div>
            <p className="mt-2 text-sm text-muted">{p.backstory}</p>
            <div className="mt-3 flex gap-3 text-xs text-muted">
              <span>income ${Math.round(p.annual_income / 1000)}k</span>
              <span>savings {Math.round(p.savings_rate * 100)}%</span>
              <span>retire @ {p.retirement_age}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

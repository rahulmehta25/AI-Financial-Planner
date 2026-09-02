"use client";

import { useState } from "react";
import { api, type ChatResponse } from "@/app/api-client";

type Msg = { role: "user" | "assistant"; content: string; tool_calls?: ChatResponse["tool_calls"]; live?: boolean };

const SUGGESTIONS = [
  "What happens if I lose my job for six months?",
  "Can I retire at my target age?",
  "How should I think about my emergency fund given my current accounts?",
];

export function AdvisorChat({ personaId }: { personaId: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send(text: string) {
    if (!text.trim() || sending) return;
    setSending(true);
    setError(null);
    const userMsg: Msg = { role: "user", content: text };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setDraft("");
    try {
      const resp = await api.chat(
        personaId,
        nextMessages.map(({ role, content }) => ({ role, content })),
      );
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content: resp.reply,
          tool_calls: resp.tool_calls,
          live: resp.anthropic_live,
        },
      ]);
    } catch {
      setMessages([
        ...nextMessages,
        {
          role: "assistant",
          content:
            "The live advisor API isn't reachable from this static demo. In the running build this reply streams from Claude, grounded on the selected persona's accounts, transactions, and goals, and cites specific balances. The Monte Carlo simulator panel runs entirely in your browser. Try that for a working taste.",
          tool_calls: [],
          live: false,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="card flex flex-col p-6">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
        <h3 className="text-base font-semibold tracking-tight">Advisor</h3>
        <span className="text-xs text-muted">Grounded on accounts, goals, and transactions</span>
      </div>

      {messages.length === 0 && (
        <div className="mt-5">
          <p className="text-sm text-muted">Try one of these:</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => send(s)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3.5 py-1.5 text-xs leading-relaxed hover:bg-white"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-5 max-h-[420px] flex-1 space-y-3 overflow-y-auto">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-xl px-4 py-3 text-sm leading-relaxed ${
              m.role === "user" ? "ml-10 bg-slate-100" : "mr-10 bg-indigo-50"
            }`}
          >
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.tool_calls && m.tool_calls.length > 0 && (
              <details className="mt-3 text-xs text-muted">
                <summary className="cursor-pointer">
                  Tool hops: {m.tool_calls.map((t) => t.tool).join(", ")}
                  {m.live === false && " (Anthropic API key missing, stub response)"}
                </summary>
                <pre className="mt-2 overflow-x-auto rounded-lg bg-white/60 p-3 text-[11px]">
                  {JSON.stringify(m.tool_calls, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
        {sending && <div className="text-xs text-muted">Claude thinking...</div>}
        {error && <div className="text-xs text-rose-600">{error}</div>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="mt-5 flex flex-col gap-3 sm:flex-row"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about retirement, debt, or income shocks..."
          className="field"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          className="rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white shadow-sm hover:bg-indigo-600 disabled:opacity-60 sm:shrink-0"
        >
          Send
        </button>
      </form>
    </div>
  );
}

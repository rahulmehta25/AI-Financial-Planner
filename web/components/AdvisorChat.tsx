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
            "The live advisor API isn't reachable from this static demo. In the running build this reply streams from Claude, grounded on the selected persona's accounts, transactions, and goals, and cites specific balances. The Monte Carlo simulator panel runs entirely in your browser — try that for a working taste.",
          tool_calls: [],
          live: false,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 flex flex-col">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Advisor</h3>
        <span className="text-xs text-muted">grounded on accounts + goals + transactions</span>
      </div>

      {messages.length === 0 && (
        <div className="mt-4">
          <p className="text-sm text-muted">Try one of these:</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs hover:bg-slate-100"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex-1 space-y-3 max-h-[420px] overflow-y-auto">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm ${
              m.role === "user" ? "bg-slate-100 ml-10" : "bg-indigo-50 mr-10"
            }`}
          >
            <div className="whitespace-pre-wrap">{m.content}</div>
            {m.tool_calls && m.tool_calls.length > 0 && (
              <details className="mt-2 text-xs text-muted">
                <summary className="cursor-pointer">
                  Tool hops: {m.tool_calls.map((t) => t.tool).join(", ")}
                  {m.live === false && " (Anthropic API key missing, stub response)"}
                </summary>
                <pre className="mt-2 bg-white/60 p-2 rounded text-[11px] overflow-x-auto">
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
        className="mt-4 flex gap-2"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about retirement, debt, shocks..."
          className="flex-1 rounded-md border border-slate-200 px-3 py-2 text-sm"
          disabled={sending}
        />
        <button
          type="submit"
          disabled={sending || !draft.trim()}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
        >
          Send
        </button>
      </form>
    </div>
  );
}

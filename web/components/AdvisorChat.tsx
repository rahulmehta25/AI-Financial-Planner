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
            "The live advisor API is not reachable from this static demo. In the running build this reply streams from Claude, grounded on the selected persona's accounts, transactions, and goals, and cites specific balances. The Monte Carlo panel runs entirely in your browser. Try that for a working taste.",
          tool_calls: [],
          live: false,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between sm:gap-4">
        <h3 className="font-display text-2xl font-medium tracking-tight">Advisor</h3>
        <span className="text-xs text-muted">Grounded on accounts, goals, and transactions</span>
      </div>

      {messages.length === 0 && (
        <div className="mt-8">
          <p className="text-sm text-muted">Try one of these:</p>
          <ul className="mt-4 space-y-3">
            {SUGGESTIONS.map((s) => (
              <li key={s}>
                <button type="button" onClick={() => send(s)} className="link text-left text-sm text-ink-soft">
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-8 max-h-[420px] flex-1 space-y-8 overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className={`max-w-2xl text-sm leading-relaxed ${m.role === "user" ? "ml-8 text-muted" : "text-ink"}`}>
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
              {m.role === "user" ? "You" : "Advisor"}
            </p>
            <div className="mt-2 whitespace-pre-wrap">{m.content}</div>
            {m.tool_calls && m.tool_calls.length > 0 && (
              <details className="mt-3 text-xs text-muted">
                <summary className="link cursor-pointer">
                  Tool hops: {m.tool_calls.map((t) => t.tool).join(", ")}
                  {m.live === false && " (Anthropic API key missing, stub response)"}
                </summary>
                <pre className="mt-2 overflow-x-auto border-t border-line pt-3 text-[11px]">
                  {JSON.stringify(m.tool_calls, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
        {sending && <div className="text-xs text-muted">Claude is thinking...</div>}
        {error && <div className="text-xs text-[#9b4a45]">{error}</div>}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(draft);
        }}
        className="mt-10 flex flex-col gap-6 sm:flex-row sm:items-end"
      >
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Ask about retirement, debt, or income shocks"
          className="field"
          disabled={sending}
        />
        <button type="submit" disabled={sending || !draft.trim()} className="btn-primary sm:shrink-0">
          Send
        </button>
      </form>
    </div>
  );
}

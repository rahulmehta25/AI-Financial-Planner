export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type AccountType =
  | "checking"
  | "savings"
  | "brokerage"
  | "retirement"
  | "credit"
  | "mortgage"
  | "auto";

export type Account = {
  id: string;
  name: string;
  type: AccountType;
  balance: number;
  institution: string;
};

export type Goal = {
  id: string;
  kind: "retirement" | "house" | "debt_payoff" | "emergency_fund";
  target_amount: number;
  target_date?: string | null;
  notes: string;
};

export type Transaction = {
  id: string;
  account_id: string;
  date: string;
  amount: number;
  category: string;
  description: string;
};

export type Persona = {
  id: string;
  name: string;
  age: number;
  annual_income: number;
  annual_spending: number;
  savings_rate: number;
  retirement_age: number;
  backstory: string;
  accounts: Account[];
  transactions: Transaction[];
  goals: Goal[];
};

export type SimulationResult = {
  p10_final: number;
  p50_final: number;
  p90_final: number;
  success_probability: number;
  median_path: number[];
  p10_path: number[];
  p90_path: number[];
  num_trials: number;
  horizon_years: number;
};

export type ToolCallTrace = {
  tool: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
};

export type ChatResponse = {
  reply: string;
  tool_calls: ToolCallTrace[];
  grounded_on: string[];
  anthropic_live: boolean;
};

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => json<{ ok: boolean; plaid_configured: boolean; anthropic_configured: boolean; model: string }>("/health"),
  personas: () => json<Persona[]>("/personas"),
  persona: (id: string) => json<Persona>(`/personas/${id}`),
  plaidLinkToken: () => json<{ link_token: string; mock?: boolean }>("/plaid/link-token", {
    method: "POST",
    body: JSON.stringify({ user_id: "demo-user" }),
  }),
  runSimulation: (body: {
    current_assets: number;
    annual_contribution: number;
    current_age: number;
    retirement_age: number;
    annual_spending_in_retirement: number;
    horizon_years?: number;
    num_trials?: number;
    income_shock_months?: number;
  }) =>
    json<SimulationResult>("/simulator/retirement", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  chat: (persona_id: string, messages: { role: "user" | "assistant"; content: string }[]) =>
    json<ChatResponse>("/chat", {
      method: "POST",
      body: JSON.stringify({ persona_id, messages }),
    }),
};

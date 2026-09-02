import type { Account, Goal } from "@/app/api-client";

const fmt = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

const typeLabel: Record<Account["type"], string> = {
  checking: "Checking",
  savings: "Savings",
  brokerage: "Brokerage",
  retirement: "Retirement",
  credit: "Credit",
  mortgage: "Mortgage",
  auto: "Auto",
};

const goalLabel: Record<Goal["kind"], string> = {
  retirement: "Retirement",
  house: "Home",
  debt_payoff: "Debt",
  emergency_fund: "Emergency fund",
};

export function AccountsTable({ accounts, goals }: { accounts: Account[]; goals?: Goal[] }) {
  const net = accounts.reduce((s, a) => s + a.balance, 0);
  return (
    <div className="card overflow-hidden">
      <div className="flex items-start justify-between gap-4 px-6 py-5">
        <div>
          <h3 className="text-base font-semibold tracking-tight">Accounts</h3>
          <p className="mt-1 text-sm text-muted">Plaid sandbox balances for this persona.</p>
        </div>
        <div className="text-right">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">Net worth</div>
          <div className="mt-1 font-mono text-base font-semibold tabular-nums">{fmt(net)}</div>
        </div>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50/80 text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
          <tr>
            <th className="px-6 py-3">Account</th>
            <th className="px-6 py-3">Type</th>
            <th className="px-6 py-3 text-right">Balance</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((a) => (
            <tr key={a.id} className="border-t border-slate-100">
              <td className="px-6 py-3.5">
                <div className="font-medium">{a.name}</div>
                <div className="mt-0.5 text-xs text-muted">{a.institution}</div>
              </td>
              <td className="px-6 py-3.5">
                <span className="rounded-full bg-slate-50 px-2 py-0.5 text-xs text-muted">{typeLabel[a.type]}</span>
              </td>
              <td
                className={`px-6 py-3.5 text-right font-mono tabular-nums ${
                  a.balance < 0 ? "text-rose-600" : "text-ink"
                }`}
              >
                {fmt(a.balance)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {goals && goals.length > 0 && (
        <div className="space-y-3 border-t border-slate-100 bg-slate-50/50 px-6 py-5">
          <h4 className="text-[11px] font-semibold uppercase tracking-wide text-muted">Goals</h4>
          <ul className="space-y-2.5">
            {goals.map((g) => (
              <li key={g.id} className="flex items-baseline justify-between gap-4 text-sm">
                <span className="text-ink">{goalLabel[g.kind]}</span>
                <span className="font-mono tabular-nums text-muted">{fmt(g.target_amount)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

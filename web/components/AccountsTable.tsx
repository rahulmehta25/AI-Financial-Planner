import type { Account, Goal } from "@/app/api-client";
import { money } from "@/app/lib/format";

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
      <div className="flex flex-col gap-4 px-6 py-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h3 className="font-display text-2xl font-medium tracking-tight">Accounts</h3>
          <p className="mt-1 text-sm text-muted">Plaid sandbox balances for this persona.</p>
        </div>
        <div className="sm:text-right">
          <div className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Net worth</div>
          <div className="num mt-1 text-3xl font-medium tracking-tight">{money(net)}</div>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-sage-wash/40 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">
            <tr>
              <th className="px-6 py-3">Account</th>
              <th className="px-6 py-3">Type</th>
              <th className="px-6 py-3 text-right">Balance</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((a) => (
              <tr key={a.id} className="border-t border-line">
                <td className="px-6 py-4">
                  <div className="font-medium">{a.name}</div>
                  <div className="mt-0.5 text-xs text-muted">{a.institution}</div>
                </td>
                <td className="px-6 py-4">
                  <span className="rounded-full bg-paper px-2.5 py-0.5 text-xs text-muted">{typeLabel[a.type]}</span>
                </td>
                <td
                  className={`num px-6 py-4 text-right text-base ${
                    a.balance < 0 ? "text-[#9b4a45]" : "text-ink"
                  }`}
                >
                  {money(a.balance)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {goals && goals.length > 0 && (
        <div className="space-y-4 border-t border-line bg-paper/50 px-6 py-6">
          <h4 className="text-[11px] font-semibold uppercase tracking-[0.16em] text-muted">Goals</h4>
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {goals.map((g) => (
              <li key={g.id} className="flex items-baseline justify-between gap-4 text-sm">
                <span className="text-ink">{goalLabel[g.kind]}</span>
                <span className="num text-muted">{money(g.target_amount)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

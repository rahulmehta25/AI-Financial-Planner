import type { Account } from "@/app/api-client";

const fmt = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

export function AccountsTable({ accounts }: { accounts: Account[] }) {
  const net = accounts.reduce((s, a) => s + a.balance, 0);
  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-200">
        <h3 className="font-semibold">Accounts</h3>
        <span className="text-sm text-muted">
          Net worth: <span className="font-medium text-ink">{fmt(net)}</span>
        </span>
      </div>
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-muted">
          <tr>
            <th className="px-5 py-2">Account</th>
            <th className="px-5 py-2">Type</th>
            <th className="px-5 py-2 text-right">Balance</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((a) => (
            <tr key={a.id} className="border-t border-slate-100">
              <td className="px-5 py-2">{a.name}</td>
              <td className="px-5 py-2 capitalize text-muted">{a.type}</td>
              <td
                className={`px-5 py-2 text-right font-mono ${
                  a.balance < 0 ? "text-rose-600" : "text-ink"
                }`}
              >
                {fmt(a.balance)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

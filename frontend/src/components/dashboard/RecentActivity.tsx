import React from "react";
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownLeft, DollarSign, Repeat2 } from "lucide-react";

interface Transaction {
  id: string;
  type: "buy" | "sell" | "dividend" | "deposit" | "withdrawal" | "fee";
  symbol?: string;
  description: string;
  amount: number;
  date: string;
}

const MOCK_TRANSACTIONS: Transaction[] = [
  { id: "1", type: "buy",        symbol: "NVDA", description: "NVIDIA Corp",        amount: 3240.00, date: "2026-04-10" },
  { id: "2", type: "dividend",   symbol: "VTI",  description: "Vanguard Total Mkt", amount: 142.50,  date: "2026-04-09" },
  { id: "3", type: "deposit",               description: "ACH Deposit",             amount: 2500.00, date: "2026-04-08" },
  { id: "4", type: "sell",       symbol: "TSLA", description: "Tesla Inc",          amount: 1850.00, date: "2026-04-07" },
  { id: "5", type: "buy",        symbol: "AGG",  description: "iShares Agg Bond",   amount: 980.00,  date: "2026-04-05" },
];

const TYPE_CONFIG = {
  buy:        { icon: TrendingUp,      color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", sign: "-", label: "Buy"      },
  sell:       { icon: TrendingDown,    color: "text-blue-400",    bg: "bg-blue-500/10",    border: "border-blue-500/20",    sign: "+", label: "Sell"     },
  dividend:   { icon: DollarSign,      color: "text-gold-light",  bg: "bg-amber-500/10",   border: "border-amber-500/20",   sign: "+", label: "Dividend" },
  deposit:    { icon: ArrowUpRight,    color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", sign: "+", label: "Deposit"  },
  withdrawal: { icon: ArrowDownLeft,   color: "text-red-400",     bg: "bg-red-500/10",     border: "border-red-500/20",     sign: "-", label: "Withdraw" },
  fee:        { icon: Repeat2,         color: "text-muted-foreground", bg: "bg-muted/20", border: "border-border",          sign: "-", label: "Fee"      },
};

interface RecentActivityProps {
  transactions?: Transaction[];
}

const RecentActivity: React.FC<{ transactions?: any[] }> = ({ transactions }) => {
  const data = transactions?.length ? transactions.slice(0, 5) : MOCK_TRANSACTIONS;

  return (
    <div id="recent-activity-card" className="metric-card">
      <div id="recent-activity-header" className="flex items-center justify-between mb-5">
        <div>
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Activity</p>
          <h3 className="text-lg font-bold text-foreground">Recent Transactions</h3>
        </div>
        <button
          id="view-all-activity"
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
        >
          View All <ArrowUpRight className="w-3 h-3" />
        </button>
      </div>

      <div id="activity-list" className="space-y-2">
        {data.map((tx: any, i) => {
          const cfg = TYPE_CONFIG[tx.type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.fee;
          const Icon = cfg.icon;
          const isPositive = cfg.sign === "+";
          return (
            <div
              key={tx.id || i}
              id={`activity-item-${i}`}
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-white/[0.025] transition-colors group"
            >
              {/* Icon */}
              <div
                id={`activity-icon-${i}`}
                className={`w-9 h-9 rounded-xl border ${cfg.bg} ${cfg.border} flex items-center justify-center flex-shrink-0`}
              >
                <Icon className={`w-4 h-4 ${cfg.color}`} />
              </div>

              {/* Details */}
              <div id={`activity-details-${i}`} className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    {tx.symbol && (
                      <span className="text-xs font-bold text-foreground">{tx.symbol}</span>
                    )}
                    <span className="text-xs text-muted-foreground truncate">{tx.description || tx.symbol}</span>
                  </div>
                  <span className={`text-sm font-bold financial-number ${isPositive ? "text-positive" : "text-foreground"}`}>
                    {isPositive ? "+" : "-"}${Math.abs(tx.amount || 0).toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-0.5">
                  <span className="text-[10px] text-muted-foreground/60">{cfg.label}</span>
                  <span className="text-[10px] text-muted-foreground/60">
                    {new Date(tx.date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RecentActivity;

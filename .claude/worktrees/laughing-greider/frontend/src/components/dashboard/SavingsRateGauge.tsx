import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const MONTHLY_DATA = [
  { month: "Oct", income: 9200, expenses: 6800, savings: 2400 },
  { month: "Nov", income: 9200, expenses: 7100, savings: 2100 },
  { month: "Dec", income: 11000, expenses: 8400, savings: 2600 },
  { month: "Jan", income: 9200, expenses: 6500, savings: 2700 },
  { month: "Feb", income: 9200, expenses: 6200, savings: 3000 },
  { month: "Mar", income: 9200, expenses: 6900, savings: 2300 },
];

const formatK = (v: number) => `$${(v / 1000).toFixed(1)}k`;

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div id="cashflow-tooltip" className="glass rounded-xl px-4 py-3 border border-white/10 shadow-xl space-y-1.5">
      <div className="text-xs font-semibold text-foreground mb-1">{label}</div>
      {payload.map((p: any) => (
        <div key={p.name} className="flex items-center gap-2 text-xs">
          <div className="w-2 h-2 rounded-full" style={{ background: p.fill }} />
          <span className="text-muted-foreground capitalize">{p.name}:</span>
          <span className="font-semibold text-foreground financial-number">${p.value.toLocaleString()}</span>
        </div>
      ))}
    </div>
  );
};

interface SavingsRateGaugeProps {
  savingsRate?: number;
  monthlySavings?: number;
  monthlyIncome?: number;
}

const SavingsRateGauge: React.FC<SavingsRateGaugeProps> = ({
  savingsRate = 22,
  monthlySavings = 2300,
  monthlyIncome = 9200,
}) => {
  // Radial gauge params
  const size = 120;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius; // half circle
  const progress = Math.min(savingsRate / 50, 1); // max 50% rate
  const offset = circumference - progress * circumference;

  const rateColor = savingsRate >= 20 ? "#10d077" : savingsRate >= 10 ? "#f9b820" : "#e8384f";
  const rateGlow = savingsRate >= 20 ? "rgba(16,208,119,0.4)" : savingsRate >= 10 ? "rgba(249,184,32,0.4)" : "rgba(232,56,79,0.4)";

  return (
    <div id="savings-rate-card" className="metric-card">
      <div id="savings-rate-header" className="mb-4">
        <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Cash Flow</p>
        <h3 className="text-lg font-bold text-foreground">Savings Rate</h3>
      </div>

      {/* Gauge */}
      <div id="savings-gauge-container" className="flex items-center justify-center mb-4">
        <div className="relative">
          <svg
            id="savings-gauge-svg"
            width={size}
            height={size / 2 + 20}
            style={{ filter: `drop-shadow(0 0 8px ${rateGlow})` }}
          >
            {/* Track (half circle) */}
            <path
              d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
              fill="none"
              stroke="hsl(220 38% 14%)"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />
            {/* Progress */}
            <path
              id="savings-gauge-fill"
              d={`M ${strokeWidth / 2} ${size / 2} A ${radius} ${radius} 0 0 1 ${size - strokeWidth / 2} ${size / 2}`}
              fill="none"
              stroke={rateColor}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.34, 1.56, 0.64, 1)" }}
            />
            {/* Value text */}
            <text x={size / 2} y={size / 2 - 4} textAnchor="middle" fill={rateColor} fontSize={22} fontWeight={700}>
              {savingsRate}%
            </text>
            <text x={size / 2} y={size / 2 + 14} textAnchor="middle" fill="hsl(215 20% 50%)" fontSize={10}>
              Savings Rate
            </text>
          </svg>
        </div>
      </div>

      {/* Stats row */}
      <div id="savings-stats-row" className="grid grid-cols-2 gap-3 mb-4">
        <div id="savings-monthly" className="text-center p-2.5 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
          <div className="text-xs text-muted-foreground mb-0.5">Saved/mo</div>
          <div className="text-sm font-bold text-positive financial-number">${monthlySavings.toLocaleString()}</div>
        </div>
        <div id="savings-income" className="text-center p-2.5 rounded-xl bg-blue-500/5 border border-blue-500/15">
          <div className="text-xs text-muted-foreground mb-0.5">Income/mo</div>
          <div className="text-sm font-bold text-blue-300 financial-number">${monthlyIncome.toLocaleString()}</div>
        </div>
      </div>

      {/* 6-month cash flow chart */}
      <div id="cashflow-chart" className="h-28 -mx-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={MONTHLY_DATA} margin={{ top: 0, right: 4, left: 4, bottom: 0 }} barCategoryGap="25%">
            <XAxis dataKey="month" tick={{ fill: "hsl(215 20% 45%)", fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(220 38% 14% / 0.5)" }} />
            <Bar dataKey="expenses" fill="hsl(356 75% 55% / 0.4)" radius={[3, 3, 0, 0]} name="expenses" />
            <Bar dataKey="savings" fill="hsl(152 69% 40% / 0.7)" radius={[3, 3, 0, 0]} name="savings" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SavingsRateGauge;

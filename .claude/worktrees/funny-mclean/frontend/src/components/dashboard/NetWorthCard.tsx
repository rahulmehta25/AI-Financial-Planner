import React, { useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  defs,
  linearGradient,
  stop,
} from "recharts";
import { TrendingUp, TrendingDown, ArrowUpRight } from "lucide-react";

// Mock 12-month net worth data (replace with real API data)
const generateNetWorthHistory = (currentValue: number) => {
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const now = new Date();
  const currentMonth = now.getMonth();
  return months.slice(0, currentMonth + 1).map((month, i) => {
    const progress = i / Math.max(currentMonth, 1);
    const base = currentValue * 0.7;
    const noise = (Math.random() - 0.4) * currentValue * 0.05;
    return {
      month,
      value: Math.round(base + (currentValue - base) * progress + noise),
    };
  });
};

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div id="net-worth-tooltip" className="glass rounded-xl px-4 py-3 border border-white/10 shadow-xl">
      <div className="text-xs text-muted-foreground mb-1">{label}</div>
      <div className="text-sm font-bold text-foreground financial-number">
        ${payload[0].value.toLocaleString()}
      </div>
    </div>
  );
};

interface NetWorthCardProps {
  totalValue?: number;
  dayChange?: number;
  dayChangePercent?: number;
  totalGain?: number;
  totalGainPercent?: number;
}

const NetWorthCard: React.FC<NetWorthCardProps> = ({
  totalValue = 485320,
  dayChange = 2840,
  dayChangePercent = 0.59,
  totalGain = 85320,
  totalGainPercent = 21.4,
}) => {
  const [chartData, setChartData] = useState<any[]>([]);
  const isPositive = dayChange >= 0;

  useEffect(() => {
    setChartData(generateNetWorthHistory(totalValue));
  }, [totalValue]);

  const formatValue = (v: number) =>
    new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(v);

  return (
    <div id="net-worth-card" className="metric-card metric-card-blue col-span-2 lg:col-span-2">
      {/* Header */}
      <div id="net-worth-header" className="flex items-start justify-between mb-6">
        <div id="net-worth-label-group">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Total Net Worth</p>
          <div id="net-worth-value" className="text-4xl font-bold text-foreground financial-number tracking-tight">
            {formatValue(totalValue)}
          </div>
          <div id="net-worth-change" className="flex items-center gap-2 mt-2">
            <span className={`flex items-center gap-1 text-sm font-semibold ${isPositive ? "text-positive" : "text-negative"}`}>
              {isPositive ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
              {isPositive ? "+" : ""}{formatValue(Math.abs(dayChange))} ({isPositive ? "+" : ""}{dayChangePercent.toFixed(2)}%)
            </span>
            <span className="text-xs text-muted-foreground">today</span>
          </div>
        </div>

        {/* Right stats */}
        <div id="net-worth-stats" className="flex flex-col items-end gap-2">
          <div id="net-worth-total-gain" className="text-right">
            <div className="text-xs text-muted-foreground">All-time gain</div>
            <div className="text-sm font-bold text-positive financial-number">+{formatValue(totalGain)}</div>
            <div className="text-xs text-positive">+{totalGainPercent.toFixed(1)}%</div>
          </div>
          <div id="net-worth-benchmark" className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
            <ArrowUpRight className="w-3 h-3 text-blue-400" />
            <span className="text-xs text-blue-400 font-medium">Beating S&P 500</span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div id="net-worth-chart" className="h-36 -mx-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: 4, bottom: 0 }}>
            <defs>
              <linearGradient id="netWorthGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="hsl(214 100% 57%)" stopOpacity={0.35} />
                <stop offset="60%" stopColor="hsl(214 100% 57%)" stopOpacity={0.08} />
                <stop offset="100%" stopColor="hsl(214 100% 57%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 30% 14%)" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: "hsl(215 20% 45%)", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide domain={["auto", "auto"]} />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: "hsl(214 100% 57% / 0.3)", strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="hsl(214 100% 60%)"
              strokeWidth={2}
              fill="url(#netWorthGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "hsl(214 100% 65%)", strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default NetWorthCard;

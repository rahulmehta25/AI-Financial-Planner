import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, DollarSign, PieChart, BarChart3 } from "lucide-react";
import {
  DEMO_HOLDINGS,
  DEMO_TOTAL_VALUE,
  DEMO_TOTAL_GAIN,
  DEMO_TOTAL_COST,
  DEMO_DAY_CHANGE,
  SECTOR_ALLOCATION,
} from "@/data/demoData";
import { PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const PortfolioPage = () => {
  const totalGainPercent = (DEMO_TOTAL_GAIN / DEMO_TOTAL_COST) * 100;

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Total Value</p>
            <p className="text-2xl font-bold">${DEMO_TOTAL_VALUE.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Total Gain</p>
            <p className="text-2xl font-bold text-emerald-600">+${DEMO_TOTAL_GAIN.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Return</p>
            <p className="text-2xl font-bold text-emerald-600">+{totalGainPercent.toFixed(1)}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <p className="text-xs text-muted-foreground mb-1">Today</p>
            <p className={`text-2xl font-bold ${DEMO_DAY_CHANGE >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
              {DEMO_DAY_CHANGE >= 0 ? '+' : ''}${DEMO_DAY_CHANGE.toLocaleString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Holdings Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-600" />
                Holdings
              </CardTitle>
              <CardDescription>{DEMO_HOLDINGS.length} positions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-muted-foreground text-xs">
                      <th className="text-left py-3 font-medium">Symbol</th>
                      <th className="text-right py-3 font-medium">Shares</th>
                      <th className="text-right py-3 font-medium hidden sm:table-cell">Avg Cost</th>
                      <th className="text-right py-3 font-medium">Price</th>
                      <th className="text-right py-3 font-medium">Value</th>
                      <th className="text-right py-3 font-medium">Gain/Loss</th>
                      <th className="text-right py-3 font-medium hidden md:table-cell">Weight</th>
                    </tr>
                  </thead>
                  <tbody>
                    {DEMO_HOLDINGS.map((h) => (
                      <tr key={h.id} className="border-b last:border-0 hover:bg-muted/30">
                        <td className="py-3">
                          <span className="font-semibold">{h.symbol}</span>
                          <p className="text-xs text-muted-foreground">{h.name}</p>
                        </td>
                        <td className="text-right py-3 tabular-nums">{h.shares}</td>
                        <td className="text-right py-3 tabular-nums hidden sm:table-cell">${h.avgCost.toFixed(2)}</td>
                        <td className="text-right py-3 tabular-nums">
                          ${h.currentPrice.toFixed(2)}
                          <p className={`text-xs ${h.dayChangePercent >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                            {h.dayChangePercent >= 0 ? '+' : ''}{h.dayChangePercent.toFixed(2)}%
                          </p>
                        </td>
                        <td className="text-right py-3 tabular-nums font-medium">${h.marketValue.toLocaleString()}</td>
                        <td className="text-right py-3">
                          <span className={`font-medium ${h.gain >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                            {h.gain >= 0 ? '+' : ''}${h.gain.toLocaleString()}
                          </span>
                          <p className={`text-xs ${h.gainPercent >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                            {h.gainPercent >= 0 ? '+' : ''}{h.gainPercent.toFixed(1)}%
                          </p>
                        </td>
                        <td className="text-right py-3 hidden md:table-cell">
                          <Badge variant="outline" className="font-normal text-xs">{h.allocation.toFixed(1)}%</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Allocation Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base">
                <PieChart className="w-4 h-4 text-emerald-600" />
                Sector Allocation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={200}>
                <RechartsPie>
                  <Pie data={SECTOR_ALLOCATION} cx="50%" cy="50%" innerRadius={40} outerRadius={80} paddingAngle={2} dataKey="value">
                    {SECTOR_ALLOCATION.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip formatter={(v: number) => `${v}%`} />
                </RechartsPie>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {SECTOR_ALLOCATION.map((s) => (
                  <div key={s.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                      <span className="text-muted-foreground">{s.name}</span>
                    </div>
                    <span className="font-medium">{s.value}%</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Holding Weights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {DEMO_HOLDINGS.map((h) => (
                <div key={h.id} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium">{h.symbol}</span>
                    <span className="text-muted-foreground">{h.allocation.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-1.5">
                    <div className="bg-emerald-600 h-1.5 rounded-full" style={{ width: `${h.allocation}%` }} />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PortfolioPage;

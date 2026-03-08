import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Calculator, Play, TrendingUp } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { runClientMonteCarlo } from '@/data/demoData';

const formatCurrency = (v: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(v);

const MonteCarloSimulation: React.FC = () => {
  const [initialInvestment, setInitialInvestment] = useState(100000);
  const [monthlyContribution, setMonthlyContribution] = useState(1000);
  const [timeHorizon, setTimeHorizon] = useState(20);
  const [hasRun, setHasRun] = useState(false);
  const [simKey, setSimKey] = useState(0);

  const results = useMemo(() => {
    if (!hasRun) return null;
    return runClientMonteCarlo(initialInvestment, monthlyContribution, timeHorizon, 1000);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasRun, simKey]);

  const chartData = useMemo(() => {
    if (!results) return [];
    const step = Math.max(1, Math.floor(results.months.length / 120));
    return results.months
      .filter((_, i) => i % step === 0 || i === results.months.length - 1)
      .map((m, idx) => {
        const i = m;
        return {
          month: m,
          year: (m / 12).toFixed(1),
          label: m % 12 === 0 ? `Year ${m / 12}` : '',
          p90: results.p90[i],
          median: results.median[i],
          p10: results.p10[i],
        };
      });
  }, [results]);

  const handleRun = () => {
    setHasRun(true);
    setSimKey((k) => k + 1);
  };

  const finalMedian = results ? results.median[results.median.length - 1] : 0;
  const finalP10 = results ? results.p10[results.p10.length - 1] : 0;
  const finalP90 = results ? results.p90[results.p90.length - 1] : 0;

  return (
    <div className="space-y-6">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="h-5 w-5 text-emerald-600" />
            Simulation Parameters
          </CardTitle>
          <CardDescription>Configure inputs and run 1,000 Monte Carlo paths using geometric Brownian motion</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-6">
            <div className="space-y-2">
              <Label htmlFor="mc-initial">Initial Investment</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
                <Input
                  id="mc-initial"
                  type="number"
                  min={0}
                  value={initialInvestment}
                  onChange={(e) => setInitialInvestment(Number(e.target.value) || 0)}
                  className="pl-7"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="mc-monthly">Monthly Contribution</Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">$</span>
                <Input
                  id="mc-monthly"
                  type="number"
                  min={0}
                  value={monthlyContribution}
                  onChange={(e) => setMonthlyContribution(Number(e.target.value) || 0)}
                  className="pl-7"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="mc-years">Time Horizon (Years)</Label>
              <Input
                id="mc-years"
                type="number"
                min={1}
                max={50}
                value={timeHorizon}
                onChange={(e) => setTimeHorizon(Math.min(50, Math.max(1, Number(e.target.value) || 1)))}
              />
            </div>
          </div>
          <Button onClick={handleRun} className="bg-emerald-600 hover:bg-emerald-700 text-white">
            <Play className="h-4 w-4 mr-2" />
            Run Simulation
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {results && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-5 text-center">
                <p className="text-xs text-muted-foreground mb-1">Median Outcome (P50)</p>
                <p className="text-2xl font-bold text-emerald-600">{formatCurrency(finalMedian)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5 text-center">
                <p className="text-xs text-muted-foreground mb-1">Pessimistic (P10)</p>
                <p className="text-2xl font-bold text-amber-600">{formatCurrency(finalP10)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5 text-center">
                <p className="text-xs text-muted-foreground mb-1">Optimistic (P90)</p>
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(finalP90)}</p>
              </CardContent>
            </Card>
          </div>

          {/* Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-emerald-600" />
                Projected Portfolio Growth
              </CardTitle>
              <CardDescription>
                1,000 simulated paths &middot; 8% expected annual return &middot; 15% volatility
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="month"
                    tickFormatter={(m: number) => m % 12 === 0 ? `Yr ${m / 12}` : ''}
                    interval="preserveStartEnd"
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                  />
                  <YAxis
                    tickFormatter={(v: number) => v >= 1000000 ? `$${(v / 1000000).toFixed(1)}M` : `$${(v / 1000).toFixed(0)}K`}
                    tick={{ fontSize: 12, fill: '#6b7280' }}
                    width={65}
                  />
                  <Tooltip
                    formatter={(v: number, name: string) => [formatCurrency(v), name === 'p90' ? '90th Percentile' : name === 'p10' ? '10th Percentile' : 'Median']}
                    labelFormatter={(m: number) => `Year ${(m / 12).toFixed(1)}`}
                  />
                  <Area type="monotone" dataKey="p90" stroke="#3b82f6" fill="#dbeafe" strokeWidth={1.5} name="p90" />
                  <Area type="monotone" dataKey="median" stroke="#059669" fill="#d1fae5" strokeWidth={2} name="median" />
                  <Area type="monotone" dataKey="p10" stroke="#d97706" fill="#fef3c7" strokeWidth={1.5} name="p10" />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex justify-center gap-6 mt-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500" />
                  <span className="text-muted-foreground">90th Percentile (Optimistic)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-emerald-600" />
                  <span className="text-muted-foreground">Median (Expected)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <span className="text-muted-foreground">10th Percentile (Conservative)</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {!results && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Calculator className="h-12 w-12 mb-4 opacity-40" />
            <p className="text-lg font-medium mb-1">No simulation results yet</p>
            <p className="text-sm">Configure parameters above and click "Run Simulation"</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MonteCarloSimulation;

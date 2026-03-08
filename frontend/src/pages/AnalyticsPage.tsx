import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Target, Calendar, DollarSign, BarChart3, PieChart, Activity } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

const performanceData = {
  monthlyReturn: 8.4,
  yearlyReturn: 12.7,
  sharpeRatio: 1.23,
  volatility: 15.2,
  maxDrawdown: -8.5,
  totalReturn: 156.3,
};

const monthlyChartData = [
  { month: 'Jan', portfolio: 5.2, benchmark: 4.1 },
  { month: 'Feb', portfolio: -2.1, benchmark: -1.8 },
  { month: 'Mar', portfolio: 8.4, benchmark: 6.2 },
  { month: 'Apr', portfolio: 3.7, benchmark: 3.1 },
  { month: 'May', portfolio: -1.2, benchmark: -0.9 },
  { month: 'Jun', portfolio: 6.8, benchmark: 5.4 },
];

const assetPerformance = [
  { name: 'US Stocks', allocation: 45, return: 14.2, risk: 'Medium' },
  { name: 'International', allocation: 25, return: 9.8, risk: 'Medium' },
  { name: 'Bonds', allocation: 20, return: 4.1, risk: 'Low' },
  { name: 'REITs', allocation: 7, return: 11.5, risk: 'High' },
  { name: 'Crypto', allocation: 3, return: 23.7, risk: 'Very High' },
];

const riskMetrics = [
  { name: 'Value at Risk (95%)', value: '-$12,450', status: 'normal' },
  { name: 'Beta', value: '1.08', status: 'normal' },
  { name: 'Correlation to S&P 500', value: '0.87', status: 'high' },
  { name: 'Information Ratio', value: '0.65', status: 'good' },
];

const AnalyticsPage = () => {
  return (
    <div>
      {/* Performance Overview */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {[
          { label: 'Monthly Return', value: `+${performanceData.monthlyReturn}%`, color: 'text-emerald-600', icon: TrendingUp, bg: 'bg-emerald-50' },
          { label: 'Yearly Return', value: `+${performanceData.yearlyReturn}%`, color: 'text-emerald-600', icon: Calendar, bg: 'bg-blue-50' },
          { label: 'Sharpe Ratio', value: `${performanceData.sharpeRatio}`, color: 'text-foreground', icon: Target, bg: 'bg-purple-50' },
          { label: 'Volatility', value: `${performanceData.volatility}%`, color: 'text-foreground', icon: Activity, bg: 'bg-amber-50' },
          { label: 'Max Drawdown', value: `${performanceData.maxDrawdown}%`, color: 'text-red-500', icon: TrendingDown, bg: 'bg-red-50' },
          { label: 'Total Return', value: `+${performanceData.totalReturn}%`, color: 'text-emerald-600', icon: DollarSign, bg: 'bg-emerald-50' },
        ].map(({ label, value, color, icon: Icon, bg }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-8 h-8 rounded-lg ${bg} flex items-center justify-center`}>
                  <Icon className="w-4 h-4 text-current" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className={`text-lg font-bold ${color}`}>{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Monthly Performance Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <BarChart3 className="w-5 h-5 text-emerald-600" />
              Monthly Performance
            </CardTitle>
            <CardDescription>Portfolio vs Benchmark (S&P 500)</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={monthlyChartData} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" tick={{ fontSize: 12 }} />
                <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(v: number) => `${v}%`} />
                <Legend />
                <Bar dataKey="portfolio" name="Portfolio" fill="#059669" radius={[3, 3, 0, 0]} />
                <Bar dataKey="benchmark" name="Benchmark" fill="#94a3b8" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Asset Class Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <PieChart className="w-5 h-5 text-emerald-600" />
              Asset Class Performance
            </CardTitle>
            <CardDescription>Returns by asset allocation</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {assetPerformance.map((asset) => (
              <div key={asset.name} className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <span className="text-xs font-bold text-emerald-600">{asset.allocation}%</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium">{asset.name}</p>
                    <Badge variant="outline" className={`text-xs ${
                      asset.risk === 'Low' ? 'text-emerald-600' :
                      asset.risk === 'Medium' ? 'text-amber-600' :
                      asset.risk === 'High' ? 'text-red-500' :
                      'text-red-600'
                    }`}>
                      {asset.risk}
                    </Badge>
                  </div>
                </div>
                <span className="font-semibold text-emerald-600">+{asset.return}%</span>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Risk Analysis */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Activity className="w-5 h-5 text-emerald-600" />
            Risk Analysis
          </CardTitle>
          <CardDescription>Key risk metrics and exposure analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {riskMetrics.map((metric) => (
              <div key={metric.name} className="text-center p-4 rounded-lg bg-muted/30">
                <p className="text-xs text-muted-foreground mb-2">{metric.name}</p>
                <p className="text-xl font-bold mb-2">{metric.value}</p>
                <Badge variant="outline" className={`text-xs ${
                  metric.status === 'good' ? 'text-emerald-600 border-emerald-200' :
                  metric.status === 'normal' ? 'text-blue-600 border-blue-200' :
                  'text-amber-600 border-amber-200'
                }`}>
                  {metric.status}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AnalyticsPage;

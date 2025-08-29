import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, Target, Calendar, DollarSign, BarChart3, PieChart, Activity } from "lucide-react";

const AnalyticsPage = () => {
  const performanceData = {
    monthlyReturn: 8.4,
    yearlyReturn: 12.7,
    sharpeRatio: 1.23,
    volatility: 15.2,
    maxDrawdown: -8.5,
    totalReturn: 156.3
  };

  const monthlyData = [
    { month: 'Jan', return: 5.2, benchmark: 4.1 },
    { month: 'Feb', return: -2.1, benchmark: -1.8 },
    { month: 'Mar', return: 8.4, benchmark: 6.2 },
    { month: 'Apr', return: 3.7, benchmark: 3.1 },
    { month: 'May', return: -1.2, benchmark: -0.9 },
    { month: 'Jun', return: 6.8, benchmark: 5.4 }
  ];

  const assetPerformance = [
    { name: 'US Stocks', allocation: 45, return: 14.2, risk: 'Medium' },
    { name: 'International', allocation: 25, return: 9.8, risk: 'Medium' },
    { name: 'Bonds', allocation: 20, return: 4.1, risk: 'Low' },
    { name: 'REITs', allocation: 7, return: 11.5, risk: 'High' },
    { name: 'Crypto', allocation: 3, return: 23.7, risk: 'Very High' }
  ];

  const riskMetrics = [
    { name: 'Value at Risk (95%)', value: '-$12,450', status: 'normal' },
    { name: 'Beta', value: '1.08', status: 'normal' },
    { name: 'Correlation to S&P 500', value: '0.87', status: 'high' },
    { name: 'Information Ratio', value: '0.65', status: 'good' }
  ];

  return (
    <div className="">
      
      <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                Portfolio Analytics
              </h1>
              <p className="text-lg text-muted-foreground">
                Deep insights into your investment performance and risk metrics
              </p>
            </div>
            <Badge variant="outline" className="glass border-primary/30 text-primary">
              Last updated: Today
            </Badge>
          </div>

          {/* Performance Overview */}
          <div className="grid grid-cols-1 md:grid-cols-6 gap-6 mb-8">
            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-success to-success-dark flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Monthly Return</p>
                    <p className="text-xl font-bold text-success">+{performanceData.monthlyReturn}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Yearly Return</p>
                    <p className="text-xl font-bold text-success">+{performanceData.yearlyReturn}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
                    <p className="text-xl font-bold">{performanceData.sharpeRatio}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-warning to-warning-dark flex items-center justify-center">
                    <Activity className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Volatility</p>
                    <p className="text-xl font-bold">{performanceData.volatility}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-destructive to-destructive-dark flex items-center justify-center">
                    <TrendingDown className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Max Drawdown</p>
                    <p className="text-xl font-bold text-destructive">{performanceData.maxDrawdown}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary-glow to-success flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Return</p>
                    <p className="text-xl font-bold text-success">+{performanceData.totalReturn}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Monthly Performance */}
          <Card className="glass border-white/10 animate-fade-in">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5" />
                Monthly Performance
              </CardTitle>
              <CardDescription>Portfolio vs Benchmark comparison</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {monthlyData.map((data, index) => (
                <div key={data.month} className="space-y-2 animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{data.month}</span>
                    <div className="flex items-center gap-4">
                      <span className={`text-sm ${data.return > 0 ? 'text-success' : 'text-destructive'}`}>
                        {data.return > 0 ? '+' : ''}{data.return}%
                      </span>
                      <span className="text-sm text-muted-foreground">
                        Benchmark: {data.benchmark > 0 ? '+' : ''}{data.benchmark}%
                      </span>
                    </div>
                  </div>
                  <div className="w-full bg-white/10 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-500 ${
                        data.return > 0 ? 'bg-gradient-to-r from-success to-success-dark' : 'bg-gradient-to-r from-destructive to-destructive-dark'
                      }`}
                      style={{ width: `${Math.min(Math.abs(data.return) * 10, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Asset Performance */}
          <Card className="glass border-white/10 animate-fade-in">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="w-5 h-5" />
                Asset Class Performance
              </CardTitle>
              <CardDescription>Returns by asset allocation</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {assetPerformance.map((asset, index) => (
                <div key={asset.name} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors animate-fade-in" style={{ animationDelay: `${index * 75}ms` }}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                      <span className="text-xs font-bold text-white">{asset.allocation}%</span>
                    </div>
                    <div>
                      <p className="font-medium">{asset.name}</p>
                      <Badge variant="outline" className={`text-xs ${
                        asset.risk === 'Low' ? 'border-success/50 text-success' :
                        asset.risk === 'Medium' ? 'border-warning/50 text-warning' :
                        asset.risk === 'High' ? 'border-destructive/50 text-destructive' :
                        'border-primary/50 text-primary'
                      }`}>
                        {asset.risk}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-success">+{asset.return}%</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Risk Analysis */}
        <Card className="glass border-white/10 animate-fade-in mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Risk Analysis
            </CardTitle>
            <CardDescription>Key risk metrics and exposure analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {riskMetrics.map((metric, index) => (
                <div key={metric.name} className="text-center p-4 rounded-lg bg-white/5 animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                  <p className="text-sm text-muted-foreground mb-2">{metric.name}</p>
                  <p className="text-xl font-bold mb-2">{metric.value}</p>
                  <Badge variant="outline" className={`${
                    metric.status === 'good' ? 'border-success/50 text-success' :
                    metric.status === 'normal' ? 'border-primary/50 text-primary' :
                    metric.status === 'high' ? 'border-warning/50 text-warning' :
                    'border-muted/50 text-muted-foreground'
                  }`}>
                    {metric.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default AnalyticsPage;
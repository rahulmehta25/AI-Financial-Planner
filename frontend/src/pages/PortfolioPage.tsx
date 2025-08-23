import { Navigation } from "@/components/Navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, DollarSign, PieChart, BarChart3, Plus } from "lucide-react";
import { ParticleBackground } from "@/components/ParticleBackground";

const PortfolioPage = () => {
  const portfolioData = {
    totalValue: 485750,
    totalGain: 45750,
    gainPercentage: 10.4,
    dayChange: 2340,
    dayChangePercentage: 0.48
  };

  const assets = [
    {
      name: "Apple Inc.",
      symbol: "AAPL",
      shares: 50,
      currentPrice: 175.23,
      totalValue: 8761.50,
      gain: 1250.50,
      gainPercentage: 16.7,
      allocation: 18
    },
    {
      name: "Microsoft Corp.",
      symbol: "MSFT", 
      shares: 30,
      currentPrice: 415.50,
      totalValue: 12465.00,
      gain: 2100.00,
      gainPercentage: 20.3,
      allocation: 26
    },
    {
      name: "Tesla Inc.",
      symbol: "TSLA",
      shares: 25,
      currentPrice: 245.67,
      totalValue: 6141.75,
      gain: -845.25,
      gainPercentage: -12.1,
      allocation: 13
    },
    {
      name: "S&P 500 ETF",
      symbol: "SPY",
      shares: 100,
      currentPrice: 485.30,
      totalValue: 48530.00,
      gain: 5830.00,
      gainPercentage: 13.7,
      allocation: 43
    }
  ];

  const sectors = [
    { name: "Technology", percentage: 45, color: "from-primary to-primary-glow" },
    { name: "Healthcare", percentage: 20, color: "from-success to-success-dark" },
    { name: "Financial", percentage: 15, color: "from-accent to-accent-dark" },
    { name: "Consumer", percentage: 12, color: "from-warning to-warning-dark" },
    { name: "Energy", percentage: 8, color: "from-destructive to-destructive-dark" }
  ];

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />
      <Navigation />
      
      <main className="relative z-10 pt-20 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                Portfolio Overview
              </h1>
              <p className="text-lg text-muted-foreground">
                Track your investments and market performance
              </p>
            </div>
            <Button className="bg-gradient-to-r from-primary to-success hover:shadow-glow transition-all duration-300">
              <Plus className="w-4 h-4 mr-2" />
              Add Investment
            </Button>
          </div>

          {/* Portfolio Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Value</p>
                    <p className="text-2xl font-bold">${portfolioData.totalValue.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-success to-success-dark flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Gain</p>
                    <p className="text-2xl font-bold text-success">+${portfolioData.totalGain.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Gain %</p>
                    <p className="text-2xl font-bold text-success">+{portfolioData.gainPercentage}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-warning to-warning-dark flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Today</p>
                    <p className="text-2xl font-bold text-success">+${portfolioData.dayChange.toLocaleString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Holdings */}
          <div className="lg:col-span-2">
            <Card className="glass border-white/10 animate-fade-in">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Holdings
                </CardTitle>
                <CardDescription>Your current investment positions</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {assets.map((asset, index) => (
                  <div key={asset.symbol} className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                        <span className="text-sm font-bold text-white">{asset.symbol.charAt(0)}</span>
                      </div>
                      <div>
                        <p className="font-semibold">{asset.name}</p>
                        <p className="text-sm text-muted-foreground">{asset.shares} shares • ${asset.currentPrice}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">${asset.totalValue.toLocaleString()}</p>
                      <div className="flex items-center gap-1">
                        {asset.gain > 0 ? (
                          <TrendingUp className="w-4 h-4 text-success" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-destructive" />
                        )}
                        <span className={asset.gain > 0 ? "text-success" : "text-destructive"}>
                          {asset.gain > 0 ? '+' : ''}${asset.gain.toLocaleString()} ({asset.gainPercentage > 0 ? '+' : ''}{asset.gainPercentage}%)
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Allocation */}
          <div className="space-y-6">
            <Card className="glass border-white/10 animate-fade-in">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <PieChart className="w-5 h-5" />
                  Asset Allocation
                </CardTitle>
                <CardDescription>Portfolio distribution by asset</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {assets.map((asset, index) => (
                  <div key={asset.symbol} className="space-y-2 animate-fade-in" style={{ animationDelay: `${index * 50}ms` }}>
                    <div className="flex justify-between text-sm">
                      <span>{asset.symbol}</span>
                      <span className="font-medium">{asset.allocation}%</span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-primary to-primary-glow h-2 rounded-full transition-all duration-500"
                        style={{ width: `${asset.allocation}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="glass border-white/10 animate-fade-in">
              <CardHeader>
                <CardTitle>Sector Breakdown</CardTitle>
                <CardDescription>Diversification by industry</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {sectors.map((sector, index) => (
                  <div key={sector.name} className="flex items-center justify-between animate-fade-in" style={{ animationDelay: `${index * 75}ms` }}>
                    <div className="flex items-center gap-3">
                      <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${sector.color}`} />
                      <span className="text-sm">{sector.name}</span>
                    </div>
                    <Badge variant="outline" className="glass border-white/20">
                      {sector.percentage}%
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default PortfolioPage;
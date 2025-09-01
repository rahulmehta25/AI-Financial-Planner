import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TrendingUp, TrendingDown, DollarSign, PieChart, BarChart3, Plus, RefreshCw, Zap } from "lucide-react";
import { portfolioService, PortfolioOverview, Holding } from "@/services/portfolio";
import { useToast } from "@/hooks/use-toast";
import { AddHoldingModal } from "@/components/portfolio/AddHoldingModal";

interface SectorData {
  name: string
  percentage: number
  color: string
}

const PortfolioPage = () => {
  const [portfolioOverview, setPortfolioOverview] = useState<PortfolioOverview | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  const { user } = useAuth();
  const { toast } = useToast();

  // Mock sector data - in real app, this would come from backend analysis
  const sectors: SectorData[] = [
    { name: "Technology", percentage: 45, color: "from-primary to-primary-glow" },
    { name: "Healthcare", percentage: 20, color: "from-success to-success-dark" },
    { name: "Financial", percentage: 15, color: "from-accent to-accent-dark" },
    { name: "Consumer", percentage: 12, color: "from-warning to-warning-dark" },
    { name: "Energy", percentage: 8, color: "from-destructive to-destructive-dark" }
  ];

  const fetchPortfolioData = async (showToast = false) => {
    try {
      setIsLoading(true);
      setError(null);

      const [overviewData, holdingsData] = await Promise.all([
        portfolioService.getPortfolioOverview(),
        portfolioService.getHoldings()
      ]);

      setPortfolioOverview(overviewData);
      setHoldings(holdingsData);

      if (showToast) {
        toast({
          title: "Portfolio updated",
          description: "Your portfolio data has been refreshed successfully.",
        });
      }
    } catch (err: any) {
      console.error('Failed to fetch portfolio data:', err);
      const errorMessage = err.message || 'Failed to load portfolio data. Please try again.';
      setError(errorMessage);
      
      toast({
        title: "Error loading portfolio",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPortfolioData();
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchPortfolioData(true);
  };

  const calculateAllocation = (holding: Holding) => {
    if (!portfolioOverview?.totalValue) return 0;
    return Math.round((holding.marketValue / portfolioOverview.totalValue) * 100);
  };

  if (isLoading) {
    return (
      <div id="portfolio-loading" className="">
        
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <Skeleton className="h-10 w-64 mb-2" />
                <Skeleton className="h-6 w-80" />
              </div>
              <Skeleton className="h-10 w-32" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="glass border-white/10">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <Skeleton className="w-12 h-12 rounded-lg" />
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-20" />
                        <Skeleton className="h-6 w-24" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error && !portfolioOverview) {
    return (
      <div id="portfolio-error" className="">
        
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <Alert variant="destructive" className="mb-6">
            <AlertDescription className="flex items-center justify-between">
              <span>{error}</span>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                {isRefreshing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  "Retry"
                )}
              </Button>
            </AlertDescription>
          </Alert>
        </main>
      </div>
    );
  }

  return (
    <div className="">
      
      <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary via-primary-glow to-success mb-2">
                Portfolio Overview
              </h1>
              <p className="text-lg text-muted-foreground">
                {user ? `Welcome back, ${user.firstName}` : 'Track your investments and market performance'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setShowAddModal(true)}
                className="bg-gradient-to-r from-primary to-success hover:opacity-90"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Holding
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isRefreshing}
                className="glass border-white/20"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Link to="/portfolio-optimizer">
                <Button variant="outline" className="glass border-white/20 text-purple-400 hover:text-purple-300">
                  <Zap className="w-4 h-4 mr-2" />
                  Optimize
                </Button>
              </Link>
            </div>
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
                    <p className="text-2xl font-bold">${portfolioOverview?.totalValue.toLocaleString() || '0'}</p>
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
                    <p className={`text-2xl font-bold ${portfolioOverview?.totalGain && portfolioOverview.totalGain >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {portfolioOverview?.totalGain ? 
                        `${portfolioOverview.totalGain >= 0 ? '+' : ''}$${portfolioOverview.totalGain.toLocaleString()}` : 
                        '$0'
                      }
                    </p>
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
                    <p className={`text-2xl font-bold ${portfolioOverview?.totalGainPercentage && portfolioOverview.totalGainPercentage >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {portfolioOverview?.totalGainPercentage ? 
                        `${portfolioOverview.totalGainPercentage >= 0 ? '+' : ''}${portfolioOverview.totalGainPercentage.toFixed(1)}%` : 
                        '0.0%'
                      }
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-warning to-warning-dark flex items-center justify-center">
                    {portfolioOverview?.dayChange && portfolioOverview.dayChange >= 0 ? (
                      <TrendingUp className="w-6 h-6 text-white" />
                    ) : (
                      <TrendingDown className="w-6 h-6 text-white" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Today</p>
                    <p className={`text-2xl font-bold ${portfolioOverview?.dayChange && portfolioOverview.dayChange >= 0 ? 'text-success' : 'text-destructive'}`}>
                      {portfolioOverview?.dayChange ? 
                        `${portfolioOverview.dayChange >= 0 ? '+' : ''}$${portfolioOverview.dayChange.toLocaleString()}` : 
                        '$0'
                      }
                    </p>
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
                {holdings.length > 0 ? holdings.map((holding, index) => (
                  <div key={holding.id} className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                        <span className="text-sm font-bold text-white">{holding.symbol.charAt(0)}</span>
                      </div>
                      <div>
                        <p className="font-semibold">{holding.name}</p>
                        <p className="text-sm text-muted-foreground">{holding.shares} shares • ${holding.currentPrice.toFixed(2)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold">${holding.marketValue.toLocaleString()}</p>
                      <div className="flex items-center gap-1">
                        {holding.totalGain >= 0 ? (
                          <TrendingUp className="w-4 h-4 text-success" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-destructive" />
                        )}
                        <span className={holding.totalGain >= 0 ? "text-success" : "text-destructive"}>
                          {holding.totalGain >= 0 ? '+' : ''}${holding.totalGain.toLocaleString()} ({holding.totalGainPercentage >= 0 ? '+' : ''}{holding.totalGainPercentage.toFixed(1)}%)
                        </span>
                      </div>
                    </div>
                  </div>
                )) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">No holdings found. Start investing to see your portfolio here.</p>
                    <Button className="mt-4 bg-gradient-to-r from-primary to-success">
                      <Plus className="w-4 h-4 mr-2" />
                      Add Your First Investment
                    </Button>
                  </div>
                )}
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
                {holdings.length > 0 ? holdings.map((holding, index) => {
                  const allocation = calculateAllocation(holding);
                  return (
                    <div key={holding.id} className="space-y-2 animate-fade-in" style={{ animationDelay: `${index * 50}ms` }}>
                      <div className="flex justify-between text-sm">
                        <span>{holding.symbol}</span>
                        <span className="font-medium">{allocation}%</span>
                      </div>
                      <div className="w-full bg-white/10 rounded-full h-2">
                        <div 
                          className="bg-gradient-to-r from-primary to-primary-glow h-2 rounded-full transition-all duration-500"
                          style={{ width: `${allocation}%` }}
                        />
                      </div>
                    </div>
                  );
                }) : (
                  <div className="text-center py-4">
                    <p className="text-muted-foreground text-sm">No allocation data available</p>
                  </div>
                )}
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
      
      {/* Add Holding Modal */}
      <AddHoldingModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false)
          fetchPortfolioData(true)
        }}
      />
    </div>
  );
};

export default PortfolioPage;
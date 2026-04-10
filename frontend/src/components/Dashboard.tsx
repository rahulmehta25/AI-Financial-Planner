import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target, 
  PieChart,
  MessageCircle,
  Bell,
  Plus,
  RefreshCw,
  AlertCircle
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { FinancialSimulation } from "./FinancialSimulation";
import { userService, DashboardData } from "@/services/user";
import { portfolioService } from "@/services/portfolio";

export const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async (showToast = false) => {
    try {
      setIsLoading(!dashboardData); // Only show loading on first load
      setIsRefreshing(showToast);
      setError(null);

      const data = await userService.getDashboardData();
      setDashboardData(data);

      if (showToast) {
        toast({
          title: "Dashboard updated",
          description: "Your dashboard data has been refreshed successfully.",
        });
      }
    } catch (err: any) {
      console.error('Failed to fetch dashboard data:', err);
      const errorMessage = err.message || 'Failed to load dashboard data. Please try again.';
      setError(errorMessage);
      
      if (showToast) {
        toast({
          title: "Refresh failed",
          description: errorMessage,
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchDashboardData();
    }
  }, [isAuthenticated]);

  const handleRefresh = () => {
    fetchDashboardData(true);
  };

  // Show loading state
  if (isLoading) {
    return (
      <div>
        <div>
          <div className="mb-8">
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-80" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="glass">
                <CardHeader className="pb-2">
                  <Skeleton className="h-4 w-32" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-24 mb-2" />
                  <Skeleton className="h-4 w-16" />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Show error state
  if (error && !dashboardData) {
    return (
      <div>
        <div>
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
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
        </div>
      </div>
    );
  }

  return (
    <div>
      <div>
        {/* Header */}
        <div className="mb-8 animate-slide-in-bottom">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold mb-2">
                Welcome back, {dashboardData?.user.firstName || user?.firstName || 'there'}!
              </h1>
              <p className="text-muted-foreground text-lg">
                Here's what's happening with your finances today.
              </p>
            </div>
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
          </div>
        </div>

        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card className="glass hover-lift card-3d animate-scale-in">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Portfolio</CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold gradient-primary bg-clip-text text-transparent">
                ${dashboardData?.portfolioSummary?.totalValue?.toLocaleString() || '0'}
              </div>
              <div className="flex items-center gap-2 mt-2">
                {dashboardData?.portfolioSummary?.dayChange !== undefined && dashboardData.portfolioSummary.dayChange >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-success" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-error" />
                )}
                <span className={dashboardData?.portfolioSummary?.dayChange !== undefined && dashboardData.portfolioSummary.dayChange >= 0 ? "text-success font-medium" : "text-error font-medium"}>
                  {dashboardData?.portfolioSummary?.dayChange !== undefined ? 
                    `${dashboardData.portfolioSummary.dayChange >= 0 ? '+' : ''}$${Math.abs(dashboardData.portfolioSummary.dayChange).toLocaleString()} (${dashboardData.portfolioSummary.dayChangePercentage >= 0 ? '+' : ''}${dashboardData.portfolioSummary.dayChangePercentage.toFixed(2)}%)` : 
                    '$0 (0.00%)'}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">Today's performance</p>
            </CardContent>
          </Card>

          <Card className="glass hover-lift card-3d animate-scale-in" style={{ animationDelay: '0.1s' }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Goals</CardTitle>
              <Target className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-success">{dashboardData?.goals?.length || 0}</div>
              <p className="text-xs text-muted-foreground mt-2">
                {dashboardData?.goals?.length ? 
                  `${Math.round(dashboardData.goals.reduce((acc, goal) => acc + goal.progress, 0) / dashboardData.goals.length)}% average progress` :
                  '0% average progress'
                }
              </p>
            </CardContent>
          </Card>

          <Card className="glass hover-lift card-3d animate-scale-in" style={{ animationDelay: '0.2s' }}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Insights</CardTitle>
              <MessageCircle className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                "Consider increasing your emergency fund allocation by 5% this month."
              </div>
              <Button variant="link" className="px-0 mt-2 text-primary">
                View all insights →
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Financial Simulation */}
        <div className="mb-8">
          <FinancialSimulation />
        </div>

        {/* Goals and Chart Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Financial Goals */}
          <Card className="glass hover-lift animate-slide-in-right">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-success" />
                Financial Goals
              </CardTitle>
              <Button variant="outline" size="sm" className="glass border-white/20">
                <Plus className="h-4 w-4 mr-2" />
                Add Goal
              </Button>
            </CardHeader>
            <CardContent className="space-y-6">
              {dashboardData?.goals?.map((goal, index) => (
                <div key={goal.name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">{goal.name}</h4>
                    <span className="text-sm text-muted-foreground">
                      ${goal.currentAmount?.toLocaleString() || '0'} / ${goal.targetAmount?.toLocaleString() || '0'}
                    </span>
                  </div>
                  <Progress value={goal.progress} className="h-2" />
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>{goal.progress}% complete</span>
                    <span>${((goal.targetAmount || 0) - (goal.currentAmount || 0)).toLocaleString()} remaining</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Portfolio Chart Placeholder */}
          <Card className="glass hover-lift animate-slide-in-right" style={{ animationDelay: '0.1s' }}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5 text-primary" />
                Asset Allocation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 bg-gradient-to-br from-primary/10 to-success/10 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <PieChart className="h-12 w-12 text-primary mx-auto mb-4" />
                  <p className="text-muted-foreground">Interactive chart coming soon</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Stocks: 60% • Bonds: 25% • Cash: 15%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card className="glass hover-lift animate-slide-in-bottom">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-warning" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {dashboardData?.recentTransactions?.map((transaction, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-card/50 hover:bg-card/80 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      transaction.type === 'buy' || transaction.type === 'dividend' ? 'bg-success/20' : 'bg-error/20'
                    }`}>
                      {transaction.type === 'buy' || transaction.type === 'dividend' ? 
                        <TrendingUp className="h-5 w-5 text-success" /> : 
                        <TrendingDown className="h-5 w-5 text-error" />
                      }
                    </div>
                    <div>
                      <p className="font-medium">{transaction.symbol || transaction.type}</p>
                      <p className="text-sm text-muted-foreground">{new Date(transaction.date).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className={`font-semibold ${
                    transaction.type === 'buy' || transaction.type === 'dividend' ? 'text-success' : 'text-error'
                  }`}>
                    {transaction.type === 'sell' || transaction.type === 'fee' ? '-' : '+'}${Math.abs(transaction.amount).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
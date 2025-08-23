import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target, 
  PieChart,
  MessageCircle,
  Bell,
  Plus
} from "lucide-react";
import { Progress } from "@/components/ui/progress";

export const Dashboard = () => {
  const portfolioData = {
    totalValue: 125000,
    todayChange: 2340,
    todayPercentage: 1.87,
    goals: [
      { name: "Emergency Fund", current: 15000, target: 25000, progress: 60 },
      { name: "Retirement", current: 85000, target: 500000, progress: 17 },
      { name: "House Down Payment", current: 30000, target: 100000, progress: 30 },
    ],
    recentTransactions: [
      { name: "Salary Deposit", amount: 5000, type: "income", date: "Today" },
      { name: "Grocery Store", amount: -150, type: "expense", date: "Yesterday" },
      { name: "Investment Dividend", amount: 280, type: "income", date: "2 days ago" },
    ]
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/30 pt-20 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-slide-in-bottom">
          <h1 className="text-4xl font-bold mb-2">Welcome back, Alex!</h1>
          <p className="text-muted-foreground text-lg">
            Here's what's happening with your finances today.
          </p>
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
                ${portfolioData.totalValue.toLocaleString()}
              </div>
              <div className="flex items-center gap-2 mt-2">
                <TrendingUp className="h-4 w-4 text-success" />
                <span className="text-success font-medium">
                  +${portfolioData.todayChange.toLocaleString()} ({portfolioData.todayPercentage}%)
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
              <div className="text-3xl font-bold text-success">{portfolioData.goals.length}</div>
              <p className="text-xs text-muted-foreground mt-2">
                {Math.round(portfolioData.goals.reduce((acc, goal) => acc + goal.progress, 0) / portfolioData.goals.length)}% average progress
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
              {portfolioData.goals.map((goal, index) => (
                <div key={goal.name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium">{goal.name}</h4>
                    <span className="text-sm text-muted-foreground">
                      ${goal.current.toLocaleString()} / ${goal.target.toLocaleString()}
                    </span>
                  </div>
                  <Progress value={goal.progress} className="h-2" />
                  <div className="flex justify-between items-center text-xs text-muted-foreground">
                    <span>{goal.progress}% complete</span>
                    <span>${(goal.target - goal.current).toLocaleString()} remaining</span>
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
              {portfolioData.recentTransactions.map((transaction, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-card/50 hover:bg-card/80 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      transaction.type === 'income' ? 'bg-success/20' : 'bg-error/20'
                    }`}>
                      {transaction.type === 'income' ? 
                        <TrendingUp className="h-5 w-5 text-success" /> : 
                        <TrendingDown className="h-5 w-5 text-error" />
                      }
                    </div>
                    <div>
                      <p className="font-medium">{transaction.name}</p>
                      <p className="text-sm text-muted-foreground">{transaction.date}</p>
                    </div>
                  </div>
                  <div className={`font-semibold ${
                    transaction.type === 'income' ? 'text-success' : 'text-error'
                  }`}>
                    {transaction.type === 'income' ? '+' : ''}${Math.abs(transaction.amount).toLocaleString()}
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
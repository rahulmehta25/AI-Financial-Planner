import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Plus, Target, TrendingUp, Calendar, DollarSign, RefreshCw, AlertCircle } from "lucide-react";
import { goalsService, Goal } from "@/services/goals";
import { useToast } from "@/hooks/use-toast";

const GoalsPage = () => {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [statistics, setStatistics] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchGoals = async (showToast = false) => {
    try {
      setIsLoading(!goals.length);
      setIsRefreshing(showToast);
      setError(null);

      const [goalsData, statsData] = await Promise.all([
        goalsService.getGoals(),
        goalsService.getGoalStatistics()
      ]);

      setGoals(goalsData);
      setStatistics(statsData);

      if (showToast) {
        toast({
          title: "Goals refreshed",
          description: "Your goals have been updated successfully.",
        });
      }
    } catch (err: any) {
      console.error('Failed to fetch goals:', err);
      const errorMessage = err.message || 'Failed to load goals. Please try again.';
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
    fetchGoals();
  }, []);

  const handleRefresh = () => {
    fetchGoals(true);
  };


  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'high': return 'text-destructive';
      case 'medium': return 'text-warning';
      case 'low': return 'text-muted-foreground';
      default: return 'text-foreground';
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="">
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
          <div className="mb-8">
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-80" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="glass border-white/10">
                <CardContent className="p-6">
                  <Skeleton className="h-12 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="glass border-white/10">
                <CardContent className="p-6">
                  <Skeleton className="h-32 w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        </main>
      </div>
    );
  }

  // Show error state
  if (error && !goals.length) {
    return (
      <div className="">
        <main className="relative z-10 pt-0 px-6 max-w-7xl mx-auto">
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
                Financial Goals
              </h1>
              <p className="text-lg text-muted-foreground">
                Track your progress and achieve your financial dreams
              </p>
            </div>
            <div className="flex gap-2">
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
              <Button className="bg-gradient-to-r from-primary to-success hover:shadow-glow transition-all duration-300">
                <Plus className="w-4 h-4 mr-2" />
                Add Goal
              </Button>
            </div>
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center">
                    <Target className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Goals</p>
                    <p className="text-2xl font-bold">{statistics?.totalGoals || goals.length}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-success to-success-dark flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Target</p>
                    <p className="text-2xl font-bold">
                      ${statistics?.totalTargetAmount ? 
                        (statistics.totalTargetAmount >= 1000000 ? 
                          `${(statistics.totalTargetAmount / 1000000).toFixed(2)}M` : 
                          `${(statistics.totalTargetAmount / 1000).toFixed(0)}K`) : 
                        '0'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Saved</p>
                    <p className="text-2xl font-bold">
                      ${statistics?.totalCurrentAmount ? 
                        (statistics.totalCurrentAmount >= 1000000 ? 
                          `${(statistics.totalCurrentAmount / 1000000).toFixed(2)}M` : 
                          `${(statistics.totalCurrentAmount / 1000).toFixed(1)}K`) : 
                        '0'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="glass border-white/10 hover-scale">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-warning to-warning-dark flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Avg Progress</p>
                    <p className="text-2xl font-bold">{statistics?.averageProgress || 0}%</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Goals Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">
          {goals.map((goal, index) => (
            <Card key={goal.id} className="glass border-white/10 hover-scale animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-xl font-semibold">{goal.name}</CardTitle>
                  <span className={`text-sm font-medium capitalize ${getPriorityColor(goal.priority)}`}>
                    {goal.priority} Priority
                  </span>
                </div>
                <CardDescription className="text-muted-foreground">
                  {goal.category} • Target: {new Date(goal.targetDate).toLocaleDateString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-medium">{goal.progress}%</span>
                  </div>
                  <Progress value={goal.progress} className="h-2" />
                </div>

                {/* Amount Info */}
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-muted-foreground">Current</p>
                    <p className="text-lg font-semibold text-success">
                      ${goal.currentAmount.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Target</p>
                    <p className="text-lg font-semibold">
                      ${goal.targetAmount.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Remaining Amount */}
                <div className="pt-4 border-t border-white/10">
                  <p className="text-sm text-muted-foreground">Remaining</p>
                  <p className="text-xl font-bold text-primary">
                    ${(goal.targetAmount - goal.currentAmount).toLocaleString()}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="flex-1 glass border-white/20">
                    Edit Goal
                  </Button>
                  <Button size="sm" className="flex-1 bg-gradient-to-r from-primary to-success">
                    Add Funds
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="pb-20"></div>
      </main>
    </div>
  );
};

export default GoalsPage;
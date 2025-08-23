import { Navigation } from "@/components/Navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Plus, Target, TrendingUp, Calendar, DollarSign } from "lucide-react";
import { ParticleBackground } from "@/components/ParticleBackground";

const GoalsPage = () => {
  const goals = [
    {
      id: 1,
      name: "Emergency Fund",
      targetAmount: 50000,
      currentAmount: 32000,
      targetDate: "2024-12-31",
      priority: "high",
      category: "Security",
      progress: 64
    },
    {
      id: 2,
      name: "House Down Payment",
      targetAmount: 100000,
      currentAmount: 45000,
      targetDate: "2025-06-30",
      priority: "high", 
      category: "Real Estate",
      progress: 45
    },
    {
      id: 3,
      name: "Vacation Fund",
      targetAmount: 15000,
      currentAmount: 8500,
      targetDate: "2024-08-15",
      priority: "medium",
      category: "Lifestyle",
      progress: 57
    },
    {
      id: 4,
      name: "Retirement Fund",
      targetAmount: 1000000,
      currentAmount: 125000,
      targetDate: "2045-01-01",
      priority: "high",
      category: "Retirement",
      progress: 13
    }
  ];

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case 'high': return 'text-destructive';
      case 'medium': return 'text-warning';
      case 'low': return 'text-muted-foreground';
      default: return 'text-foreground';
    }
  };

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
                Financial Goals
              </h1>
              <p className="text-lg text-muted-foreground">
                Track your progress and achieve your financial dreams
              </p>
            </div>
            <Button className="bg-gradient-to-r from-primary to-success hover:shadow-glow transition-all duration-300">
              <Plus className="w-4 h-4 mr-2" />
              Add Goal
            </Button>
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
                    <p className="text-2xl font-bold">{goals.length}</p>
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
                    <p className="text-2xl font-bold">$1.17M</p>
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
                    <p className="text-2xl font-bold">$210.5K</p>
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
                    <p className="text-2xl font-bold">45%</p>
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
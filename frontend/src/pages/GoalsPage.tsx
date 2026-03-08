import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Target, DollarSign, TrendingUp, Home, Shield, Sunset } from "lucide-react";
import { DEMO_GOALS } from "@/data/demoData";

const goalIcons: Record<string, React.ElementType> = {
  sunset: Sunset,
  shield: Shield,
  home: Home,
};

const GoalsPage = () => {
  const totalTarget = DEMO_GOALS.reduce((s, g) => s + g.targetAmount, 0);
  const totalCurrent = DEMO_GOALS.reduce((s, g) => s + g.currentAmount, 0);
  const avgProgress = Math.round(DEMO_GOALS.reduce((s, g) => s + g.progress, 0) / DEMO_GOALS.length);

  return (
    <div>
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                <Target className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Goals</p>
                <p className="text-2xl font-bold">{DEMO_GOALS.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Target</p>
                <p className="text-2xl font-bold">
                  ${totalTarget >= 1000000 ? `${(totalTarget / 1000000).toFixed(1)}M` : `${(totalTarget / 1000).toFixed(0)}K`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Saved</p>
                <p className="text-2xl font-bold">
                  ${totalCurrent >= 1000000 ? `${(totalCurrent / 1000000).toFixed(1)}M` : `${(totalCurrent / 1000).toFixed(0)}K`}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center">
                <Target className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Avg Progress</p>
                <p className="text-2xl font-bold">{avgProgress}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {DEMO_GOALS.map((goal) => {
          const Icon = goalIcons[goal.icon] || Target;
          const remaining = goal.targetAmount - goal.currentAmount;
          return (
            <Card key={goal.id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
                      <Icon className="w-5 h-5 text-emerald-600" />
                    </div>
                    {goal.name}
                  </CardTitle>
                  <span className={`text-xs font-medium capitalize px-2 py-1 rounded-full ${
                    goal.priority === 'high' ? 'bg-red-50 text-red-600' :
                    goal.priority === 'medium' ? 'bg-amber-50 text-amber-600' :
                    'bg-gray-50 text-gray-600'
                  }`}>
                    {goal.priority}
                  </span>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Progress</span>
                    <span className="font-semibold">{goal.progress}%</span>
                  </div>
                  <Progress value={goal.progress} className="h-3" />
                </div>

                {/* Amounts */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Saved</p>
                    <p className="text-lg font-bold text-emerald-600">
                      ${goal.currentAmount >= 1000000
                        ? `${(goal.currentAmount / 1000000).toFixed(1)}M`
                        : goal.currentAmount.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">Target</p>
                    <p className="text-lg font-bold">
                      ${goal.targetAmount >= 1000000
                        ? `${(goal.targetAmount / 1000000).toFixed(1)}M`
                        : goal.targetAmount.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Remaining */}
                <div className="pt-3 border-t">
                  <div className="flex justify-between items-center">
                    <div>
                      <p className="text-xs text-muted-foreground">Remaining</p>
                      <p className="text-base font-bold">
                        ${remaining >= 1000000
                          ? `${(remaining / 1000000).toFixed(1)}M`
                          : remaining.toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Target Date</p>
                      <p className="text-sm font-medium">
                        {new Date(goal.targetDate).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
                      </p>
                    </div>
                  </div>
                </div>

                <Button variant="outline" size="sm" className="w-full">
                  Add Funds
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
};

export default GoalsPage;

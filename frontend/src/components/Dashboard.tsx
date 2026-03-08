import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  PieChart,
  MessageCircle,
  Bell,
} from "lucide-react";
import {
  DEMO_TOTAL_VALUE,
  DEMO_DAY_CHANGE,
  DEMO_GOALS,
  DEMO_RECENT_TRANSACTIONS,
  SECTOR_ALLOCATION,
} from "@/data/demoData";
import { PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

export const Dashboard = () => {
  const navigate = useNavigate();
  const dayChangePercent = (DEMO_DAY_CHANGE / DEMO_TOTAL_VALUE) * 100;

  return (
    <div>
      {/* Portfolio Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Portfolio</CardTitle>
            <DollarSign className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">${DEMO_TOTAL_VALUE.toLocaleString()}</div>
            <div className="flex items-center gap-2 mt-2">
              {DEMO_DAY_CHANGE >= 0 ? (
                <TrendingUp className="h-4 w-4 text-emerald-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className={`text-sm font-medium ${DEMO_DAY_CHANGE >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                {DEMO_DAY_CHANGE >= 0 ? '+' : ''}${DEMO_DAY_CHANGE.toLocaleString()} ({dayChangePercent >= 0 ? '+' : ''}{dayChangePercent.toFixed(2)}%)
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Today's performance</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Active Goals</CardTitle>
            <Target className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{DEMO_GOALS.length}</div>
            <p className="text-sm text-muted-foreground mt-2">
              {Math.round(DEMO_GOALS.reduce((acc, g) => acc + g.progress, 0) / DEMO_GOALS.length)}% average progress
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">AI Insights</CardTitle>
            <MessageCircle className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              "Consider increasing your emergency fund allocation by 5% this month."
            </p>
            <Button variant="link" className="px-0 mt-2 text-emerald-600" onClick={() => navigate('/ai-advisor')}>
              View all insights →
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Goals and Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Target className="h-5 w-5 text-emerald-600" />
              Financial Goals
            </CardTitle>
            <Button variant="outline" size="sm" onClick={() => navigate('/goals')}>View All</Button>
          </CardHeader>
          <CardContent className="space-y-5">
            {DEMO_GOALS.map((goal) => (
              <div key={goal.id} className="space-y-2">
                <div className="flex justify-between items-center">
                  <h4 className="font-medium text-sm">{goal.name}</h4>
                  <span className="text-xs text-muted-foreground">
                    ${goal.currentAmount.toLocaleString()} / ${goal.targetAmount.toLocaleString()}
                  </span>
                </div>
                <Progress value={goal.progress} className="h-2" />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>{goal.progress}% complete</span>
                  <span>${(goal.targetAmount - goal.currentAmount).toLocaleString()} remaining</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <PieChart className="h-5 w-5 text-emerald-600" />
              Sector Allocation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div style={{ width: '100%', minHeight: 240 }}>
              <ResponsiveContainer width="100%" height={240} minWidth={200}>
                <RechartsPie>
                  <Pie
                    data={SECTOR_ALLOCATION}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={95}
                    paddingAngle={2}
                    dataKey="value"
                    nameKey="name"
                    label={({ name, value }) => `${name} ${value}%`}
                    labelLine={false}
                  >
                    {SECTOR_ALLOCATION.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => `${v}%`} />
                </RechartsPie>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bell className="h-5 w-5 text-amber-500" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {DEMO_RECENT_TRANSACTIONS.map((tx) => (
              <div key={tx.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    tx.type === 'buy' || tx.type === 'dividend' ? 'bg-emerald-50 text-emerald-600' : 'bg-red-50 text-red-500'
                  }`}>
                    {tx.type === 'buy' || tx.type === 'dividend' ?
                      <TrendingUp className="h-4 w-4" /> :
                      <TrendingDown className="h-4 w-4" />
                    }
                  </div>
                  <div>
                    <p className="text-sm font-medium">{tx.symbol} · {tx.type.charAt(0).toUpperCase() + tx.type.slice(1)}</p>
                    <p className="text-xs text-muted-foreground">{new Date(tx.date).toLocaleDateString()}</p>
                  </div>
                </div>
                <span className={`text-sm font-semibold ${
                  tx.type === 'sell' ? 'text-red-500' : 'text-emerald-600'
                }`}>
                  {tx.type === 'sell' ? '-' : '+'}${tx.amount.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

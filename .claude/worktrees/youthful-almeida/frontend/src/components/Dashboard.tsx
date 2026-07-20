import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { RefreshCw, AlertCircle, BrainCircuit, LineChart, BarChart3, Sparkles, ArrowRight } from "lucide-react";

import { userService, DashboardData } from "@/services/user";

// Premium dashboard sub-components
import NetWorthCard from "./dashboard/NetWorthCard";
import AssetAllocationDonut from "./dashboard/AssetAllocationDonut";
import GoalProgressRings from "./dashboard/GoalProgressRings";
import FinancialHealthScore from "./dashboard/FinancialHealthScore";
import SavingsRateGauge from "./dashboard/SavingsRateGauge";
import QuickAIInsight from "./dashboard/QuickAIInsight";
import RecentActivity from "./dashboard/RecentActivity";

/* ─── Skeleton Loader ─── */
const DashboardSkeleton = () => (
  <div id="dashboard-skeleton" className="space-y-6 animate-fade-in">
    <div id="skeleton-header" className="flex items-center justify-between pt-6">
      <div className="space-y-2">
        <Skeleton className="h-7 w-56 rounded-xl bg-navy-800" />
        <Skeleton className="h-4 w-40 rounded-lg bg-navy-800" />
      </div>
      <Skeleton className="h-8 w-24 rounded-xl bg-navy-800" />
    </div>
    <div id="skeleton-top-row" className="grid grid-cols-1 lg:grid-cols-3 gap-5">
      <Skeleton className="h-56 rounded-2xl bg-navy-800 lg:col-span-2" />
      <Skeleton className="h-56 rounded-2xl bg-navy-800" />
    </div>
    <div id="skeleton-mid-row" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
      {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-48 rounded-2xl bg-navy-800" />)}
    </div>
    <div id="skeleton-bottom-row" className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <Skeleton className="h-64 rounded-2xl bg-navy-800" />
      <Skeleton className="h-64 rounded-2xl bg-navy-800" />
    </div>
  </div>
);

/* ─── Quick Nav Cards ─── */
const QUICK_LINKS = [
  { label: "Monte Carlo",   desc: "Simulate outcomes",    icon: LineChart,    path: "/monte-carlo",         color: "blue"   },
  { label: "AI Advisor",    desc: "Get personalized tips", icon: BrainCircuit, path: "/ai-advisor",          color: "violet" },
  { label: "Analytics",     desc: "Deep dive reports",    icon: BarChart3,    path: "/analytics",           color: "emerald"},
];

const colorMap: Record<string, { bg: string; border: string; text: string }> = {
  blue:   { bg: "bg-blue-500/8",   border: "border-blue-500/20",   text: "text-blue-400"   },
  violet: { bg: "bg-violet-500/8", border: "border-violet-500/20", text: "text-violet-400" },
  emerald:{ bg: "bg-emerald-500/8",border: "border-emerald-500/20",text: "text-emerald-400"},
};

/* ─── Main Dashboard ─── */
export const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading]         = useState(true);
  const [isRefreshing, setIsRefreshing]   = useState(false);
  const [error, setError]                 = useState<string | null>(null);

  const fetchData = async (refresh = false) => {
    try {
      if (!dashboardData) setIsLoading(true);
      setIsRefreshing(refresh);
      setError(null);
      const data = await userService.getDashboardData();
      setDashboardData(data);
      if (refresh) toast({ title: "Dashboard refreshed", description: "All data is up to date." });
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data.");
      if (refresh) toast({ title: "Refresh failed", description: err.message, variant: "destructive" });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => { if (isAuthenticated) fetchData(); }, [isAuthenticated]);

  if (isLoading) return <DashboardSkeleton />;

  if (error && !dashboardData) {
    return (
      <div id="dashboard-error" className="pt-6">
        <Alert variant="destructive" className="glass border-red-500/30 bg-red-500/5">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="flex items-center justify-between">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={() => fetchData(true)} disabled={isRefreshing}
              className="ml-4 border-red-500/30 hover:bg-red-500/10">
              {isRefreshing ? <RefreshCw className="w-4 h-4 animate-spin" /> : "Retry"}
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const portfolio = dashboardData?.portfolioSummary;
  const firstName = dashboardData?.user?.firstName || user?.firstName || "there";
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";

  return (
    <div id="dashboard-root" className="space-y-6 pt-5 pb-10 page-enter">

      {/* ─── Header ─── */}
      <div id="dashboard-header" className="flex items-start justify-between">
        <div id="dashboard-greeting">
          <h1 id="dashboard-title" className="text-2xl font-bold text-foreground tracking-tight">
            {greeting}, <span className="text-gradient-primary">{firstName}</span>
          </h1>
          <p id="dashboard-subtitle" className="text-sm text-muted-foreground mt-0.5">
            {new Date().toLocaleDateString("en-US", { weekday: "long", year: "numeric", month: "long", day: "numeric" })}
          </p>
        </div>

        <div id="dashboard-header-actions" className="flex items-center gap-2">
          <Button
            id="dashboard-refresh-btn"
            variant="ghost"
            size="sm"
            onClick={() => fetchData(true)}
            disabled={isRefreshing}
            className="h-8 px-3 text-xs text-muted-foreground hover:text-foreground hover:bg-white/[0.06] border border-white/10 gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          <Button
            id="dashboard-ai-btn"
            size="sm"
            onClick={() => navigate("/ai-advisor")}
            className="h-8 px-3 text-xs gap-1.5 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white border-0 shadow-glow-blue"
          >
            <Sparkles className="w-3.5 h-3.5" />
            Ask AI
          </Button>
        </div>
      </div>

      {/* ─── ROW 1: Net Worth (wide) + Asset Allocation ─── */}
      <div id="dashboard-row-1" className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Net Worth spans 2 cols */}
        <div id="dashboard-net-worth-wrapper" className="lg:col-span-2 animate-slide-in-bottom">
          <NetWorthCard
            totalValue={portfolio?.totalValue ?? 485320}
            dayChange={portfolio?.dayChange ?? 2840}
            dayChangePercent={portfolio?.dayChangePercentage ?? 0.59}
            totalGain={portfolio?.totalGain ?? 85320}
            totalGainPercent={portfolio?.totalGainPercentage ?? 21.4}
          />
        </div>

        {/* Asset Allocation donut */}
        <div id="dashboard-allocation-wrapper" className="animate-slide-in-bottom stagger-2">
          <AssetAllocationDonut />
        </div>
      </div>

      {/* ─── ROW 2: Goals | Health Score | Savings | AI Insight ─── */}
      <div id="dashboard-row-2" className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5">
        <div id="dashboard-goals-wrapper" className="animate-scale-in stagger-1">
          <GoalProgressRings />
        </div>
        <div id="dashboard-health-wrapper" className="animate-scale-in stagger-2">
          <FinancialHealthScore score={82} />
        </div>
        <div id="dashboard-savings-wrapper" className="animate-scale-in stagger-3">
          <SavingsRateGauge savingsRate={22} monthlySavings={2300} monthlyIncome={9200} />
        </div>
        <div id="dashboard-ai-insight-wrapper" className="animate-scale-in stagger-4 flex flex-col gap-4">
          <QuickAIInsight />

          {/* Quick links */}
          <div id="dashboard-quick-links" className="space-y-2">
            {QUICK_LINKS.map((link) => {
              const Icon = link.icon;
              const c = colorMap[link.color];
              return (
                <button
                  key={link.path}
                  id={`quick-link-${link.label.toLowerCase().replace(/\s/g, "-")}`}
                  onClick={() => navigate(link.path)}
                  className={`w-full flex items-center gap-3 p-3 rounded-xl border ${c.bg} ${c.border} hover:opacity-90 transition-all text-left group`}
                >
                  <div className={`w-7 h-7 rounded-lg ${c.bg} ${c.border} border flex items-center justify-center flex-shrink-0`}>
                    <Icon className={`w-3.5 h-3.5 ${c.text}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-xs font-semibold ${c.text}`}>{link.label}</div>
                    <div className="text-[10px] text-muted-foreground">{link.desc}</div>
                  </div>
                  <ArrowRight className={`w-3 h-3 ${c.text} opacity-0 group-hover:opacity-100 transition-opacity`} />
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ─── ROW 3: Recent Activity ─── */}
      <div id="dashboard-row-3" className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div id="dashboard-activity-wrapper" className="animate-slide-in-bottom stagger-1">
          <RecentActivity transactions={dashboardData?.recentTransactions} />
        </div>

        {/* Portfolio performance mini card */}
        <div id="dashboard-performance-wrapper" className="animate-slide-in-bottom stagger-2">
          <div id="dashboard-performance-card" className="metric-card h-full">
            <div id="performance-header" className="mb-5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest mb-1">Performance</p>
              <h3 className="text-lg font-bold text-foreground">Portfolio Summary</h3>
            </div>

            <div id="performance-stats" className="space-y-4">
              {[
                { label: "Total Portfolio Value", value: `$${(portfolio?.totalValue ?? 485320).toLocaleString()}`,     color: "text-foreground"   },
                { label: "Total Gain / Loss",     value: `+$${(portfolio?.totalGain ?? 85320).toLocaleString()}`,      color: "text-positive"    },
                { label: "Day Change",            value: `+$${(portfolio?.dayChange ?? 2840).toLocaleString()} (+0.59%)`, color: "text-positive" },
                { label: "Annualized Return",     value: "9.4%",                                                        color: "text-blue-300"    },
                { label: "Sharpe Ratio",          value: "1.42",                                                        color: "text-gold-light"  },
                { label: "Beta",                  value: "0.87",                                                        color: "text-muted-foreground" },
              ].map((stat, i) => (
                <div key={stat.label} id={`perf-stat-${i}`} className="flex items-center justify-between py-2 border-b border-white/[0.04] last:border-0">
                  <span className="text-sm text-muted-foreground">{stat.label}</span>
                  <span className={`text-sm font-bold financial-number ${stat.color}`}>{stat.value}</span>
                </div>
              ))}
            </div>

            <Button
              id="view-portfolio-btn"
              variant="outline"
              size="sm"
              onClick={() => navigate("/portfolio")}
              className="w-full mt-5 h-8 text-xs border-white/10 hover:bg-white/[0.04] hover:border-white/20 gap-1.5"
            >
              View Full Portfolio <ArrowRight className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ParticleBackground } from "@/components/ParticleBackground";
import {
  TrendingUp,
  PieChart,
  Target,
  LineChart,
  Calculator,
  MessageCircle,
  BarChart3,
  User,
  Settings,
  LogOut,
  Home,
  Wallet,
  BrainCircuit,
  DollarSign,
  Activity,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Bell,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  description: string;
  badge?: string;
  color?: string;
}

const navItems: NavItem[] = [
  { id: "dashboard",        label: "Dashboard",        icon: Home,          path: "/dashboard",           description: "Overview & Summary",        color: "text-blue-400"   },
  { id: "portfolio",        label: "Portfolio",         icon: Wallet,        path: "/portfolio",           description: "Holdings & Performance",    color: "text-emerald-400"},
  { id: "optimizer",        label: "Optimizer",         icon: Target,        path: "/portfolio-optimizer", description: "Portfolio Optimization",    color: "text-violet-400" },
  { id: "monte-carlo",      label: "Monte Carlo",       icon: LineChart,     path: "/monte-carlo",         description: "Risk Simulation",           color: "text-blue-400"   },
  { id: "tax",              label: "Tax Planning",      icon: DollarSign,    path: "/tax-optimization",    description: "Tax Optimization",          color: "text-gold-light" },
  { id: "ai-advisor",       label: "AI Advisor",        icon: BrainCircuit,  path: "/ai-advisor",          description: "Personalized Advice",       color: "text-primary",   badge: "AI" },
  { id: "analytics",        label: "Analytics",         icon: BarChart3,     path: "/analytics",           description: "Reports & Insights",        color: "text-purple-400" },
  { id: "realtime",         label: "Real-Time",         icon: Activity,      path: "/realtime",            description: "Live Market Data",          color: "text-emerald-400"},
];

export const AuthenticatedLayout = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [activeId, setActiveId] = useState("dashboard");

  useEffect(() => {
    const match = navItems.find((item) => item.path === location.pathname);
    if (match) setActiveId(match.id);
  }, [location.pathname]);

  const handleNavigate = (item: NavItem) => {
    setActiveId(item.id);
    navigate(item.path);
  };

  const handleLogout = () => { logout(); navigate("/"); };

  const getUserInitials = () => {
    if (!user) return "U";
    return `${user.firstName?.charAt(0) || ""}${user.lastName?.charAt(0) || ""}`.toUpperCase() || user.email?.charAt(0)?.toUpperCase() || "U";
  };

  const currentItem = navItems.find((item) => item.id === activeId);

  useEffect(() => {
    if (!isAuthenticated) navigate("/login");
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  return (
    <div id="authenticated-layout-root" className="flex min-h-screen bg-background">
      <ParticleBackground />

      {/* ─── SIDEBAR ─── */}
      <aside
        id="sidebar-container"
        className={`
          fixed left-0 top-0 bottom-0 z-40 flex flex-col
          transition-all duration-300 ease-in-out
          border-r border-white/[0.06]
          ${collapsed ? "w-[72px]" : "w-[260px]"}
        `}
        style={{ background: "linear-gradient(180deg, hsl(222 50% 5%) 0%, hsl(220 45% 7%) 100%)" }}
      >
        {/* Logo */}
        <div id="sidebar-logo" className={`flex items-center h-16 px-4 border-b border-white/[0.06] flex-shrink-0 ${collapsed ? "justify-center" : "gap-3"}`}>
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center flex-shrink-0 shadow-glow-blue">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          {!collapsed && (
            <div id="sidebar-brand-text">
              <div className="text-sm font-bold text-white tracking-tight">FinanceAI</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-widest">Premium</div>
            </div>
          )}
        </div>

        {/* Nav Items */}
        <nav id="sidebar-nav" className="flex-1 px-3 py-4 overflow-y-auto space-y-1">
          {/* Section label */}
          {!collapsed && (
            <div id="sidebar-nav-label" className="px-3 mb-3">
              <span className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.12em]">Navigation</span>
            </div>
          )}

          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeId === item.id;
            return (
              <button
                key={item.id}
                id={`sidebar-nav-${item.id}`}
                onClick={() => handleNavigate(item)}
                title={collapsed ? item.label : undefined}
                className={`
                  w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left
                  transition-all duration-200 relative group
                  ${isActive
                    ? "bg-blue-500/10 border border-blue-500/20 text-blue-300"
                    : "text-muted-foreground hover:text-foreground hover:bg-white/[0.04] border border-transparent"
                  }
                  ${collapsed ? "justify-center" : ""}
                `}
              >
                {/* Active indicator */}
                {isActive && (
                  <span
                    id={`sidebar-indicator-${item.id}`}
                    className="absolute left-0 top-1/4 bottom-1/4 w-0.5 bg-blue-400 rounded-r-full"
                  />
                )}

                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? "text-blue-400" : ""}`} />

                {!collapsed && (
                  <>
                    <span className="flex-1 text-sm font-medium">{item.label}</span>
                    {item.badge && (
                      <span id={`sidebar-badge-${item.id}`} className="badge-gold text-[10px] px-1.5 py-0.5">
                        {item.badge}
                      </span>
                    )}
                  </>
                )}

                {/* Tooltip for collapsed */}
                {collapsed && (
                  <div
                    id={`sidebar-tooltip-${item.id}`}
                    className="absolute left-full ml-3 px-3 py-1.5 glass rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 border border-white/10"
                  >
                    {item.label}
                  </div>
                )}
              </button>
            );
          })}
        </nav>

        {/* Bottom: User + Collapse */}
        <div id="sidebar-footer" className="border-t border-white/[0.06] p-3 space-y-2 flex-shrink-0">
          {/* Collapse toggle */}
          <button
            id="sidebar-collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-muted-foreground hover:text-foreground hover:bg-white/[0.04] transition-all duration-200 ${collapsed ? "justify-center" : ""}`}
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <><ChevronLeft className="w-4 h-4" /><span className="text-sm">Collapse</span></>}
          </button>

          {/* User */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                id="sidebar-user-btn"
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white/[0.04] transition-all duration-200 ${collapsed ? "justify-center" : ""}`}
              >
                <Avatar className="h-7 w-7 flex-shrink-0 ring-2 ring-blue-500/30">
                  <AvatarImage src={user?.profileImage} alt={user?.firstName || ""} />
                  <AvatarFallback className="bg-gradient-to-br from-blue-600 to-blue-800 text-white text-xs">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <div className="text-left min-w-0" id="sidebar-user-info">
                    <div className="text-xs font-semibold text-foreground truncate">
                      {user?.firstName} {user?.lastName}
                    </div>
                    <div className="text-[10px] text-muted-foreground truncate">{user?.email}</div>
                  </div>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-52 glass border border-white/10 bg-navy-850" side="right" align="end">
              <div className="px-3 py-2 border-b border-white/10" id="sidebar-dropdown-user">
                <div className="text-sm font-semibold">{user?.firstName} {user?.lastName}</div>
                <div className="text-xs text-muted-foreground">{user?.email}</div>
              </div>
              <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer gap-2">
                <User className="h-4 w-4" /> Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/settings")} className="cursor-pointer gap-2">
                <Settings className="h-4 w-4" /> Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer gap-2 text-red-400 focus:text-red-400">
                <LogOut className="h-4 w-4" /> Sign Out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* ─── MAIN CONTENT ─── */}
      <div
        id="main-content-wrapper"
        className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${collapsed ? "ml-[72px]" : "ml-[260px]"}`}
      >
        {/* Top bar */}
        <header
          id="top-bar"
          className="fixed top-0 right-0 z-30 h-16 flex items-center justify-between px-6 border-b border-white/[0.06]"
          style={{
            left: collapsed ? "72px" : "260px",
            background: "hsl(222 47% 5% / 0.95)",
            backdropFilter: "blur(20px)",
            transition: "left 0.3s ease-in-out",
          }}
        >
          {/* Page title */}
          <div id="top-bar-title" className="flex items-center gap-3">
            {currentItem && (
              <>
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                  <currentItem.icon className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <h1 className="text-sm font-semibold text-foreground">{currentItem.label}</h1>
                  <p className="text-[11px] text-muted-foreground">{currentItem.description}</p>
                </div>
              </>
            )}
          </div>

          {/* Top-right actions */}
          <div id="top-bar-actions" className="flex items-center gap-3">
            {/* Live indicator */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <span className="status-dot-green" />
              <span className="text-xs text-emerald-400 font-medium">Live</span>
            </div>

            {/* AI Advisor shortcut */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/ai-advisor")}
              className="hidden md:flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground hover:bg-white/[0.06] border border-transparent hover:border-white/10"
            >
              <Sparkles className="w-3.5 h-3.5 text-gold-light" />
              Ask AI
            </Button>

            {/* Notification bell */}
            <Button variant="ghost" size="sm" className="w-8 h-8 p-0 text-muted-foreground hover:text-foreground hover:bg-white/[0.06]">
              <Bell className="w-4 h-4" />
            </Button>

            {/* Avatar dropdown (duplicate for easy access) */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-8 w-8 p-0 rounded-full">
                  <Avatar className="h-8 w-8 ring-2 ring-blue-500/20">
                    <AvatarImage src={user?.profileImage} />
                    <AvatarFallback className="bg-gradient-to-br from-blue-600 to-blue-800 text-white text-xs">
                      {getUserInitials()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-52 glass border border-white/10 bg-navy-850" align="end">
                <div className="px-3 py-2 border-b border-white/10">
                  <div className="text-sm font-semibold">{user?.firstName} {user?.lastName}</div>
                  <div className="text-xs text-muted-foreground">{user?.email}</div>
                </div>
                <DropdownMenuItem onClick={() => navigate("/profile")} className="cursor-pointer gap-2"><User className="h-4 w-4" />Profile</DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/settings")} className="cursor-pointer gap-2"><Settings className="h-4 w-4" />Settings</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="cursor-pointer gap-2 text-red-400 focus:text-red-400"><LogOut className="h-4 w-4" />Sign Out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main id="page-main" className="flex-1 pt-16 pb-8 px-6 relative z-10">
          <div id="page-content-inner" className="max-w-[1400px] mx-auto page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AuthenticatedLayout;

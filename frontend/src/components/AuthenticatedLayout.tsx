import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useDemo } from "@/contexts/DemoContext";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  TrendingUp,
  Target,
  LineChart,
  DollarSign,
  BrainCircuit,
  BarChart3,
  User,
  Settings,
  LogOut,
  Home,
  Wallet,
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
}

export const AuthenticatedLayout = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const { isDemoMode } = useDemo();
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("dashboard");

  const navItems: NavItem[] = [
    { id: "dashboard", label: "Dashboard", icon: Home, path: "/dashboard" },
    { id: "portfolio", label: "Portfolio", icon: Wallet, path: "/portfolio" },
    { id: "goals", label: "Goals", icon: Target, path: "/goals" },
    { id: "monte-carlo", label: "Monte Carlo", icon: LineChart, path: "/monte-carlo" },
    { id: "tax", label: "Tax Planning", icon: DollarSign, path: "/tax-optimization" },
    { id: "ai-advisor", label: "AI Advisor", icon: BrainCircuit, path: "/ai-advisor" },
    { id: "analytics", label: "Analytics", icon: BarChart3, path: "/analytics" },
  ];

  useEffect(() => {
    const currentPath = location.pathname;
    if (currentPath === "/" || currentPath === "/dashboard") {
      setActiveTab("dashboard");
    } else {
      const matchingItem = navItems.find(item => item.path === currentPath);
      if (matchingItem) setActiveTab(matchingItem.id);
    }
  }, [location.pathname]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    const item = navItems.find(nav => nav.id === value);
    if (item) navigate(item.path);
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const displayName = user?.firstName || (isDemoMode ? "Demo User" : "User");

  useEffect(() => {
    if (!isAuthenticated && !isDemoMode) {
      navigate("/login");
    }
  }, [isAuthenticated, isDemoMode, navigate]);

  if (!isAuthenticated && !isDemoMode) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* Top Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-foreground">FinanceAI</span>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-3">
              <span className="hidden md:block text-sm text-muted-foreground">
                Welcome, <span className="font-medium text-foreground">{displayName}</span>
              </span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-9 w-9 rounded-full">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback className="bg-emerald-600 text-white text-sm">
                        {isDemoMode ? "DU" : (user?.email?.charAt(0) || "U").toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-48" align="end">
                  <div className="px-2 py-1.5">
                    <p className="text-sm font-medium">{isDemoMode ? "Demo User" : user?.email}</p>
                    <p className="text-xs text-muted-foreground">{isDemoMode ? "demo@financeai.com" : user?.email}</p>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/profile")}>
                    <User className="mr-2 h-4 w-4" /> Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/settings")}>
                    <Settings className="mr-2 h-4 w-4" /> Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-500">
                    <LogOut className="mr-2 h-4 w-4" /> Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-t">
          <div className="max-w-7xl mx-auto px-4 sm:px-6">
            <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
              <TabsList className="w-full justify-start h-11 bg-transparent rounded-none border-0 p-0 overflow-x-auto">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <TabsTrigger
                      key={item.id}
                      value={item.id}
                      className="flex items-center gap-1.5 px-3 h-11 rounded-none border-b-2 border-transparent text-muted-foreground data-[state=active]:border-emerald-600 data-[state=active]:text-emerald-600 data-[state=active]:bg-transparent text-sm"
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden sm:inline">{item.label}</span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </Tabs>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-28 pb-8 px-4 sm:px-6">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AuthenticatedLayout;

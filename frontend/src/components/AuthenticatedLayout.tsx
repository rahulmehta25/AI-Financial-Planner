import { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
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
  Activity
} from "lucide-react";

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path: string;
  description: string;
}

export const AuthenticatedLayout = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [activeTab, setActiveTab] = useState("dashboard");

  // Define navigation items with icons and descriptions
  const navItems: NavItem[] = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: Home,
      path: "/dashboard",
      description: "Overview & Summary"
    },
    {
      id: "portfolio",
      label: "Portfolio",
      icon: Wallet,
      path: "/portfolio",
      description: "Holdings & Performance"
    },
    {
      id: "optimizer",
      label: "Optimizer",
      icon: Target,
      path: "/portfolio-optimizer",
      description: "Portfolio Optimization"
    },
    {
      id: "monte-carlo",
      label: "Monte Carlo",
      icon: LineChart,
      path: "/monte-carlo",
      description: "Risk Simulation"
    },
    {
      id: "tax",
      label: "Tax Planning",
      icon: DollarSign,
      path: "/tax-optimization",
      description: "Tax Optimization"
    },
    {
      id: "ai-advisor",
      label: "AI Advisor",
      icon: BrainCircuit,
      path: "/ai-advisor",
      description: "Personalized Advice"
    },
    {
      id: "analytics",
      label: "Analytics",
      icon: BarChart3,
      path: "/analytics",
      description: "Reports & Insights"
    },
    {
      id: "realtime",
      label: "Real-Time",
      icon: Activity,
      path: "/realtime",
      description: "Live Market Data"
    }
  ];

  // Update active tab based on current path
  useEffect(() => {
    const currentPath = location.pathname;
    const matchingItem = navItems.find(item => item.path === currentPath);
    if (matchingItem) {
      setActiveTab(matchingItem.id);
    }
  }, [location.pathname]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    const item = navItems.find(nav => nav.id === value);
    if (item) {
      navigate(item.path);
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const getUserInitials = () => {
    if (!user) return "U";
    const firstInitial = user.firstName?.charAt(0) || user.email?.charAt(0) || "";
    const lastInitial = user.lastName?.charAt(0) || "";
    return `${firstInitial}${lastInitial}`.toUpperCase();
  };

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate("/login");
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen relative">
      <ParticleBackground />
      
      {/* Top Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-success flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
                FinanceAI
              </span>
            </div>

            {/* User Menu */}
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
                Welcome back, <span className="font-semibold text-foreground">{user?.firstName || "User"}</span>
              </div>
              
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-10 w-10 rounded-full">
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={user?.profileImage} alt={user?.firstName || ""} />
                      <AvatarFallback className="bg-gradient-to-br from-primary to-success text-white">
                        {getUserInitials()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56 glass border-white/20" align="end">
                  <div className="flex items-center justify-start gap-2 p-2">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">{user?.firstName} {user?.lastName}</p>
                      <p className="text-xs text-muted-foreground">{user?.email}</p>
                    </div>
                  </div>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate("/profile")}>
                    <User className="mr-2 h-4 w-4" />
                    Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/settings")}>
                    <Settings className="mr-2 h-4 w-4" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-500">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="border-t border-white/10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6">
            <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
              <TabsList className="w-full justify-start h-14 bg-transparent rounded-none border-0 p-0 overflow-x-auto">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <TabsTrigger
                      key={item.id}
                      value={item.id}
                      className="flex items-center gap-2 px-4 h-14 rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
                    >
                      <Icon className="w-4 h-4" />
                      <span className="hidden sm:inline">{item.label}</span>
                      <span className="sm:hidden">{item.label.split(' ')[0]}</span>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </Tabs>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="pt-32 pb-8 px-4 sm:px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Page Header */}
          <div className="mb-8">
            {(() => {
              const currentItem = navItems.find(item => item.id === activeTab);
              if (currentItem) {
                const Icon = currentItem.icon;
                return (
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-success/20 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h1 className="text-3xl font-bold">{currentItem.label}</h1>
                      <p className="text-muted-foreground">{currentItem.description}</p>
                    </div>
                  </div>
                );
              }
              return null;
            })()}
          </div>

          {/* Route Content */}
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AuthenticatedLayout;
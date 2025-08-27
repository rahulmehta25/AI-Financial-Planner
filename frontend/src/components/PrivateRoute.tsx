import { useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, TrendingUp } from "lucide-react";

interface PrivateRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}

const PrivateRoute: React.FC<PrivateRouteProps> = ({ 
  children, 
  requireAuth = true 
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading spinner while authentication state is being determined
  if (isLoading) {
    return (
      <div id="auth-loading-screen" className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex items-center justify-center">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-success/10 rounded-full blur-3xl" />
        </div>

        <Card id="loading-card" className="relative glass border-white/10 w-full max-w-sm">
          <CardContent id="loading-content" className="flex flex-col items-center justify-center p-8 space-y-6">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-success flex items-center justify-center">
                <TrendingUp className="w-7 h-7 text-white" />
              </div>
              <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-success">
                FinanceAI
              </span>
            </div>

            {/* Loading spinner */}
            <div className="flex flex-col items-center space-y-4">
              <div className="relative">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <div className="absolute inset-0 rounded-full border-2 border-primary/20" />
              </div>
              <div className="text-center space-y-1">
                <p className="text-sm font-medium">Authenticating...</p>
                <p className="text-xs text-muted-foreground">Please wait while we verify your session</p>
              </div>
            </div>

            {/* Loading progress indicator */}
            <div className="w-full">
              <div className="w-full bg-muted/20 rounded-full h-1">
                <div className="bg-gradient-to-r from-primary to-success h-1 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // If authentication is required and user is not authenticated, redirect to login
  if (requireAuth && !isAuthenticated) {
    return (
      <Navigate 
        to="/login" 
        state={{ from: location }} 
        replace 
      />
    );
  }

  // If user is authenticated but shouldn't be (like login/register pages), redirect to dashboard
  if (!requireAuth && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // Render the protected component
  return <>{children}</>;
};

export default PrivateRoute;
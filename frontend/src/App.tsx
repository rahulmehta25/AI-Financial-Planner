import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import PrivateRoute from "@/components/PrivateRoute";

// Public pages
import Index from "./pages/Index";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";

// Protected pages
import DashboardPage from "./pages/DashboardPage";
import GoalsPage from "./pages/GoalsPage";
import PortfolioPage from "./pages/PortfolioPage";
import ChatPage from "./pages/ChatPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import ProfilePage from "./pages/ProfilePage";

// Fallback
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<Index />} />
            
            {/* Authentication routes (redirect to dashboard if already logged in) */}
            <Route 
              path="/login" 
              element={
                <PrivateRoute requireAuth={false}>
                  <LoginPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/register" 
              element={
                <PrivateRoute requireAuth={false}>
                  <RegisterPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/forgot-password" 
              element={
                <PrivateRoute requireAuth={false}>
                  <ForgotPasswordPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/reset-password" 
              element={
                <PrivateRoute requireAuth={false}>
                  <ResetPasswordPage />
                </PrivateRoute>
              } 
            />
            
            {/* Protected routes */}
            <Route 
              path="/dashboard" 
              element={
                <PrivateRoute>
                  <DashboardPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/goals" 
              element={
                <PrivateRoute>
                  <GoalsPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/portfolio" 
              element={
                <PrivateRoute>
                  <PortfolioPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/chat" 
              element={
                <PrivateRoute>
                  <ChatPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <PrivateRoute>
                  <AnalyticsPage />
                </PrivateRoute>
              } 
            />
            <Route 
              path="/profile" 
              element={
                <PrivateRoute>
                  <ProfilePage />
                </PrivateRoute>
              } 
            />
            
            {/* Fallback route */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
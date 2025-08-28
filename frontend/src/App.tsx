import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import { Toaster } from './components/ui/sonner'
import ProtectedRoute from './components/ProtectedRoute'

// Pages
import Index from './pages/Index'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import SignupPage from './pages/SignupPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import DashboardPage from './pages/DashboardPage'
import { RealTimeDashboard } from './pages/RealTimeDashboard'
import PortfolioPage from './pages/PortfolioPage'
import GoalsPage from './pages/GoalsPage'
import AnalyticsPage from './pages/AnalyticsPage'
import AIAdvisor from './pages/AIAdvisor'
import ProfilePage from './pages/ProfilePage'
import { TaxOptimization } from './pages/TaxOptimization'
import MonteCarloSimulation from './pages/MonteCarloSimulation'
import PortfolioOptimizer from './pages/PortfolioOptimizer'
import NotFound from './pages/NotFound'

import './App.css'

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 4xx errors (client errors)
        if (error?.status >= 400 && error?.status < 500) {
          return false
        }
        // Retry up to 3 times for other errors
        return failureCount < 3
      },
      refetchOnWindowFocus: false, // Don't refetch on window focus by default
      refetchOnReconnect: true, // Refetch when connection is restored
      refetchOnMount: true, // Refetch when component mounts
    },
    mutations: {
      retry: (failureCount, error: any) => {
        // Don't retry mutations on client errors
        if (error?.status >= 400 && error?.status < 500) {
          return false
        }
        return failureCount < 2
      },
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public Routes */}
              <Route path="/" element={<Index />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/signup" element={<SignupPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              
              {/* Protected Routes */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <DashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/realtime"
                element={
                  <ProtectedRoute>
                    <RealTimeDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/portfolio"
                element={
                  <ProtectedRoute>
                    <PortfolioPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/goals"
                element={
                  <ProtectedRoute>
                    <GoalsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/analytics"
                element={
                  <ProtectedRoute>
                    <AnalyticsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <AIAdvisor />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/tax-optimization"
                element={
                  <ProtectedRoute>
                    <TaxOptimization />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/monte-carlo"
                element={
                  <ProtectedRoute>
                    <MonteCarloSimulation />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/portfolio-optimizer"
                element={
                  <ProtectedRoute>
                    <PortfolioOptimizer />
                  </ProtectedRoute>
                }
              />
              
              {/* Redirect /app to /dashboard for backward compatibility */}
              <Route path="/app" element={<Navigate to="/dashboard" replace />} />
              
              {/* Catch-all route for 404 */}
              <Route path="*" element={<NotFound />} />
            </Routes>
            
            {/* Global Toast Notifications */}
            <Toaster 
              position="top-right"
              expand={false}
              richColors
              closeButton
              toastOptions={{
                duration: 4000,
                classNames: {
                  error: 'border-red-500 bg-red-50 text-red-900',
                  success: 'border-green-500 bg-green-50 text-green-900',
                  warning: 'border-yellow-500 bg-yellow-50 text-yellow-900',
                  info: 'border-blue-500 bg-blue-50 text-blue-900',
                },
              }}
            />
          </div>
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
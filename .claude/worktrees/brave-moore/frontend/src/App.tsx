import { lazy, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from './contexts/AuthContext'
import { DemoProvider } from './contexts/DemoContext'
import { Toaster } from './components/ui/sonner'
import ProtectedRoute from './components/ProtectedRoute'
import AuthenticatedLayout from './components/AuthenticatedLayout'
import { Skeleton } from './components/ui/skeleton'

// Eagerly load the landing page and auth pages (above-the-fold, small)
import Index from './pages/Index'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import SignupPage from './pages/SignupPage'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import NotFound from './pages/NotFound'

// Lazy-load all authenticated/heavy pages to reduce initial bundle
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const RealTimeDashboard = lazy(() =>
  import('./pages/RealTimeDashboard').then((m) => ({ default: m.RealTimeDashboard })),
)
const PortfolioPage = lazy(() => import('./pages/PortfolioPage'))
const GoalsPage = lazy(() => import('./pages/GoalsPage'))
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'))
const AIAdvisor = lazy(() => import('./pages/AIAdvisor'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const TaxOptimization = lazy(() =>
  import('./pages/TaxOptimization').then((m) => ({ default: m.TaxOptimization })),
)
const MonteCarloSimulation = lazy(() => import('./pages/MonteCarloSimulation'))
const PortfolioOptimizer = lazy(() => import('./pages/PortfolioOptimizer'))

// Full-page loading fallback
function PageLoader() {
  return (
    <div className="flex flex-col gap-4 p-8 min-h-screen bg-background" role="status" aria-label="Loading page" aria-busy="true">
      <Skeleton className="h-8 w-48 rounded skeleton-shimmer" />
      <Skeleton className="h-4 w-full rounded skeleton-shimmer" />
      <Skeleton className="h-4 w-3/4 rounded skeleton-shimmer" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <Skeleton className="h-40 rounded-xl skeleton-shimmer" />
        <Skeleton className="h-40 rounded-xl skeleton-shimmer" />
        <Skeleton className="h-40 rounded-xl skeleton-shimmer" />
      </div>
      <span className="sr-only">Loading...</span>
    </div>
  )
}

// TanStack Query v5-compatible client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
      retry: (failureCount, error: unknown) => {
        const status = (error as { status?: number })?.status
        if (status !== undefined && status >= 400 && status < 500) return false
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      refetchOnMount: true,
    },
    mutations: {
      retry: (failureCount, error: unknown) => {
        const status = (error as { status?: number })?.status
        if (status !== undefined && status >= 400 && status < 500) return false
        return failureCount < 2
      },
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <DemoProvider>
          <Router>
            <div className="App">
              <Suspense fallback={<PageLoader />}>
                <Routes>
                  {/* Public Routes */}
                  <Route path="/" element={<Index />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/signup" element={<SignupPage />} />
                  <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                  <Route path="/reset-password" element={<ResetPasswordPage />} />

                  {/* Protected Routes with Authenticated Layout */}
                  <Route element={<ProtectedRoute><AuthenticatedLayout /></ProtectedRoute>}>
                    <Route path="/dashboard" element={<DashboardPage />} />
                    <Route path="/realtime" element={<RealTimeDashboard />} />
                    <Route path="/portfolio" element={<PortfolioPage />} />
                    <Route path="/goals" element={<GoalsPage />} />
                    <Route path="/analytics" element={<AnalyticsPage />} />
                    <Route path="/ai-advisor" element={<AIAdvisor />} />
                    <Route path="/chat" element={<AIAdvisor />} />
                    <Route path="/profile" element={<ProfilePage />} />
                    <Route path="/tax-optimization" element={<TaxOptimization />} />
                    <Route path="/monte-carlo" element={<MonteCarloSimulation />} />
                    <Route path="/portfolio-optimizer" element={<PortfolioOptimizer />} />
                    <Route path="/settings" element={<ProfilePage />} />
                  </Route>

                  {/* Redirect /app to /dashboard for backward compatibility */}
                  <Route path="/app" element={<Navigate to="/dashboard" replace />} />

                  {/* Catch-all route for 404 */}
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </Suspense>

              {/* Global Toast Notifications */}
              <Toaster
                position="top-right"
                expand={false}
                richColors
                closeButton
                toastOptions={{
                  duration: 4000,
                  classNames: {
                    error: 'border-red-500/50',
                    success: 'border-green-500/50',
                    warning: 'border-yellow-500/50',
                    info: 'border-blue-500/50',
                  },
                }}
              />
            </div>
          </Router>
        </DemoProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App

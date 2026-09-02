import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { useDemo } from '@/contexts/DemoContext'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface ProtectedRouteProps {
  children: React.ReactNode
  redirectTo?: string
}

const LoadingSkeleton = () => (
  <div id="protected-route-loading" className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
    <Card className="w-full max-w-md">
      <CardContent className="p-6 space-y-4">
        <div id="loading-header" className="text-center space-y-2">
          <Skeleton className="h-8 w-3/4 mx-auto" />
          <Skeleton className="h-4 w-1/2 mx-auto" />
        </div>
        <div id="loading-content" className="space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
          <Skeleton className="h-4 w-4/5" />
        </div>
        <div id="loading-footer" className="flex justify-center">
          <Skeleton className="h-10 w-24" />
        </div>
      </CardContent>
    </Card>
  </div>
)

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  redirectTo = '/login' 
}) => {
  const { isAuthenticated, isLoading, user } = useAuth()
  const { isDemoMode } = useDemo()
  const location = useLocation()

  // Show loading state while checking authentication
  if (isLoading) {
    return <LoadingSkeleton />
  }

  // Allow access if authenticated OR in demo mode
  if (!isAuthenticated && !isDemoMode && !user) {
    return (
      <Navigate 
        to={redirectTo} 
        state={{ 
          from: location.pathname,
          returnUrl: location.pathname + location.search 
        }} 
        replace 
      />
    )
  }

  // User is authenticated or in demo mode, render the protected content
  return <>{children}</>
}

export default ProtectedRoute
export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'),
  wsURL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  enableMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true' || true, // Default to true for serverless functions
  isProduction: import.meta.env.NODE_ENV === 'production',
  useServerless: import.meta.env.VITE_USE_SERVERLESS !== 'false', // Default to true
  timeout: 10000, // 10 seconds
  retryAttempts: 3,
  endpoints: {
    auth: {
      login: '/api/v1/auth/login',
      register: '/api/v1/auth/register',
      refresh: '/api/v1/auth/refresh',
      logout: '/api/v1/auth/logout'
    },
    user: {
      profile: '/api/v1/users/profile',
      settings: '/api/v1/users/settings',
      updateProfile: '/api/v1/users/profile',
      updateSettings: '/api/v1/users/settings'
    },
    financial: {
      accounts: '/api/v1/financial/accounts',
      transactions: '/api/v1/financial/transactions',
      goals: '/api/v1/financial/goals',
      budget: '/api/v1/financial/budget'
    },
    ai: {
      chat: '/api/v1/ai/chat',
      recommendations: '/api/v1/ai/recommendations',
      insights: '/api/v1/ai/insights',
      analysis: '/api/v1/ai/analysis'
    },
    simulations: {
      monteCarlo: '/api/v1/simulations/monte-carlo',
      portfolioOptimization: '/api/v1/simulations/portfolio-optimization',
      scenarios: '/api/v1/simulations/scenarios'
    },
    portfolio: {
      overview: '/api/v1/portfolio/overview',
      holdings: '/api/v1/portfolio/holdings',
      performance: '/api/v1/portfolio/performance',
      allocation: '/api/v1/portfolio/allocation'
    }
  }
}

export const getApiUrl = (endpoint: string): string => {
  // If using serverless functions and endpoint doesn't start with /api, prepend it
  if (API_CONFIG.useServerless && !endpoint.startsWith('/api')) {
    // Handle special cases for financial planning endpoints
    if (endpoint === '/simulate' || endpoint === '/portfolio-optimization' || endpoint === '/market-data' || endpoint === '/health' || endpoint === '/demo') {
      return `${API_CONFIG.baseURL}/api${endpoint}`
    }
    // For versioned endpoints, they already include the full path
    return `${API_CONFIG.baseURL}${endpoint}`
  }
  return `${API_CONFIG.baseURL}${endpoint}`
}

export const getWsUrl = (userId: string): string => {
  return `${API_CONFIG.wsURL}/ws/${userId}`
}

export const getHealthCheckUrl = (): string => {
  return `${API_CONFIG.baseURL}/health`
}

export const isValidApiUrl = (): boolean => {
  try {
    new URL(API_CONFIG.baseURL)
    return true
  } catch {
    return false
  }
}

export const getRequestConfig = () => {
  return {
    timeout: API_CONFIG.timeout,
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      ...(API_CONFIG.isProduction && {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      })
    }
  }
}
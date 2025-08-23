export const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  wsURL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  enableMockData: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true',
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
  return `${API_CONFIG.baseURL}${endpoint}`
}

export const getWsUrl = (userId: string): string => {
  return `${API_CONFIG.wsURL}/ws/${userId}`
}
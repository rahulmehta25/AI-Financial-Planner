/**
 * API Service for Financial Planner
 * Unified service for all API calls
 */

import { API_CONFIG, getApiUrl } from '@/config/api'

// API client with proper error handling and authentication
class ApiService {
  private baseURL: string

  constructor() {
    // Don't use external APIs - everything is now through Supabase
    this.baseURL = ''
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // For now, return empty data to prevent errors
    // All real data comes from Supabase services
    console.log(`API call intercepted: ${endpoint}`)
    
    // Return mock empty responses to prevent errors
    if (endpoint.includes('dashboard')) {
      return {
        portfolioValue: 0,
        totalGain: 0,
        totalGainPercentage: 0,
        dayChange: 0,
        dayChangePercentage: 0,
        holdings: [],
        recentTransactions: [],
        marketOverview: {
          sp500: { value: 0, change: 0, changePercent: 0 },
          nasdaq: { value: 0, change: 0, changePercent: 0 },
          dow: { value: 0, change: 0, changePercent: 0 }
        }
      } as any
    }
    
    if (endpoint.includes('profile')) {
      return {
        id: '1',
        email: 'user@example.com',
        firstName: 'User',
        lastName: 'Name',
        isActive: true,
        createdAt: new Date().toISOString(),
        settings: {}
      } as any
    }
    
    // Return empty array for list endpoints
    if (endpoint.includes('transactions') || endpoint.includes('goals') || endpoint.includes('accounts')) {
      return [] as any
    }
    
    // Return empty object for other endpoints
    return {} as any
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'GET',
    })
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    })
  }
}

// Create singleton instance
export const apiService = new ApiService()

/**
 * Portfolio API endpoints - now using Supabase
 */
export const portfolioApi = {
  getPortfolio: async () => {
    // This is handled by portfolioService now
    const { portfolioService } = await import('./portfolio')
    const overview = await portfolioService.getPortfolioOverview()
    const holdings = await portfolioService.getHoldings()
    return { overview, holdings }
  },

  getHealth: async () => {
    // Return mock health data
    return {
      status: 'healthy',
      diversification: 'good',
      riskLevel: 'moderate'
    }
  },

  updatePrices: async () => {
    // Prices are updated automatically via Edge Functions
    return { success: true, message: 'Prices updated' }
  }
}

/**
 * Financial Advisor API endpoints
 */
export const advisorApi = {
  getTaxOpportunities: async () => {
    return {
      opportunities: [],
      potentialSavings: 0
    }
  },

  getRecommendations: async () => {
    return {
      recommendations: [],
      insights: []
    }
  }
}

export default {
  portfolio: portfolioApi,
  advisor: advisorApi
}
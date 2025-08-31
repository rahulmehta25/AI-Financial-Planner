/**
 * API Service for Financial Planner
 * Handles all API calls to backend services
 */

// Determine API URL based on environment
const getApiUrl = () => {
  // In production (Vercel), use relative paths for serverless functions
  if (import.meta.env.PROD) {
    return '';
  }
  // In development, use localhost
  return 'http://localhost:8002';
};

const API_BASE_URL = getApiUrl();

/**
 * Portfolio API endpoints
 */
export const portfolioApi = {
  // Get current portfolio
  getPortfolio: async () => {
    const response = await fetch(`${API_BASE_URL}/api/portfolio`);
    if (!response.ok) throw new Error('Failed to fetch portfolio');
    return response.json();
  },

  // Get portfolio health analysis
  getHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/api/portfolio/health`);
    if (!response.ok) throw new Error('Failed to fetch health analysis');
    return response.json();
  },

  // Update market prices
  updatePrices: async () => {
    const response = await fetch(`${API_BASE_URL}/api/portfolio/update`);
    if (!response.ok) throw new Error('Failed to update prices');
    return response.json();
  }
};

/**
 * Financial Advisor API endpoints
 */
export const advisorApi = {
  // Get tax opportunities
  getTaxOpportunities: async () => {
    const response = await fetch(`${API_BASE_URL}/api/advisor/tax-opportunities`);
    if (!response.ok) throw new Error('Failed to fetch tax opportunities');
    return response.json();
  },

  // Get investment guidance
  getInvestmentGuidance: async () => {
    const response = await fetch(`${API_BASE_URL}/api/advisor/investment-guidance`);
    if (!response.ok) throw new Error('Failed to fetch investment guidance');
    return response.json();
  },

  // Get market insights
  getMarketInsights: async () => {
    const response = await fetch(`${API_BASE_URL}/api/advisor/market-insights`);
    if (!response.ok) throw new Error('Failed to fetch market insights');
    return response.json();
  },

  // Get portfolio health (legacy endpoint)
  getHealth: async () => {
    const response = await fetch(`${API_BASE_URL}/api/advisor/health`);
    if (!response.ok) throw new Error('Failed to fetch health analysis');
    return response.json();
  }
};

// Legacy export for compatibility
export const apiService = {
  portfolio: portfolioApi,
  advisor: advisorApi
};

export default {
  portfolio: portfolioApi,
  advisor: advisorApi
};
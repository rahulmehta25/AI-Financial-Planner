import { apiService } from './api'

export interface FinancialProfile {
  age: number
  income: number
  savings: number
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive'
}

export interface SimulationResult {
  simulation_id: string
  result: {
    success_probability: number
    median_balance: number
    recommendation: string
  }
  message: string
}

export interface PortfolioAllocation {
  risk_tolerance: string
  recommended_allocation: {
    stocks: string
    bonds: string
    cash: string
    expected_return: string
    risk_level: string
  }
  disclaimer: string
}

export interface MarketData {
  asset_classes: Array<{
    name: string
    expected_return: string
    volatility: string
    sharpe_ratio: string
  }>
  last_updated: number
}

export class FinancialPlanningService {
  /**
   * Run a financial simulation
   */
  async runSimulation(profile: FinancialProfile): Promise<SimulationResult> {
    return apiService.post<SimulationResult>('/simulate', profile)
  }

  /**
   * Get portfolio optimization recommendations
   */
  async getPortfolioOptimization(riskTolerance: string): Promise<PortfolioAllocation> {
    return apiService.get<PortfolioAllocation>(`/portfolio-optimization?risk_tolerance=${riskTolerance}`)
  }

  /**
   * Get market data and asset analytics
   */
  async getMarketData(): Promise<MarketData> {
    return apiService.get<MarketData>('/market-data')
  }

  /**
   * Get demo information
   */
  async getDemoInfo(): Promise<any> {
    return apiService.get('/demo')
  }

  /**
   * Check backend health
   */
  async checkHealth(): Promise<any> {
    return apiService.get('/health')
  }

  /**
   * Get all available simulations
   */
  async getSimulations(): Promise<any> {
    return apiService.get('/simulations')
  }

  /**
   * Get a specific simulation by ID
   */
  async getSimulation(simulationId: string): Promise<any> {
    return apiService.get(`/simulations/${simulationId}`)
  }
}

export const financialPlanningService = new FinancialPlanningService()
export default financialPlanningService

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
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockSimulationResult(profile)
      }
      
      return await apiService.post<SimulationResult>('/simulate', profile)
    } catch (error) {
      console.error('Failed to run simulation, using mock calculations:', error)
      return this.getMockSimulationResult(profile)
    }
  }

  /**
   * Get portfolio optimization recommendations
   */
  async getPortfolioOptimization(riskTolerance: string): Promise<PortfolioAllocation> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockPortfolioOptimization(riskTolerance)
      }
      
      return await apiService.get<PortfolioAllocation>(`/portfolio-optimization?risk_tolerance=${riskTolerance}`)
    } catch (error) {
      console.error('Failed to get portfolio optimization, using mock data:', error)
      return this.getMockPortfolioOptimization(riskTolerance)
    }
  }

  /**
   * Get market data and asset analytics
   */
  async getMarketData(): Promise<MarketData> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockMarketData()
      }
      
      return await apiService.get<MarketData>('/market-data')
    } catch (error) {
      console.error('Failed to get market data, using mock data:', error)
      return this.getMockMarketData()
    }
  }

  /**
   * Get demo information
   */
  async getDemoInfo(): Promise<any> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockDemoInfo()
      }
      
      return await apiService.get('/demo')
    } catch (error) {
      console.error('Failed to get demo info, using mock data:', error)
      return this.getMockDemoInfo()
    }
  }

  /**
   * Check backend health
   */
  async checkHealth(): Promise<any> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return { status: 'mock', message: 'Backend unavailable - using mock data', timestamp: new Date().toISOString() }
      }
      
      return await apiService.get('/health')
    } catch (error) {
      console.error('Failed to check health, using mock response:', error)
      return { status: 'mock', message: 'Backend unavailable - using mock data', timestamp: new Date().toISOString(), error: error.message }
    }
  }

  /**
   * Get all available simulations
   */
  async getSimulations(): Promise<any> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockSimulations()
      }
      
      return await apiService.get('/simulations')
    } catch (error) {
      console.error('Failed to get simulations, using mock data:', error)
      return this.getMockSimulations()
    }
  }

  /**
   * Get a specific simulation by ID
   */
  async getSimulation(simulationId: string): Promise<any> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockSimulation(simulationId)
      }
      
      return await apiService.get(`/simulations/${simulationId}`)
    } catch (error) {
      console.error('Failed to get simulation, using mock data:', error)
      return this.getMockSimulation(simulationId)
    }
  }

  // Mock data methods
  private getMockSimulationResult(profile: FinancialProfile): SimulationResult {
    // Calculate mock results based on the profile
    const yearsToRetirement = 65 - profile.age
    const compoundGrowthRate = this.getRiskAdjustedReturn(profile.risk_tolerance)
    
    // Compound growth calculation
    const currentSavings = profile.savings
    const annualContribution = profile.income * 0.15 // Assume 15% savings rate
    
    // Future value of existing savings
    const futureValueCurrent = currentSavings * Math.pow(1 + compoundGrowthRate, yearsToRetirement)
    
    // Future value of annuity (annual contributions)
    const futureValueAnnuity = annualContribution * (Math.pow(1 + compoundGrowthRate, yearsToRetirement) - 1) / compoundGrowthRate
    
    const totalFutureValue = futureValueCurrent + futureValueAnnuity
    const retirementGoal = profile.income * 25 // 25x annual income rule
    
    const successProbability = Math.min(95, Math.max(15, (totalFutureValue / retirementGoal) * 80))
    
    let recommendation = ''
    if (successProbability >= 80) {
      recommendation = 'You are on track for a comfortable retirement! Consider optimizing your tax strategy and diversification.'
    } else if (successProbability >= 60) {
      recommendation = 'You are making good progress. Consider increasing your savings rate or extending your working years slightly.'
    } else {
      recommendation = 'Consider increasing your savings rate significantly, reducing expenses, or working a few additional years to meet your retirement goals.'
    }
    
    return {
      simulation_id: 'mock-simulation-' + Date.now(),
      result: {
        success_probability: Math.round(successProbability),
        median_balance: Math.round(totalFutureValue),
        recommendation
      },
      message: 'Simulation completed successfully (using mock calculations)'
    }
  }
  
  private getRiskAdjustedReturn(riskTolerance: 'conservative' | 'moderate' | 'aggressive'): number {
    const returns = {
      conservative: 0.05, // 5% annual return
      moderate: 0.07,     // 7% annual return
      aggressive: 0.09    // 9% annual return
    }
    return returns[riskTolerance] || 0.07
  }

  private getMockPortfolioOptimization(riskTolerance: string): PortfolioAllocation {
    const allocations = {
      conservative: {
        stocks: '30%',
        bonds: '60%',
        cash: '10%',
        expected_return: '5.2%',
        risk_level: 'Low'
      },
      moderate: {
        stocks: '60%',
        bonds: '35%',
        cash: '5%',
        expected_return: '7.1%',
        risk_level: 'Medium'
      },
      aggressive: {
        stocks: '85%',
        bonds: '10%',
        cash: '5%',
        expected_return: '9.3%',
        risk_level: 'High'
      }
    }
    
    const allocation = allocations[riskTolerance] || allocations['moderate']
    
    return {
      risk_tolerance: riskTolerance,
      recommended_allocation: allocation,
      disclaimer: 'This is a mock recommendation for demonstration purposes. Please consult with a financial advisor for personalized advice.'
    }
  }

  private getMockMarketData(): MarketData {
    return {
      asset_classes: [
        {
          name: 'US Stocks (Large Cap)',
          expected_return: '8.5%',
          volatility: '15.2%',
          sharpe_ratio: '0.56'
        },
        {
          name: 'International Stocks',
          expected_return: '7.8%',
          volatility: '16.8%',
          sharpe_ratio: '0.46'
        },
        {
          name: 'Emerging Markets',
          expected_return: '9.2%',
          volatility: '22.1%',
          sharpe_ratio: '0.42'
        },
        {
          name: 'Corporate Bonds',
          expected_return: '4.1%',
          volatility: '5.8%',
          sharpe_ratio: '0.71'
        },
        {
          name: 'Government Bonds',
          expected_return: '3.2%',
          volatility: '4.1%',
          sharpe_ratio: '0.78'
        },
        {
          name: 'REITs',
          expected_return: '6.9%',
          volatility: '19.3%',
          sharpe_ratio: '0.36'
        }
      ],
      last_updated: Date.now()
    }
  }

  private getMockDemoInfo(): any {
    return {
      mode: 'mock',
      message: 'This is a demonstration of the Financial Planning System with mock data',
      features: [
        'Portfolio tracking and analysis',
        'Financial goal planning',
        'AI-powered recommendations',
        'Risk assessment and optimization',
        'Retirement planning simulations'
      ],
      disclaimer: 'All data shown is simulated for demonstration purposes',
      backend_status: 'unavailable',
      using_mock_data: true
    }
  }

  private getMockSimulations(): any {
    return {
      simulations: [
        {
          id: 'mock-sim-1',
          name: 'Conservative Retirement Plan',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          success_probability: 78,
          median_balance: 850000
        },
        {
          id: 'mock-sim-2',
          name: 'Moderate Growth Strategy',
          created_at: new Date(Date.now() - 172800000).toISOString(),
          success_probability: 85,
          median_balance: 1200000
        },
        {
          id: 'mock-sim-3',
          name: 'Aggressive Accumulation',
          created_at: new Date(Date.now() - 259200000).toISOString(),
          success_probability: 92,
          median_balance: 1650000
        }
      ],
      total: 3,
      message: 'Mock simulation data'
    }
  }

  private getMockSimulation(simulationId: string): any {
    return {
      id: simulationId,
      name: 'Mock Simulation',
      profile: {
        age: 35,
        income: 75000,
        savings: 50000,
        risk_tolerance: 'moderate'
      },
      result: {
        success_probability: 85,
        median_balance: 1200000,
        recommendation: 'Your financial plan is on track. Consider maximizing your 401(k) contributions to take advantage of tax benefits.'
      },
      created_at: new Date().toISOString(),
      message: 'Mock simulation details'
    }
  }
}

export const financialPlanningService = new FinancialPlanningService()
export default financialPlanningService
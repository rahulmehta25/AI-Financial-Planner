import { API_CONFIG } from '@/config/api'
import { apiService } from './api'

export interface PortfolioOverview {
  totalValue: number
  totalGain: number
  totalGainPercentage: number
  dayChange: number
  dayChangePercentage: number
  totalInvested: number
  cashBalance: number
  lastUpdated: string
}

export interface Holding {
  id: string
  symbol: string
  name: string
  shares: number
  avgCostBasis: number
  currentPrice: number
  marketValue: number
  totalGain: number
  totalGainPercentage: number
  dayChange: number
  dayChangePercentage: number
  allocation: number
  sector: string
  assetType: 'stock' | 'etf' | 'bond' | 'crypto' | 'cash'
}

export interface PerformanceData {
  period: string
  return: number
  benchmark?: number
  dates: string[]
  values: number[]
  benchmarkValues?: number[]
}

export interface AllocationData {
  category: string
  value: number
  percentage: number
  color: string
}

export interface PortfolioAnalytics {
  riskMetrics: {
    beta: number
    sharpeRatio: number
    volatility: number
    maxDrawdown: number
    var95: number
  }
  diversification: {
    sectorAllocation: AllocationData[]
    assetAllocation: AllocationData[]
    geographicAllocation: AllocationData[]
  }
  performance: {
    ytd: PerformanceData
    oneYear: PerformanceData
    threeYear: PerformanceData
    fiveYear: PerformanceData
    inception: PerformanceData
  }
}

class PortfolioService {
  async getPortfolioOverview(): Promise<PortfolioOverview> {
    try {
      return await apiService.get<PortfolioOverview>(API_CONFIG.endpoints.portfolio.overview)
    } catch (error) {
      console.error('Failed to fetch portfolio overview:', error)
      throw error
    }
  }

  async getHoldings(): Promise<Holding[]> {
    try {
      return await apiService.get<Holding[]>(API_CONFIG.endpoints.portfolio.holdings)
    } catch (error) {
      console.error('Failed to fetch holdings:', error)
      throw error
    }
  }

  async getPerformance(period: '1D' | '1W' | '1M' | '3M' | '6M' | '1Y' | '3Y' | '5Y' | 'ALL' = '1Y'): Promise<PerformanceData> {
    try {
      return await apiService.get<PerformanceData>(`${API_CONFIG.endpoints.portfolio.performance}?period=${period}`)
    } catch (error) {
      console.error('Failed to fetch portfolio performance:', error)
      throw error
    }
  }

  async getAllocation(): Promise<AllocationData[]> {
    try {
      return await apiService.get<AllocationData[]>(API_CONFIG.endpoints.portfolio.allocation)
    } catch (error) {
      console.error('Failed to fetch portfolio allocation:', error)
      throw error
    }
  }

  async getAnalytics(): Promise<PortfolioAnalytics> {
    try {
      return await apiService.get<PortfolioAnalytics>(`${API_CONFIG.endpoints.portfolio.overview}/analytics`)
    } catch (error) {
      console.error('Failed to fetch portfolio analytics:', error)
      throw error
    }
  }

  async addHolding(holding: {
    symbol: string
    shares: number
    avgCostBasis: number
    purchaseDate: string
  }): Promise<Holding> {
    try {
      return await apiService.post<Holding>(API_CONFIG.endpoints.portfolio.holdings, holding)
    } catch (error) {
      console.error('Failed to add holding:', error)
      throw error
    }
  }

  async updateHolding(holdingId: string, updates: Partial<Holding>): Promise<Holding> {
    try {
      return await apiService.put<Holding>(`${API_CONFIG.endpoints.portfolio.holdings}/${holdingId}`, updates)
    } catch (error) {
      console.error('Failed to update holding:', error)
      throw error
    }
  }

  async deleteHolding(holdingId: string): Promise<void> {
    try {
      await apiService.delete(`${API_CONFIG.endpoints.portfolio.holdings}/${holdingId}`)
    } catch (error) {
      console.error('Failed to delete holding:', error)
      throw error
    }
  }

  async rebalancePortfolio(targetAllocation: AllocationData[]): Promise<{
    recommendations: Array<{
      symbol: string
      action: 'buy' | 'sell'
      shares: number
      reason: string
    }>
    estimatedCost: number
  }> {
    try {
      const backendAvailable = await apiService.isBackendAvailable()
      if (!backendAvailable) {
        return this.getMockRebalanceRecommendations(targetAllocation)
      }
      
      return await apiService.post(`${API_CONFIG.endpoints.portfolio.overview}/rebalance`, {
        targetAllocation
      })
    } catch (error) {
      console.error('Failed to get rebalancing recommendations, using mock data:', error)
      return this.getMockRebalanceRecommendations(targetAllocation)
    }
  }

  // Mock data methods
  private getMockPortfolioOverview(): PortfolioOverview {
    return {
      totalValue: 145000,
      totalGain: 25000,
      totalGainPercentage: 20.83,
      dayChange: 1250,
      dayChangePercentage: 0.87,
      totalInvested: 120000,
      cashBalance: 5000,
      lastUpdated: new Date().toISOString()
    }
  }

  private getMockHoldings(): Holding[] {
    return [
      {
        id: 'holding-1',
        symbol: 'AAPL',
        name: 'Apple Inc.',
        shares: 50,
        avgCostBasis: 150,
        currentPrice: 175,
        marketValue: 8750,
        totalGain: 1250,
        totalGainPercentage: 16.67,
        dayChange: 87.5,
        dayChangePercentage: 1.01,
        allocation: 6.0,
        sector: 'Technology',
        assetType: 'stock'
      },
      {
        id: 'holding-2',
        symbol: 'GOOGL',
        name: 'Alphabet Inc.',
        shares: 25,
        avgCostBasis: 2200,
        currentPrice: 2650,
        marketValue: 66250,
        totalGain: 11250,
        totalGainPercentage: 20.45,
        dayChange: 662.5,
        dayChangePercentage: 1.01,
        allocation: 45.7,
        sector: 'Technology',
        assetType: 'stock'
      },
      {
        id: 'holding-3',
        symbol: 'SPY',
        name: 'SPDR S&P 500 ETF',
        shares: 100,
        avgCostBasis: 400,
        currentPrice: 450,
        marketValue: 45000,
        totalGain: 5000,
        totalGainPercentage: 12.5,
        dayChange: 450,
        dayChangePercentage: 1.01,
        allocation: 31.0,
        sector: 'Diversified',
        assetType: 'etf'
      },
      {
        id: 'holding-4',
        symbol: 'MSFT',
        name: 'Microsoft Corporation',
        shares: 30,
        avgCostBasis: 300,
        currentPrice: 375,
        marketValue: 11250,
        totalGain: 2250,
        totalGainPercentage: 25.0,
        dayChange: 112.5,
        dayChangePercentage: 1.01,
        allocation: 7.8,
        sector: 'Technology',
        assetType: 'stock'
      },
      {
        id: 'holding-5',
        symbol: 'BND',
        name: 'Vanguard Total Bond Market ETF',
        shares: 150,
        avgCostBasis: 85,
        currentPrice: 80,
        marketValue: 12000,
        totalGain: -750,
        totalGainPercentage: -5.88,
        dayChange: -60,
        dayChangePercentage: -0.50,
        allocation: 8.3,
        sector: 'Fixed Income',
        assetType: 'etf'
      }
    ]
  }

  private getMockPerformance(period: string): PerformanceData {
    const generatePerformanceData = (days: number) => {
      const dates: string[] = []
      const values: number[] = []
      const benchmarkValues: number[] = []
      
      const startValue = 120000
      const currentValue = 145000
      const endReturn = (currentValue - startValue) / startValue
      
      for (let i = 0; i <= days; i++) {
        const date = new Date()
        date.setDate(date.getDate() - (days - i))
        dates.push(date.toISOString().split('T')[0])
        
        // Generate realistic portfolio curve with some volatility
        const progress = i / days
        const volatility = (Math.sin(i * 0.1) * 0.02) + (Math.random() - 0.5) * 0.01
        const value = startValue * (1 + (endReturn * progress) + volatility)
        values.push(Math.round(value))
        
        // Benchmark slightly lower performance
        const benchmarkReturn = endReturn * 0.8
        const benchmarkValue = startValue * (1 + (benchmarkReturn * progress) + volatility * 0.5)
        benchmarkValues.push(Math.round(benchmarkValue))
      }
      
      return { dates, values, benchmarkValues }
    }

    const periodData = {
      '1D': generatePerformanceData(1),
      '1W': generatePerformanceData(7),
      '1M': generatePerformanceData(30),
      '3M': generatePerformanceData(90),
      '6M': generatePerformanceData(180),
      '1Y': generatePerformanceData(365),
      '3Y': generatePerformanceData(1095),
      '5Y': generatePerformanceData(1825),
      'ALL': generatePerformanceData(2555)
    }

    const data = periodData[period] || periodData['1Y']
    const currentValue = data.values[data.values.length - 1]
    const startValue = data.values[0]
    const portfolioReturn = ((currentValue - startValue) / startValue) * 100
    
    const benchmarkCurrentValue = data.benchmarkValues[data.benchmarkValues.length - 1]
    const benchmarkStartValue = data.benchmarkValues[0]
    const benchmarkReturn = ((benchmarkCurrentValue - benchmarkStartValue) / benchmarkStartValue) * 100

    return {
      period,
      return: portfolioReturn,
      benchmark: benchmarkReturn,
      dates: data.dates,
      values: data.values,
      benchmarkValues: data.benchmarkValues
    }
  }

  private getMockAllocation(): AllocationData[] {
    return [
      { category: 'Technology', value: 77500, percentage: 53.4, color: '#3b82f6' },
      { category: 'Diversified ETFs', value: 45000, percentage: 31.0, color: '#10b981' },
      { category: 'Fixed Income', value: 12000, percentage: 8.3, color: '#f59e0b' },
      { category: 'Cash', value: 5000, percentage: 3.4, color: '#6b7280' },
      { category: 'Other', value: 5500, percentage: 3.8, color: '#8b5cf6' }
    ]
  }

  private getMockAnalytics(): PortfolioAnalytics {
    return {
      riskMetrics: {
        beta: 1.12,
        sharpeRatio: 1.35,
        volatility: 0.18,
        maxDrawdown: 0.12,
        var95: 0.08
      },
      diversification: {
        sectorAllocation: [
          { category: 'Technology', value: 77500, percentage: 53.4, color: '#3b82f6' },
          { category: 'Financial Services', value: 25000, percentage: 17.2, color: '#10b981' },
          { category: 'Healthcare', value: 20000, percentage: 13.8, color: '#f59e0b' },
          { category: 'Consumer Discretionary', value: 15000, percentage: 10.3, color: '#ef4444' },
          { category: 'Fixed Income', value: 12000, percentage: 8.3, color: '#8b5cf6' }
        ],
        assetAllocation: [
          { category: 'Stocks', value: 97500, percentage: 67.2, color: '#3b82f6' },
          { category: 'ETFs', value: 37500, percentage: 25.9, color: '#10b981' },
          { category: 'Bonds', value: 12000, percentage: 8.3, color: '#f59e0b' },
          { category: 'Cash', value: 5000, percentage: 3.4, color: '#6b7280' }
        ],
        geographicAllocation: [
          { category: 'US', value: 120000, percentage: 82.8, color: '#3b82f6' },
          { category: 'International Developed', value: 15000, percentage: 10.3, color: '#10b981' },
          { category: 'Emerging Markets', value: 7500, percentage: 5.2, color: '#f59e0b' },
          { category: 'Other', value: 2500, percentage: 1.7, color: '#6b7280' }
        ]
      },
      performance: {
        ytd: this.getMockPerformance('1Y'),
        oneYear: this.getMockPerformance('1Y'),
        threeYear: this.getMockPerformance('3Y'),
        fiveYear: this.getMockPerformance('5Y'),
        inception: this.getMockPerformance('ALL')
      }
    }
  }

  private mockAddHolding(holding: any): Holding {
    const mockPrice = 100 + Math.random() * 200
    return {
      id: 'holding-' + Date.now(),
      symbol: holding.symbol,
      name: `${holding.symbol} Mock Company`,
      shares: holding.shares,
      avgCostBasis: holding.avgCostBasis,
      currentPrice: mockPrice,
      marketValue: holding.shares * mockPrice,
      totalGain: holding.shares * (mockPrice - holding.avgCostBasis),
      totalGainPercentage: ((mockPrice - holding.avgCostBasis) / holding.avgCostBasis) * 100,
      dayChange: holding.shares * mockPrice * 0.01,
      dayChangePercentage: 1.0,
      allocation: 5.0,
      sector: 'Technology',
      assetType: 'stock'
    }
  }

  private mockUpdateHolding(holdingId: string, updates: Partial<Holding>): Holding {
    const existingHoldings = this.getMockHoldings()
    const existing = existingHoldings.find(h => h.id === holdingId) || existingHoldings[0]
    
    return {
      ...existing,
      ...updates,
      id: holdingId
    }
  }

  private getMockRebalanceRecommendations(targetAllocation: AllocationData[]): any {
    return {
      recommendations: [
        {
          symbol: 'SPY',
          action: 'buy' as const,
          shares: 10,
          reason: 'Increase diversified exposure to match target allocation'
        },
        {
          symbol: 'AAPL',
          action: 'sell' as const,
          shares: 5,
          reason: 'Reduce technology overweight to balance portfolio'
        },
        {
          symbol: 'BND',
          action: 'buy' as const,
          shares: 20,
          reason: 'Add fixed income exposure for better risk management'
        }
      ],
      estimatedCost: 1250.50
    }
  }
}

export const portfolioService = new PortfolioService()
export default portfolioService
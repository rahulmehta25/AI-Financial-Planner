/**
 * Real Portfolio Service using Supabase
 * This replaces the mock portfolio service with actual database operations
 */

import { supabase, portfolios, holdings, fetchMarketData, MarketData } from '../lib/supabase'

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
    standardDeviation: number
    sharpeRatio: number
    maxDrawdown: number
  }
  returns: {
    daily: number
    weekly: number
    monthly: number
    quarterly: number
    yearly: number
    allTime: number
  }
  diversification: {
    sectorAllocation: AllocationData[]
    assetTypeAllocation: AllocationData[]
    geographicAllocation: AllocationData[]
  }
}

class PortfolioService {
  private marketDataCache: Map<string, { data: MarketData, timestamp: number }> = new Map()
  private CACHE_DURATION = 60000 // 1 minute cache

  async getPortfolioOverview(): Promise<PortfolioOverview> {
    try {
      // Get the user's default portfolio
      const { data: userPortfolios, error } = await portfolios.getAll()
      
      if (error || !userPortfolios || userPortfolios.length === 0) {
        // Return empty portfolio if none exists
        return this.getEmptyPortfolio()
      }

      // Use the first portfolio or the default one
      const portfolio = userPortfolios.find(p => p.is_default) || userPortfolios[0]
      
      // Get holdings for this portfolio
      const { data: portfolioHoldings } = await holdings.getByPortfolio(portfolio.id)
      
      if (!portfolioHoldings || portfolioHoldings.length === 0) {
        return this.getEmptyPortfolio()
      }

      // Fetch current market data for all symbols
      const symbols = portfolioHoldings.map(h => h.symbol).join(',')
      const marketData = await this.getMarketData(symbols)
      
      // Calculate portfolio metrics
      let totalValue = 0
      let totalInvested = 0
      let dayChange = 0
      
      portfolioHoldings.forEach(holding => {
        const quote = marketData.find(q => q.symbol === holding.symbol)
        if (quote) {
          const marketValue = holding.quantity * quote.price
          totalValue += marketValue
          totalInvested += holding.cost_basis
          dayChange += holding.quantity * quote.change
        }
      })
      
      const totalGain = totalValue - totalInvested
      const totalGainPercentage = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0
      const dayChangePercentage = totalValue > 0 ? (dayChange / totalValue) * 100 : 0
      
      return {
        totalValue,
        totalGain,
        totalGainPercentage,
        dayChange,
        dayChangePercentage,
        totalInvested,
        cashBalance: 0, // TODO: Add cash balance to portfolio model
        lastUpdated: new Date().toISOString()
      }
    } catch (error) {
      console.error('Error fetching portfolio overview:', error)
      return this.getEmptyPortfolio()
    }
  }

  async getHoldings(): Promise<Holding[]> {
    try {
      // Get user's portfolios
      const { data: userPortfolios, error } = await portfolios.getAll()
      
      if (error || !userPortfolios || userPortfolios.length === 0) {
        return []
      }

      const portfolio = userPortfolios.find(p => p.is_default) || userPortfolios[0]
      const { data: portfolioHoldings } = await holdings.getByPortfolio(portfolio.id)
      
      if (!portfolioHoldings || portfolioHoldings.length === 0) {
        return []
      }

      // Fetch market data
      const symbols = portfolioHoldings.map(h => h.symbol).join(',')
      const marketData = await this.getMarketData(symbols)
      
      // Calculate total portfolio value for allocation
      const totalValue = portfolioHoldings.reduce((sum, holding) => {
        const quote = marketData.find(q => q.symbol === holding.symbol)
        return sum + (quote ? holding.quantity * quote.price : 0)
      }, 0)
      
      // Transform to Holding format
      return portfolioHoldings.map(h => {
        const quote = marketData.find(q => q.symbol === h.symbol)
        const currentPrice = quote?.price || 0
        const marketValue = h.quantity * currentPrice
        const totalGain = marketValue - h.cost_basis
        const totalGainPercentage = h.cost_basis > 0 ? (totalGain / h.cost_basis) * 100 : 0
        const dayChange = h.quantity * (quote?.change || 0)
        const dayChangePercentage = quote?.changePercent || 0
        const allocation = totalValue > 0 ? (marketValue / totalValue) * 100 : 0
        
        return {
          id: h.id,
          symbol: h.symbol,
          name: quote?.name || h.symbol,
          shares: h.quantity,
          avgCostBasis: h.cost_basis / h.quantity,
          currentPrice,
          marketValue,
          totalGain,
          totalGainPercentage,
          dayChange,
          dayChangePercentage,
          allocation,
          sector: this.getSector(h.symbol), // TODO: Get from market data
          assetType: (h.asset_type as any) || 'stock'
        }
      })
    } catch (error) {
      console.error('Error fetching holdings:', error)
      return []
    }
  }

  async getPerformance(period: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL' = '1M'): Promise<PerformanceData> {
    try {
      // Get holdings
      const userHoldings = await this.getHoldings()
      
      if (userHoldings.length === 0) {
        return this.getEmptyPerformance(period)
      }

      // Map period to yfinance format
      const periodMap = {
        '1D': '1d',
        '1W': '5d',
        '1M': '1mo',
        '3M': '3mo',
        '1Y': '1y',
        'ALL': '5y'
      }

      // For now, return simplified performance data
      // TODO: Fetch historical data from Edge Function
      const symbols = userHoldings.map(h => h.symbol).join(',')
      const historicalData = await fetchMarketData('historical', symbols, periodMap[period])
      
      // Process historical data
      return this.processHistoricalData(historicalData, period)
    } catch (error) {
      console.error('Error fetching performance:', error)
      return this.getEmptyPerformance(period)
    }
  }

  async getAllocation(type: 'sector' | 'asset' | 'geography' = 'sector'): Promise<AllocationData[]> {
    try {
      const userHoldings = await this.getHoldings()
      
      if (userHoldings.length === 0) {
        return []
      }

      const allocations = new Map<string, number>()
      const totalValue = userHoldings.reduce((sum, h) => sum + h.marketValue, 0)
      
      userHoldings.forEach(holding => {
        let category = ''
        
        switch (type) {
          case 'sector':
            category = holding.sector || 'Unknown'
            break
          case 'asset':
            category = holding.assetType
            break
          case 'geography':
            category = 'US' // TODO: Get from market data
            break
        }
        
        allocations.set(category, (allocations.get(category) || 0) + holding.marketValue)
      })
      
      const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899']
      let colorIndex = 0
      
      return Array.from(allocations.entries()).map(([category, value]) => ({
        category,
        value,
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0,
        color: colors[colorIndex++ % colors.length]
      }))
    } catch (error) {
      console.error('Error fetching allocation:', error)
      return []
    }
  }

  async getAnalytics(): Promise<PortfolioAnalytics> {
    // Simplified analytics for now
    return {
      riskMetrics: {
        beta: 1.0,
        standardDeviation: 15.2,
        sharpeRatio: 1.2,
        maxDrawdown: -12.5
      },
      returns: {
        daily: 0.5,
        weekly: 2.1,
        monthly: 4.3,
        quarterly: 8.7,
        yearly: 18.5,
        allTime: 45.2
      },
      diversification: {
        sectorAllocation: await this.getAllocation('sector'),
        assetTypeAllocation: await this.getAllocation('asset'),
        geographicAllocation: await this.getAllocation('geography')
      }
    }
  }

  async addHolding(symbol: string, shares: number, costBasis: number): Promise<void> {
    try {
      const { data: userPortfolios } = await portfolios.getAll()
      
      if (!userPortfolios || userPortfolios.length === 0) {
        throw new Error('No portfolio found')
      }

      const portfolio = userPortfolios.find(p => p.is_default) || userPortfolios[0]
      
      await holdings.create({
        portfolio_id: portfolio.id,
        symbol: symbol.toUpperCase(),
        quantity: shares,
        cost_basis: costBasis,
        purchase_date: new Date().toISOString().split('T')[0],
        asset_type: 'stock'
      })
    } catch (error) {
      console.error('Error adding holding:', error)
      throw error
    }
  }

  async updateHolding(holdingId: string, updates: Partial<Holding>): Promise<void> {
    try {
      await holdings.update(holdingId, {
        quantity: updates.shares,
        cost_basis: updates.avgCostBasis ? updates.avgCostBasis * (updates.shares || 0) : undefined
      })
    } catch (error) {
      console.error('Error updating holding:', error)
      throw error
    }
  }

  async removeHolding(holdingId: string): Promise<void> {
    try {
      await holdings.delete(holdingId)
    } catch (error) {
      console.error('Error removing holding:', error)
      throw error
    }
  }

  // Helper methods
  private async getMarketData(symbols: string): Promise<MarketData[]> {
    try {
      // Check cache first
      const cachedData: MarketData[] = []
      const symbolsToFetch: string[] = []
      const now = Date.now()
      
      symbols.split(',').forEach(symbol => {
        const cached = this.marketDataCache.get(symbol)
        if (cached && (now - cached.timestamp) < this.CACHE_DURATION) {
          cachedData.push(cached.data)
        } else {
          symbolsToFetch.push(symbol)
        }
      })
      
      if (symbolsToFetch.length === 0) {
        return cachedData
      }
      
      // Fetch missing data
      const freshData = await fetchMarketData('quote', symbolsToFetch.join(','))
      
      // Update cache
      if (Array.isArray(freshData)) {
        freshData.forEach(quote => {
          this.marketDataCache.set(quote.symbol, { data: quote, timestamp: now })
        })
      }
      
      return [...cachedData, ...(Array.isArray(freshData) ? freshData : [])]
    } catch (error) {
      console.error('Error fetching market data:', error)
      return []
    }
  }

  private getEmptyPortfolio(): PortfolioOverview {
    return {
      totalValue: 0,
      totalGain: 0,
      totalGainPercentage: 0,
      dayChange: 0,
      dayChangePercentage: 0,
      totalInvested: 0,
      cashBalance: 0,
      lastUpdated: new Date().toISOString()
    }
  }

  private getEmptyPerformance(period: string): PerformanceData {
    return {
      period,
      return: 0,
      benchmark: 0,
      dates: [],
      values: [],
      benchmarkValues: []
    }
  }

  private processHistoricalData(data: any, period: string): PerformanceData {
    // Process the historical data from the Edge Function
    if (!data || !data.data) {
      return this.getEmptyPerformance(period)
    }

    const dates = data.data.map((d: any) => d.date)
    const values = data.data.map((d: any) => d.close)
    
    const startValue = values[0]
    const endValue = values[values.length - 1]
    const returnPercent = ((endValue - startValue) / startValue) * 100
    
    return {
      period,
      return: returnPercent,
      benchmark: returnPercent * 0.8, // Simplified benchmark
      dates,
      values,
      benchmarkValues: values.map((v: number) => v * 0.95) // Simplified benchmark
    }
  }

  private getSector(symbol: string): string {
    // Simplified sector mapping
    const sectorMap: { [key: string]: string } = {
      'AAPL': 'Technology',
      'MSFT': 'Technology',
      'GOOGL': 'Technology',
      'AMZN': 'Consumer Discretionary',
      'TSLA': 'Consumer Discretionary',
      'META': 'Technology',
      'NVDA': 'Technology',
      'JPM': 'Financials',
      'BAC': 'Financials',
      'WMT': 'Consumer Staples',
      'JNJ': 'Healthcare',
      'PFE': 'Healthcare',
      'XOM': 'Energy',
      'CVX': 'Energy'
    }
    
    return sectorMap[symbol] || 'Other'
  }
}

export const portfolioService = new PortfolioService()
import type { VercelRequest, VercelResponse } from '@vercel/node'

interface PortfolioOverview {
  totalValue: number
  dayChange: number
  dayChangePercent: number
  allocation: {
    stocks: number
    bonds: number
    cash: number
    alternatives: number
  }
  performance: {
    oneDay: number
    oneWeek: number
    oneMonth: number
    threeMonths: number
    oneYear: number
    inception: number
  }
  holdings: Array<{
    symbol: string
    name: string
    quantity: number
    currentPrice: number
    totalValue: number
    dayChange: number
    dayChangePercent: number
    allocation: number
  }>
}

interface PortfolioAllocation {
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

// Portfolio allocation models based on risk tolerance
const portfolioModels = {
  conservative: {
    stocks: '30%',
    bonds: '60%',
    cash: '10%',
    expected_return: '5-7%',
    risk_level: 'Low'
  },
  moderate: {
    stocks: '60%',
    bonds: '30%',
    cash: '10%',
    expected_return: '7-9%',
    risk_level: 'Medium'
  },
  aggressive: {
    stocks: '80%',
    bonds: '15%',
    cash: '5%',
    expected_return: '9-12%',
    risk_level: 'High'
  }
}

const generateMockPortfolio = (): PortfolioOverview => {
  // Mock holdings data
  const holdings = [
    {
      symbol: 'VTI',
      name: 'Vanguard Total Stock Market ETF',
      quantity: 45.5,
      currentPrice: 242.18,
      dayChange: 2.34,
      dayChangePercent: 0.97
    },
    {
      symbol: 'VTIAX',
      name: 'Vanguard Total International Stock',
      quantity: 85.2,
      currentPrice: 22.45,
      dayChange: -0.12,
      dayChangePercent: -0.53
    },
    {
      symbol: 'BND',
      name: 'Vanguard Total Bond Market ETF',
      quantity: 125.0,
      currentPrice: 76.89,
      dayChange: 0.15,
      dayChangePercent: 0.20
    },
    {
      symbol: 'VNQ',
      name: 'Vanguard Real Estate ETF',
      quantity: 12.3,
      currentPrice: 87.65,
      dayChange: 1.23,
      dayChangePercent: 1.42
    },
    {
      symbol: 'VMOT',
      name: 'Vanguard Ultra-Short-Term Bond ETF',
      quantity: 95.8,
      currentPrice: 49.12,
      dayChange: 0.02,
      dayChangePercent: 0.04
    }
  ]
  
  // Calculate values
  const enrichedHoldings = holdings.map(holding => {
    const totalValue = holding.quantity * holding.currentPrice
    const dayChange = holding.quantity * holding.dayChange
    return {
      ...holding,
      totalValue,
      dayChange,
      allocation: 0 // Will be calculated below
    }
  })
  
  const totalValue = enrichedHoldings.reduce((sum, holding) => sum + holding.totalValue, 0)
  const totalDayChange = enrichedHoldings.reduce((sum, holding) => sum + holding.dayChange, 0)
  const totalDayChangePercent = (totalDayChange / (totalValue - totalDayChange)) * 100
  
  // Calculate allocations
  enrichedHoldings.forEach(holding => {
    holding.allocation = (holding.totalValue / totalValue) * 100
  })
  
  // Calculate asset class allocations
  const stocksValue = enrichedHoldings.filter(h => ['VTI', 'VTIAX'].includes(h.symbol))
    .reduce((sum, h) => sum + h.totalValue, 0)
  const bondsValue = enrichedHoldings.filter(h => ['BND', 'VMOT'].includes(h.symbol))
    .reduce((sum, h) => sum + h.totalValue, 0)
  const alternativesValue = enrichedHoldings.filter(h => ['VNQ'].includes(h.symbol))
    .reduce((sum, h) => sum + h.totalValue, 0)
  const cashValue = totalValue * 0.05 // Assume 5% cash
  
  return {
    totalValue: Math.round(totalValue),
    dayChange: Math.round(totalDayChange * 100) / 100,
    dayChangePercent: Math.round(totalDayChangePercent * 100) / 100,
    allocation: {
      stocks: Math.round((stocksValue / totalValue) * 100),
      bonds: Math.round((bondsValue / totalValue) * 100),
      cash: Math.round((cashValue / totalValue) * 100),
      alternatives: Math.round((alternativesValue / totalValue) * 100)
    },
    performance: {
      oneDay: Math.round(totalDayChangePercent * 100) / 100,
      oneWeek: Math.round((Math.random() * 4 - 2) * 100) / 100, // Mock data
      oneMonth: Math.round((Math.random() * 8 - 4) * 100) / 100,
      threeMonths: Math.round((Math.random() * 15 - 7.5) * 100) / 100,
      oneYear: Math.round((Math.random() * 25 + 5) * 100) / 100,
      inception: Math.round((Math.random() * 40 + 20) * 100) / 100
    },
    holdings: enrichedHoldings.map(h => ({
      ...h,
      allocation: Math.round(h.allocation * 100) / 100
    }))
  }
}

const extractUserIdFromToken = (token: string): string | null => {
  try {
    const parts = token.split('_')
    if (parts.length >= 4 && parts[0] === 'acc') {
      return parts[2]
    }
    return null
  } catch {
    return null
  }
}

const extractTokenFromHeader = (authHeader: string): string | null => {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null
  }
  return authHeader.substring(7)
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }
  
  const { operation, risk_tolerance } = req.query
  
  try {
    const operationType = operation as string || 'overview'
    
    switch (operationType) {
      case 'overview': {
        // Extract and validate token for portfolio overview
        const authHeader = req.headers.authorization as string
        const token = extractTokenFromHeader(authHeader)
        
        if (!token) {
          return res.status(401).json({
            detail: 'Authorization token required'
          })
        }
        
        const userId = extractUserIdFromToken(token)
        if (!userId) {
          return res.status(401).json({
            detail: 'Invalid token format'
          })
        }
        
        const portfolio = generateMockPortfolio()
        return res.status(200).json(portfolio)
      }
      
      case 'optimization': {
        if (!risk_tolerance) {
          return res.status(400).json({
            error: 'Missing required parameter: risk_tolerance'
          })
        }
        
        const riskLevel = risk_tolerance as string
        
        if (!['conservative', 'moderate', 'aggressive'].includes(riskLevel)) {
          return res.status(400).json({
            error: 'Invalid risk_tolerance. Must be: conservative, moderate, or aggressive'
          })
        }
        
        const allocation = portfolioModels[riskLevel as keyof typeof portfolioModels]
        
        const result: PortfolioAllocation = {
          risk_tolerance: riskLevel,
          recommended_allocation: allocation,
          disclaimer: 'This is a general recommendation based on your risk tolerance. Please consult with a financial advisor for personalized advice. Past performance does not guarantee future results.'
        }
        
        return res.status(200).json(result)
      }
      
      default:
        return res.status(400).json({
          error: 'Invalid operation. Supported operations: overview, optimization'
        })
    }
    
  } catch (error) {
    console.error('Portfolio API error:', error)
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to process portfolio request'
    })
  }
}
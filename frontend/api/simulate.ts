import type { VercelRequest, VercelResponse } from '@vercel/node'

interface FinancialProfile {
  age: number
  income: number
  savings: number
  risk_tolerance: 'conservative' | 'moderate' | 'aggressive'
}

interface SimulationResult {
  simulation_id: string
  result: {
    success_probability: number
    median_balance: number
    recommendation: string
  }
  message: string
}

// Mock Monte Carlo simulation logic
function runMonteCarloSimulation(profile: FinancialProfile): SimulationResult {
  const { age, income, savings, risk_tolerance } = profile
  
  // Risk multipliers
  const riskMultipliers = {
    conservative: { return: 0.06, volatility: 0.1 },
    moderate: { return: 0.08, volatility: 0.15 },
    aggressive: { return: 0.10, volatility: 0.20 }
  }
  
  const risk = riskMultipliers[risk_tolerance]
  const years = 65 - age // Assume retirement at 65
  const annualSavings = income * 0.15 // Assume 15% savings rate
  
  // Simple compound growth calculation with some randomness
  let projectedBalance = savings
  const simulations = 1000
  const results: number[] = []
  
  for (let i = 0; i < simulations; i++) {
    let balance = savings
    for (let year = 0; year < years; year++) {
      // Random return based on risk profile
      const randomReturn = risk.return + (Math.random() - 0.5) * risk.volatility * 2
      balance = balance * (1 + randomReturn) + annualSavings
    }
    results.push(balance)
  }
  
  results.sort((a, b) => a - b)
  const medianBalance = results[Math.floor(results.length / 2)]
  const successThreshold = income * 10 // 10x annual income for retirement
  const successfulSimulations = results.filter(r => r >= successThreshold).length
  const successProbability = (successfulSimulations / simulations) * 100
  
  // Generate recommendation based on results
  let recommendation = ''
  if (successProbability >= 80) {
    recommendation = `Excellent! You're on track for a comfortable retirement. Consider diversifying your investments or exploring tax-advantaged accounts.`
  } else if (successProbability >= 60) {
    recommendation = `Good progress, but consider increasing your savings rate by ${Math.ceil((80 - successProbability) / 10)}% or adjusting your risk tolerance.`
  } else {
    recommendation = `You may need to significantly increase your savings rate or consider working a few years longer. Consider consulting with a financial advisor.`
  }
  
  return {
    simulation_id: `sim_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    result: {
      success_probability: Math.round(successProbability),
      median_balance: Math.round(medianBalance),
      recommendation
    },
    message: `Simulation completed successfully. Based on ${simulations} scenarios over ${years} years.`
  }
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }
  
  try {
    const profile: FinancialProfile = req.body
    
    // Validate required fields
    if (!profile.age || !profile.income || !profile.savings || !profile.risk_tolerance) {
      return res.status(400).json({
        error: 'Missing required fields: age, income, savings, risk_tolerance'
      })
    }
    
    // Validate data types and ranges
    if (profile.age < 18 || profile.age > 100) {
      return res.status(400).json({ error: 'Age must be between 18 and 100' })
    }
    
    if (profile.income <= 0 || profile.savings < 0) {
      return res.status(400).json({ error: 'Income must be positive and savings cannot be negative' })
    }
    
    if (!['conservative', 'moderate', 'aggressive'].includes(profile.risk_tolerance)) {
      return res.status(400).json({ error: 'Risk tolerance must be conservative, moderate, or aggressive' })
    }
    
    const result = runMonteCarloSimulation(profile)
    
    res.status(200).json(result)
  } catch (error) {
    console.error('Simulation error:', error)
    res.status(500).json({ 
      error: 'Internal server error',
      message: 'Failed to run financial simulation'
    })
  }
}
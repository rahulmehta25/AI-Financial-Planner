import type { VercelRequest, VercelResponse } from '@vercel/node'

interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant' | 'system'
  timestamp: string
  metadata?: {
    sources?: string[]
    confidence?: number
    suggestions?: string[]
  }
}

interface ChatRequest {
  message: string
  sessionId?: string
  context?: {
    portfolioData?: any
    financialProfile?: any
    goals?: any[]
  }
}

interface ChatResponse {
  message: ChatMessage
  sessionId: string
  suggestions?: string[]
}

interface InsightResponse {
  insights: Array<{
    id: string
    type: 'spending' | 'saving' | 'investment' | 'risk' | 'goal'
    title: string
    description: string
    priority: 'low' | 'medium' | 'high'
    actionItems: string[]
    impact?: string
  }>
  summary: string
}

interface RecommendationResponse {
  recommendations: Array<{
    id: string
    category: 'portfolio' | 'savings' | 'debt' | 'insurance' | 'tax'
    title: string
    description: string
    reasoning: string
    priority: 'low' | 'medium' | 'high'
    timeframe: 'immediate' | 'short_term' | 'long_term'
    estimatedImpact?: string
  }>
  nextSteps: string[]
}

// Mock financial advice responses
const generateFinancialAdvice = (userMessage: string, context?: any): string => {
  const message = userMessage.toLowerCase()
  
  // Investment advice
  if (message.includes('invest') || message.includes('portfolio')) {
    return `Based on your query about investments, here are some key considerations:

1. **Diversification**: Spread your investments across different asset classes (stocks, bonds, real estate) to reduce risk.

2. **Risk Tolerance**: Your age and financial goals should guide your risk level. Generally, younger investors can take more risk.

3. **Time Horizon**: Long-term investments can weather market volatility better than short-term ones.

4. **Cost Management**: Look for low-fee index funds and ETFs to maximize your returns.

Would you like me to analyze your current portfolio or help you understand specific investment options?`
  }
  
  // Retirement planning
  if (message.includes('retirement') || message.includes('retire')) {
    return `Retirement planning is crucial for your financial future. Here's what you should consider:

1. **Start Early**: The power of compound interest means starting early can dramatically increase your retirement savings.

2. **401(k) Match**: Always contribute enough to get your full employer match - it's free money!

3. **Rule of Thumb**: Aim to save 10-15% of your income for retirement.

4. **Multiple Accounts**: Consider both traditional and Roth retirement accounts for tax diversification.

Based on our simulation tools, would you like me to run a retirement projection for you?`
  }
  
  // Budgeting and savings
  if (message.includes('budget') || message.includes('save') || message.includes('expense')) {
    return `Great question about budgeting! Here's a proven approach:

1. **50/30/20 Rule**: 50% needs, 30% wants, 20% savings and debt payments.

2. **Emergency Fund**: Build 3-6 months of expenses in a high-yield savings account.

3. **Track Everything**: Use apps or spreadsheets to monitor your spending patterns.

4. **Automate Savings**: Set up automatic transfers to make saving effortless.

Would you like help creating a personalized budget based on your income and expenses?`
  }
  
  // Default response
  return `I'm here to help with your financial planning questions! I can assist with:

• Investment and portfolio advice
• Retirement planning strategies  
• Budgeting and savings tips
• Debt management approaches
• Tax planning strategies
• Insurance considerations

What specific financial topic would you like to discuss? Feel free to ask about your current situation, and I can provide personalized guidance based on your goals and circumstances.`
}

const generateInsights = (): InsightResponse => {
  return {
    insights: [
      {
        id: 'insight_1',
        type: 'spending',
        title: 'High Discretionary Spending',
        description: 'Your entertainment and dining expenses have increased by 15% over the last 3 months.',
        priority: 'medium',
        actionItems: [
          'Set a monthly dining budget of $400',
          'Use the 24-hour rule before non-essential purchases',
          'Consider cooking at home more often'
        ],
        impact: 'Could save $200-300 monthly'
      },
      {
        id: 'insight_2',
        type: 'investment',
        title: 'Portfolio Concentration Risk',
        description: 'Your portfolio is heavily weighted in technology stocks (45% allocation).',
        priority: 'high',
        actionItems: [
          'Rebalance to reduce tech exposure to 25-30%',
          'Add more international diversification',
          'Consider adding bond allocation for stability'
        ],
        impact: 'Reduced volatility and better risk-adjusted returns'
      },
      {
        id: 'insight_3',
        type: 'saving',
        title: 'Emergency Fund Gap',
        description: 'Your emergency fund covers only 2 months of expenses. Recommended: 3-6 months.',
        priority: 'high',
        actionItems: [
          'Increase monthly emergency fund contributions by $300',
          'Move emergency funds to high-yield savings account',
          'Automate weekly transfers of $75'
        ],
        impact: 'Better financial security and peace of mind'
      }
    ],
    summary: 'Focus on building your emergency fund and rebalancing your portfolio for better diversification. Consider reducing discretionary spending to accelerate your financial goals.'
  }
}

const generateRecommendations = (riskProfile?: string): RecommendationResponse => {
  return {
    recommendations: [
      {
        id: 'rec_1',
        category: 'portfolio',
        title: 'Rebalance Investment Portfolio',
        description: 'Your current allocation is too aggressive for your stated risk tolerance.',
        reasoning: 'Based on your moderate risk tolerance, a 60/30/10 stock/bond/cash allocation would be more appropriate than your current 80/15/5 split.',
        priority: 'high',
        timeframe: 'immediate',
        estimatedImpact: 'Reduced portfolio volatility by 15-20%'
      },
      {
        id: 'rec_2',
        category: 'savings',
        title: 'Maximize 401(k) Employer Match',
        description: 'You\'re currently contributing 4% but your employer matches up to 6%.',
        reasoning: 'This is essentially free money - a 100% return on investment up to the match limit.',
        priority: 'high',
        timeframe: 'immediate',
        estimatedImpact: 'Additional $2,400 annually in retirement savings'
      },
      {
        id: 'rec_3',
        category: 'tax',
        title: 'Consider Roth IRA Conversion',
        description: 'Given your current tax bracket, a partial Roth conversion could be beneficial.',
        reasoning: 'You\'re in a relatively low tax bracket now, and converting some traditional IRA funds to Roth could save taxes in retirement.',
        priority: 'medium',
        timeframe: 'short_term',
        estimatedImpact: 'Potential tax savings of $10,000-15,000 over 20 years'
      },
      {
        id: 'rec_4',
        category: 'insurance',
        title: 'Review Life Insurance Coverage',
        description: 'Your current coverage may be insufficient given your recent salary increase.',
        reasoning: 'Rule of thumb is 10-12x annual salary in life insurance coverage for adequate family protection.',
        priority: 'medium',
        timeframe: 'short_term',
        estimatedImpact: 'Better financial protection for dependents'
      }
    ],
    nextSteps: [
      'Schedule a portfolio rebalancing within the next 2 weeks',
      'Contact HR to increase 401(k) contribution to 6%',
      'Research Roth IRA conversion opportunities for next tax year',
      'Get quotes for additional term life insurance coverage'
    ]
  }
}

// Simple session management (in production, you'd use a database)
const sessions: { [key: string]: ChatMessage[] } = {}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  const { operation } = req.query
  
  try {
    const operationType = operation as string || 'chat'
    
    switch (operationType) {
      case 'chat': {
        if (req.method === 'POST') {
          const { message, sessionId, context }: ChatRequest = req.body
          
          if (!message) {
            return res.status(400).json({ error: 'Message is required' })
          }
          
          const currentSessionId = sessionId || `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
          
          // Initialize session if it doesn't exist
          if (!sessions[currentSessionId]) {
            sessions[currentSessionId] = []
          }
          
          // Add user message to session
          const userMessage: ChatMessage = {
            id: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            content: message,
            role: 'user',
            timestamp: new Date().toISOString()
          }
          sessions[currentSessionId].push(userMessage)
          
          // Generate AI response
          const assistantResponse = generateFinancialAdvice(message, context)
          const assistantMessage: ChatMessage = {
            id: `msg_${Date.now() + 1}_${Math.random().toString(36).substr(2, 9)}`,
            content: assistantResponse,
            role: 'assistant',
            timestamp: new Date().toISOString(),
            metadata: {
              confidence: 0.85,
              suggestions: [
                "Would you like to run a financial simulation?",
                "Should we analyze your portfolio allocation?",
                "Do you want to set up a savings goal?"
              ]
            }
          }
          sessions[currentSessionId].push(assistantMessage)
          
          const response: ChatResponse = {
            message: assistantMessage,
            sessionId: currentSessionId,
            suggestions: assistantMessage.metadata?.suggestions
          }
          
          return res.status(200).json(response)
          
        } else if (req.method === 'GET') {
          // Handle chat session retrieval
          const { sessionId } = req.query
          
          if (sessionId) {
            // Get specific session
            const sessionMessages = sessions[sessionId as string] || []
            return res.status(200).json({
              id: sessionId,
              title: `Chat Session`,
              messages: sessionMessages,
              createdAt: sessionMessages[0]?.timestamp || new Date().toISOString(),
              updatedAt: sessionMessages[sessionMessages.length - 1]?.timestamp || new Date().toISOString(),
              userId: 'demo_user'
            })
          } else {
            // Get all sessions
            const allSessions = Object.keys(sessions).map(id => ({
              id,
              title: `Chat Session ${id.split('_')[1]}`,
              messages: sessions[id],
              createdAt: sessions[id][0]?.timestamp || new Date().toISOString(),
              updatedAt: sessions[id][sessions[id].length - 1]?.timestamp || new Date().toISOString(),
              userId: 'demo_user'
            }))
            return res.status(200).json(allSessions)
          }
        } else {
          return res.status(405).json({ error: 'Method not allowed for chat operation' })
        }
      }
      
      case 'insights': {
        if (req.method !== 'GET') {
          return res.status(405).json({ error: 'Method not allowed for insights operation' })
        }
        
        const insights = generateInsights()
        return res.status(200).json(insights)
      }
      
      case 'recommendations': {
        if (req.method !== 'GET') {
          return res.status(405).json({ error: 'Method not allowed for recommendations operation' })
        }
        
        const { risk_profile } = req.query
        const recommendations = generateRecommendations(risk_profile as string)
        return res.status(200).json(recommendations)
      }
      
      default:
        return res.status(400).json({
          error: 'Invalid operation. Supported operations: chat, insights, recommendations'
        })
    }
    
  } catch (error) {
    console.error('AI API error:', error)
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to process AI request'
    })
  }
}
import { API_CONFIG } from '@/config/api'
import { apiService } from './api'
import { supabase } from '@/lib/supabase'

export interface ChatMessage {
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

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
  userId: string
}

export interface ChatRequest {
  message: string
  sessionId?: string
  context?: {
    portfolioData?: any
    financialProfile?: any
    goals?: any[]
  }
}

export interface ChatResponse {
  message: ChatMessage
  sessionId: string
  suggestions?: string[]
}

export interface AIRecommendation {
  id: string
  type: 'portfolio_rebalance' | 'savings_optimization' | 'risk_adjustment' | 'goal_update' | 'tax_strategy'
  title: string
  description: string
  impact: 'low' | 'medium' | 'high'
  confidence: number
  actionable: boolean
  estimatedBenefit?: string
  timeframe?: string
  details: {
    currentState: any
    recommendedAction: any
    reasoning: string
    risks: string[]
    prerequisites: string[]
  }
  createdAt: string
}

export interface AIInsights {
  spending_patterns: {
    trends: Array<{
      category: string
      change: number
      timeframe: string
    }>
    recommendations: string[]
  }
  portfolio_analysis: {
    performance_summary: string
    risk_assessment: string
    diversification_score: number
    recommendations: string[]
  }
  goal_progress: {
    on_track_goals: number
    at_risk_goals: number
    recommendations: string[]
  }
  market_context: {
    relevant_updates: string[]
    potential_impacts: string[]
  }
}

class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      // Try to use Supabase Edge Function if available
      const { data: edgeResponse, error: edgeError } = await supabase.functions.invoke('ai-chat', {
        body: { message: request.message, context: request.context }
      })

      if (!edgeError && edgeResponse) {
        return {
          message: {
            id: crypto.randomUUID(),
            content: edgeResponse.message || edgeResponse.response || 'I can help you with your financial planning needs.',
            role: 'assistant',
            timestamp: new Date().toISOString(),
            metadata: {
              suggestions: edgeResponse.suggestions
            }
          },
          sessionId: request.sessionId || crypto.randomUUID(),
          suggestions: edgeResponse.suggestions
        }
      }

      // Fallback to mock AI responses
      const responses = [
        'Based on your portfolio, I recommend diversifying into international markets to reduce concentration risk.',
        'Your current allocation looks good, but consider increasing your emergency fund to cover 6 months of expenses.',
        'Given your risk tolerance, you might want to consider adding some bonds to your portfolio for stability.',
        'I notice you have significant tech exposure. Consider rebalancing to maintain your target allocation.',
        'Your investment strategy aligns well with your long-term goals. Keep up the consistent contributions!'
      ]

      const suggestions = [
        'Review your portfolio allocation',
        'Check your risk tolerance',
        'Analyze your investment goals',
        'Explore tax-efficient strategies'
      ]

      const randomResponse = responses[Math.floor(Math.random() * responses.length)]

      return {
        message: {
          id: crypto.randomUUID(),
          content: randomResponse,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          metadata: {
            confidence: 0.85,
            suggestions
          }
        },
        sessionId: request.sessionId || crypto.randomUUID(),
        suggestions
      }
    } catch (error) {
      console.error('Failed to send chat message:', error)
      // Return a helpful fallback message
      return {
        message: {
          id: crypto.randomUUID(),
          content: 'I can help you with portfolio analysis, investment strategies, and financial planning. What would you like to know?',
          role: 'assistant',
          timestamp: new Date().toISOString()
        },
        sessionId: request.sessionId || crypto.randomUUID()
      }
    }
  }

  async getChatSessions(): Promise<ChatSession[]> {
    try {
      return await apiService.get<ChatSession[]>(`${API_CONFIG.endpoints.ai.chat}/sessions`)
    } catch (error) {
      console.error('Failed to fetch chat sessions:', error)
      throw error
    }
  }

  async getChatSession(sessionId: string): Promise<ChatSession> {
    try {
      return await apiService.get<ChatSession>(`${API_CONFIG.endpoints.ai.chat}/sessions/${sessionId}`)
    } catch (error) {
      console.error('Failed to fetch chat session:', error)
      throw error
    }
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    try {
      return await apiService.post<ChatSession>(`${API_CONFIG.endpoints.ai.chat}/sessions`, {
        title: title || `Chat ${new Date().toLocaleDateString()}`
      })
    } catch (error) {
      console.error('Failed to create chat session:', error)
      throw error
    }
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    try {
      await apiService.delete(`${API_CONFIG.endpoints.ai.chat}/sessions/${sessionId}`)
    } catch (error) {
      console.error('Failed to delete chat session:', error)
      throw error
    }
  }

  async getRecommendations(): Promise<AIRecommendation[]> {
    try {
      return await apiService.get<AIRecommendation[]>(API_CONFIG.endpoints.ai.recommendations)
    } catch (error) {
      console.error('Failed to fetch recommendations:', error)
      throw error
    }
  }

  async getInsights(): Promise<AIInsights> {
    try {
      return await apiService.get<AIInsights>(API_CONFIG.endpoints.ai.insights)
    } catch (error) {
      console.error('Failed to fetch insights:', error)
      throw error
    }
  }

  async analyzePortfolio(): Promise<{
    summary: string
    recommendations: string[]
    riskAssessment: string
    optimizationSuggestions: string[]
  }> {
    try {
      return await apiService.post(API_CONFIG.endpoints.ai.analysis, {
        type: 'portfolio'
      })
    } catch (error) {
      console.error('Failed to analyze portfolio:', error)
      throw error
    }
  }

  async analyzeGoals(): Promise<{
    summary: string
    recommendations: string[]
    progressAssessment: string
    adjustmentSuggestions: string[]
  }> {
    try {
      return await apiService.post(API_CONFIG.endpoints.ai.analysis, {
        type: 'goals'
      })
    } catch (error) {
      console.error('Failed to analyze goals:', error)
      throw error
    }
  }

  async analyzeSpending(): Promise<{
    summary: string
    patterns: Array<{
      category: string
      trend: 'increasing' | 'decreasing' | 'stable'
      amount: number
      suggestions: string[]
    }>
    budgetRecommendations: string[]
    savingsOpportunities: string[]
  }> {
    try {
      return await apiService.post(API_CONFIG.endpoints.ai.analysis, {
        type: 'spending'
      })
    } catch (error) {
      console.error('Failed to analyze spending:', error)
      throw error
    }
  }

  // WebSocket connection for real-time chat (if supported)
  connectToChat(sessionId: string, onMessage: (message: ChatMessage) => void): WebSocket | null {
    try {
      const wsUrl = `${API_CONFIG.wsURL}/ws/chat/${sessionId}`
      const ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as ChatMessage
          onMessage(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }

      return ws
    } catch (error) {
      console.error('Failed to connect to chat WebSocket:', error)
      return null
    }
  }

  // Mock data methods
  private getMockChatResponse(request: ChatRequest): ChatResponse {
    const responses = this.getSmartResponses(request.message)
    const response = responses[Math.floor(Math.random() * responses.length)]
    
    const message: ChatMessage = {
      id: 'msg-' + Date.now(),
      content: response,
      role: 'assistant',
      timestamp: new Date().toISOString(),
      metadata: {
        sources: ['Mock Financial AI'],
        confidence: 0.85,
        suggestions: [
          'Tell me about portfolio optimization',
          'How can I plan for retirement?',
          'What are good investment strategies?'
        ]
      }
    }

    return {
      message,
      sessionId: request.sessionId || 'mock-session-' + Date.now(),
      suggestions: message.metadata?.suggestions
    }
  }

  private getSmartResponses(userMessage: string): string[] {
    const message = userMessage.toLowerCase()
    
    if (message.includes('retirement') || message.includes('retire')) {
      return [
        'For retirement planning, I recommend following the 4% withdrawal rule and diversifying your investments across stocks, bonds, and other assets. Based on typical scenarios, you should aim to save 10-15% of your income consistently.',
        'Retirement planning depends on your age, current savings, and lifestyle goals. Generally, you\'ll want to maximize tax-advantaged accounts like 401(k)s and IRAs, and consider target-date funds for automatic diversification.',
        'A good retirement strategy includes: 1) Start early to benefit from compound interest, 2) Maximize employer 401(k) matching, 3) Diversify investments based on your risk tolerance, 4) Review and adjust your plan annually.'
      ]
    }
    
    if (message.includes('portfolio') || message.includes('investment') || message.includes('stock')) {
      return [
        'For portfolio optimization, consider diversifying across asset classes. A common approach is the age-based allocation: subtract your age from 100 to determine your stock percentage. The remainder goes to bonds and other conservative investments.',
        'Your portfolio should reflect your risk tolerance and time horizon. Young investors can typically handle more volatility with higher stock allocations, while those nearing retirement should prioritize capital preservation.',
        'Key portfolio principles: 1) Diversification reduces risk, 2) Low-cost index funds often outperform active management, 3) Regular rebalancing maintains your target allocation, 4) Dollar-cost averaging can reduce timing risk.'
      ]
    }
    
    if (message.includes('budget') || message.includes('spending') || message.includes('expense')) {
      return [
        'Effective budgeting starts with the 50/30/20 rule: 50% for needs, 30% for wants, and 20% for savings and debt repayment. Track your expenses to identify areas for optimization.',
        'To improve your budget: 1) List all income and expenses, 2) Categorize spending as needs vs wants, 3) Look for recurring subscriptions you don\'t use, 4) Set up automatic transfers to savings.',
        'Consider using budgeting apps to track spending automatically. Focus on reducing high-impact expenses like housing, transportation, and food while maintaining your quality of life.'
      ]
    }
    
    if (message.includes('debt') || message.includes('loan') || message.includes('credit')) {
      return [
        'For debt management, prioritize high-interest debt first (avalanche method) or start with smallest balances for psychological wins (snowball method). Consider debt consolidation if it lowers your overall interest rate.',
        'Debt reduction strategies: 1) List all debts with interest rates, 2) Pay minimums on all debts, 3) Put extra money toward the highest-rate debt, 4) Consider balance transfers for credit card debt.',
        'Good debt (mortgages, education loans) can build wealth over time, while bad debt (credit cards, personal loans) should be eliminated quickly. Aim to keep total debt payments under 36% of your income.'
      ]
    }
    
    if (message.includes('risk') || message.includes('tolerance')) {
      return [
        'Risk tolerance depends on your age, financial goals, and comfort with volatility. Generally, younger investors can take more risk for potentially higher returns, while older investors should focus on capital preservation.',
        'To assess your risk tolerance, consider: 1) Your investment timeline, 2) How you\'d react to a 20% portfolio drop, 3) Your need for current income vs. growth, 4) Your overall financial stability.',
        'Conservative investors might prefer 30% stocks/70% bonds, moderate investors often choose 60%/40%, while aggressive investors might go 80%/20% or higher in stocks.'
      ]
    }
    
    // Default responses for general financial questions
    return [
      'I\'m here to help with your financial planning questions! I can assist with retirement planning, investment strategies, budgeting, debt management, and more. What specific area would you like to explore?',
      'Financial planning is a journey, and I\'m here to guide you. Whether you\'re looking to optimize your portfolio, plan for retirement, or manage your budget, I can provide personalized advice based on your situation.',
      'Great question! Financial success comes from consistent habits: saving regularly, investing wisely, managing risk, and staying informed. What aspect of your financial life would you like to improve first?',
      'Every financial situation is unique, but some universal principles apply: spend less than you earn, invest for the long term, diversify your investments, and review your plan regularly. How can I help you implement these strategies?'
    ]
  }

  private getMockChatSessions(): ChatSession[] {
    return [
      {
        id: 'session-1',
        title: 'Retirement Planning Discussion',
        messages: [
          {
            id: 'msg-1',
            content: 'How should I plan for retirement at age 30?',
            role: 'user',
            timestamp: new Date(Date.now() - 3600000).toISOString()
          },
          {
            id: 'msg-2',
            content: 'Starting retirement planning at 30 is excellent! I recommend maximizing your 401(k) contributions, especially to get full employer matching. Consider target-date funds for automatic diversification.',
            role: 'assistant',
            timestamp: new Date(Date.now() - 3500000).toISOString()
          }
        ],
        createdAt: new Date(Date.now() - 86400000).toISOString(),
        updatedAt: new Date(Date.now() - 3500000).toISOString(),
        userId: 'mock-user-123'
      },
      {
        id: 'session-2',
        title: 'Portfolio Optimization',
        messages: [
          {
            id: 'msg-3',
            content: 'How can I optimize my investment portfolio?',
            role: 'user',
            timestamp: new Date(Date.now() - 7200000).toISOString()
          },
          {
            id: 'msg-4',
            content: 'Portfolio optimization starts with proper asset allocation based on your risk tolerance and time horizon. Consider diversifying across stocks, bonds, and other asset classes.',
            role: 'assistant',
            timestamp: new Date(Date.now() - 7000000).toISOString()
          }
        ],
        createdAt: new Date(Date.now() - 172800000).toISOString(),
        updatedAt: new Date(Date.now() - 7000000).toISOString(),
        userId: 'mock-user-123'
      }
    ]
  }

  private getMockChatSession(sessionId: string): ChatSession {
    const sessions = this.getMockChatSessions()
    return sessions.find(s => s.id === sessionId) || sessions[0]
  }

  private createMockChatSession(title?: string): ChatSession {
    return {
      id: 'session-' + Date.now(),
      title: title || `Chat ${new Date().toLocaleDateString()}`,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      userId: 'mock-user-123'
    }
  }

  private getMockRecommendations(): AIRecommendation[] {
    return [
      {
        id: 'rec-1',
        type: 'portfolio_rebalance',
        title: 'Rebalance Your Portfolio',
        description: 'Your stock allocation has grown to 75% due to market gains. Consider rebalancing to your target 60/40 allocation.',
        impact: 'medium',
        confidence: 0.85,
        actionable: true,
        estimatedBenefit: '$2,400 in reduced risk',
        timeframe: '1-2 weeks',
        details: {
          currentState: { stocks: '75%', bonds: '25%' },
          recommendedAction: { stocks: '60%', bonds: '40%' },
          reasoning: 'Market gains have shifted your allocation away from your target. Rebalancing maintains your desired risk level.',
          risks: ['Market timing risk', 'Transaction costs'],
          prerequisites: ['Review tax implications', 'Consider dollar-cost averaging for large adjustments']
        },
        createdAt: new Date().toISOString()
      },
      {
        id: 'rec-2',
        type: 'savings_optimization',
        title: 'Increase 401(k) Contribution',
        description: 'You\'re not maximizing your employer match. Increase contributions to get the full $3,000 annual match.',
        impact: 'high',
        confidence: 0.95,
        actionable: true,
        estimatedBenefit: '$3,000 free money annually',
        timeframe: 'Next payroll cycle',
        details: {
          currentState: { contribution: '3%', match: '50% lost' },
          recommendedAction: { contribution: '6%', match: '100% captured' },
          reasoning: 'Employer matching is guaranteed 100% return on investment up to the match limit.',
          risks: ['Reduced take-home pay'],
          prerequisites: ['Update payroll deductions', 'Adjust budget if needed']
        },
        createdAt: new Date(Date.now() - 86400000).toISOString()
      },
      {
        id: 'rec-3',
        type: 'tax_strategy',
        title: 'Open a Roth IRA',
        description: 'Based on your income and tax bracket, a Roth IRA could provide significant tax-free growth for retirement.',
        impact: 'high',
        confidence: 0.78,
        actionable: true,
        estimatedBenefit: '$15,000+ in tax savings over 30 years',
        timeframe: '2-3 weeks',
        details: {
          currentState: { rothIRA: 'none', taxAdvantage: 'limited' },
          recommendedAction: { rothIRA: '$6,000 annual', taxAdvantage: 'maximized' },
          reasoning: 'Your current tax bracket makes Roth contributions very attractive for long-term growth.',
          risks: ['Contribution limits', 'Income phase-out limits'],
          prerequisites: ['Verify income eligibility', 'Choose investment provider', 'Set up automatic contributions']
        },
        createdAt: new Date(Date.now() - 172800000).toISOString()
      }
    ]
  }

  private getMockInsights(): AIInsights {
    return {
      spending_patterns: {
        trends: [
          { category: 'Dining Out', change: 15, timeframe: 'last 3 months' },
          { category: 'Transportation', change: -8, timeframe: 'last 3 months' },
          { category: 'Entertainment', change: 22, timeframe: 'last 3 months' },
          { category: 'Utilities', change: 5, timeframe: 'last 3 months' }
        ],
        recommendations: [
          'Consider cooking more meals at home to reduce dining expenses',
          'Review streaming subscriptions and cancel unused services',
          'Take advantage of lower transportation costs to boost savings'
        ]
      },
      portfolio_analysis: {
        performance_summary: 'Your portfolio has returned 12.3% over the past year, outperforming the S&P 500 by 1.8%.',
        risk_assessment: 'Current risk level is moderate with a beta of 1.12. Volatility is within expected range for your allocation.',
        diversification_score: 85,
        recommendations: [
          'Consider adding international exposure for better diversification',
          'Your tech allocation is high - consider rebalancing to other sectors',
          'Bond duration could be reduced given current interest rate environment'
        ]
      },
      goal_progress: {
        on_track_goals: 2,
        at_risk_goals: 1,
        recommendations: [
          'Increase emergency fund contributions by $200/month to reach 6-month target',
          'Retirement savings are on track - maintain current contribution rate',
          'Consider accelerating house down payment savings with high-yield account'
        ]
      },
      market_context: {
        relevant_updates: [
          'Fed interest rate decision upcoming - may impact bond prices',
          'Tech earnings season showing mixed results',
          'Inflation data suggests continued moderation'
        ],
        potential_impacts: [
          'Rising rates could benefit new bond purchases',
          'Value stocks may outperform growth in current environment',
          'Consider tax-loss harvesting opportunities before year-end'
        ]
      }
    }
  }

  private getMockPortfolioAnalysis() {
    return {
      summary: 'Your portfolio shows strong performance with 12.3% annual returns. Asset allocation is slightly overweight in technology stocks but overall diversification is good.',
      recommendations: [
        'Rebalance to reduce technology overweight from 35% to target 25%',
        'Add international exposure to improve diversification',
        'Consider tax-loss harvesting in underperforming positions'
      ],
      riskAssessment: 'Current risk level is appropriate for your age and goals. Beta of 1.12 indicates slightly higher volatility than market average.',
      optimizationSuggestions: [
        'Reduce expense ratios by switching to lower-cost index funds',
        'Implement tax-efficient fund placement across account types',
        'Consider adding REITs for inflation protection and diversification'
      ]
    }
  }

  private getMockGoalsAnalysis() {
    return {
      summary: 'You have 3 financial goals tracked. Two are on track while your emergency fund needs attention.',
      recommendations: [
        'Increase emergency fund contributions by $200/month',
        'Consider automatic transfers to reach goals consistently',
        'Set up milestone celebrations to maintain motivation'
      ],
      progressAssessment: 'Retirement: 95% on track, House Down Payment: 85% on track, Emergency Fund: 60% on track',
      adjustmentSuggestions: [
        'Redirect dining out savings toward emergency fund',
        'Consider side income to accelerate goal achievement',
        'Review and update goal timelines based on life changes'
      ]
    }
  }

  private getMockSpendingAnalysis() {
    return {
      summary: 'Your spending has increased 8% over the last quarter, primarily driven by dining and entertainment expenses.',
      patterns: [
        {
          category: 'Dining Out',
          trend: 'increasing' as const,
          amount: 450,
          suggestions: ['Try meal planning and batch cooking', 'Set a monthly dining budget limit']
        },
        {
          category: 'Transportation',
          trend: 'decreasing' as const,
          amount: 320,
          suggestions: ['Great work reducing transport costs', 'Consider investing savings']
        },
        {
          category: 'Entertainment',
          trend: 'increasing' as const,
          amount: 280,
          suggestions: ['Review streaming subscriptions', 'Look for free local activities']
        },
        {
          category: 'Utilities',
          trend: 'stable' as const,
          amount: 180,
          suggestions: ['Consider energy-efficient upgrades', 'Monitor seasonal variations']
        }
      ],
      budgetRecommendations: [
        'Set specific limits for discretionary categories',
        'Use the 50/30/20 budgeting rule as a framework',
        'Track spending weekly to stay aware of patterns'
      ],
      savingsOpportunities: [
        'Reduce dining out by $150/month through meal planning',
        'Cancel unused subscriptions for $45/month savings',
        'Negotiate lower insurance premiums for potential $30/month savings'
      ]
    }
  }
}

export const chatService = new ChatService()
export default chatService
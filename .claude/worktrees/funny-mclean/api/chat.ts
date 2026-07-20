import type { VercelRequest, VercelResponse } from '@vercel/node'

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface RequestBody {
  message: string
  history?: ChatMessage[]
  context?: {
    portfolioData?: unknown
    financialProfile?: unknown
    goals?: unknown[]
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*')
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  const apiKey = process.env.ANTHROPIC_API_KEY
  if (!apiKey) {
    return res.status(503).json({
      error: 'AI service not configured',
      message: 'Please configure ANTHROPIC_API_KEY in your environment variables to enable the AI advisor.',
    })
  }

  const { message, history = [], context } = req.body as RequestBody

  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    return res.status(400).json({ error: 'Message is required' })
  }

  // Build system prompt with financial context
  const systemPrompt = buildSystemPrompt(context)

  // Convert history to Anthropic message format
  const messages: ChatMessage[] = [
    ...history.slice(-10), // Keep last 10 messages for context
    { role: 'user', content: message.trim() },
  ]

  try {
    const response = await fetch(ANTHROPIC_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 1024,
        system: systemPrompt,
        messages,
      }),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('Anthropic API error:', response.status, errorData)
      return res.status(502).json({
        error: 'AI service temporarily unavailable',
        message: 'The AI advisor is experiencing issues. Please try again shortly.',
      })
    }

    const data = await response.json()
    const assistantMessage = data.content?.[0]?.text || 'I was unable to generate a response. Please try again.'

    // Extract actionable suggestions from the response
    const suggestions = extractSuggestions(assistantMessage)

    return res.status(200).json({
      message: assistantMessage,
      suggestions,
      model: data.model,
    })
  } catch (err) {
    console.error('Chat handler error:', err)
    return res.status(500).json({
      error: 'Internal server error',
      message: 'An unexpected error occurred. Please try again.',
    })
  }
}

function buildSystemPrompt(context?: RequestBody['context']): string {
  let prompt = `You are an expert AI financial advisor for a personal finance planning application. You provide clear, actionable, and personalized financial guidance.

Your expertise covers:
- Portfolio management and asset allocation
- Retirement planning and Monte Carlo projections
- Tax optimization strategies (tax-loss harvesting, Roth conversions, asset location)
- Goal-based financial planning (emergency fund, home purchase, education, retirement)
- Investment analysis and risk assessment
- Budgeting and cash flow management

Guidelines:
- Give specific, actionable advice rather than generic statements
- Always acknowledge risk and uncertainty when discussing investments
- Recommend consulting a licensed financial advisor for major decisions
- Keep responses concise but comprehensive (2-4 paragraphs max)
- Use dollar amounts and percentages where helpful
- Never recommend specific individual stocks; focus on diversification and asset classes
- Be honest about limitations in your analysis when data is unavailable`

  if (context?.portfolioData) {
    prompt += `\n\nUser's Portfolio Context:\n${JSON.stringify(context.portfolioData, null, 2)}`
  }

  if (context?.financialProfile) {
    prompt += `\n\nUser's Financial Profile:\n${JSON.stringify(context.financialProfile, null, 2)}`
  }

  if (context?.goals && Array.isArray(context.goals) && context.goals.length > 0) {
    prompt += `\n\nUser's Financial Goals:\n${JSON.stringify(context.goals, null, 2)}`
  }

  return prompt
}

function extractSuggestions(text: string): string[] {
  const suggestions: string[] = []

  const topics = [
    { keywords: ['rebalanc', 'allocat'], suggestion: 'Review your portfolio allocation' },
    { keywords: ['emergency fund', 'liquid'], suggestion: 'Check your emergency fund status' },
    { keywords: ['tax', 'harvest', 'roth'], suggestion: 'Explore tax optimization strategies' },
    { keywords: ['retire', '401k', 'ira'], suggestion: 'Review retirement contributions' },
    { keywords: ['diversif', 'concentrat'], suggestion: 'Improve portfolio diversification' },
    { keywords: ['risk', 'volatil'], suggestion: 'Reassess your risk tolerance' },
    { keywords: ['goal', 'target', 'milestone'], suggestion: 'Update your financial goals' },
    { keywords: ['budget', 'spend', 'saving'], suggestion: 'Analyze your spending patterns' },
  ]

  const lowerText = text.toLowerCase()
  for (const topic of topics) {
    if (topic.keywords.some((kw) => lowerText.includes(kw))) {
      suggestions.push(topic.suggestion)
    }
    if (suggestions.length >= 3) break
  }

  return suggestions
}

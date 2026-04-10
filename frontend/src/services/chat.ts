/**
 * Chat Service — connects to the /api/chat Vercel endpoint backed by Claude AI.
 * Sessions are managed in localStorage so conversations persist across page reloads.
 */

// Utility function for generating IDs that works in all browsers
function generateId(): string {
  return 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).substr(2, 9)
}

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
    portfolioData?: unknown
    financialProfile?: unknown
    goals?: unknown[]
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
    currentState: unknown
    recommendedAction: unknown
    reasoning: string
    risks: string[]
    prerequisites: string[]
  }
  createdAt: string
}

export interface AIInsights {
  spending_patterns: {
    trends: Array<{ category: string; change: number; timeframe: string }>
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

const SESSIONS_KEY = 'ai_chat_sessions'

function loadSessions(): ChatSession[] {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveSessions(sessions: ChatSession[]): void {
  try {
    // Keep only the 20 most recent sessions to limit storage usage
    const trimmed = sessions.slice(0, 20)
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(trimmed))
  } catch {
    // localStorage quota exceeded — silently continue
  }
}

class ChatService {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    // Build conversation history from session (last 10 messages)
    const sessions = loadSessions()
    const session = request.sessionId ? sessions.find((s) => s.id === request.sessionId) : null
    const history = session
      ? session.messages
          .filter((m) => m.role === 'user' || m.role === 'assistant')
          .slice(-10)
          .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
      : []

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: request.message,
          history,
          context: request.context,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: ChatMessage = {
          id: generateId(),
          content: data.message,
          role: 'assistant',
          timestamp: new Date().toISOString(),
          metadata: {
            suggestions: data.suggestions,
          },
        }

        // Persist the exchange to the session
        this.persistMessageToSession(request.sessionId, request.message, assistantMessage)

        return {
          message: assistantMessage,
          sessionId: request.sessionId || generateId(),
          suggestions: data.suggestions,
        }
      }

      // API returned an error response
      const errorData = await response.json().catch(() => ({}))
      const errorMessage = errorData.message || 'The AI advisor is temporarily unavailable. Please try again.'

      return this.errorResponse(errorMessage, request.sessionId)
    } catch (err) {
      console.error('Chat service error:', err)
      return this.errorResponse(
        'Unable to reach the AI advisor. Please check your connection and try again.',
        request.sessionId,
      )
    }
  }

  private errorResponse(content: string, sessionId?: string): ChatResponse {
    return {
      message: {
        id: generateId(),
        content,
        role: 'assistant',
        timestamp: new Date().toISOString(),
      },
      sessionId: sessionId || generateId(),
    }
  }

  private persistMessageToSession(sessionId: string | undefined, userText: string, assistantMsg: ChatMessage): void {
    const sessions = loadSessions()
    const id = sessionId || generateId()
    const existing = sessions.find((s) => s.id === id)

    const userMessage: ChatMessage = {
      id: generateId(),
      content: userText,
      role: 'user',
      timestamp: new Date(assistantMsg.timestamp).toISOString(),
    }

    if (existing) {
      existing.messages.push(userMessage, assistantMsg)
      existing.updatedAt = new Date().toISOString()
    } else {
      const newSession: ChatSession = {
        id,
        title: userText.length > 50 ? userText.slice(0, 50) + '…' : userText,
        messages: [userMessage, assistantMsg],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        userId: 'local',
      }
      sessions.unshift(newSession)
    }

    saveSessions(sessions)
  }

  async getChatSessions(): Promise<ChatSession[]> {
    return loadSessions()
  }

  async getChatSession(sessionId: string): Promise<ChatSession> {
    const sessions = loadSessions()
    const session = sessions.find((s) => s.id === sessionId)
    if (!session) throw new Error('Session not found')
    return session
  }

  async createChatSession(title?: string): Promise<ChatSession> {
    const sessions = loadSessions()
    const newSession: ChatSession = {
      id: generateId(),
      title: title || `Chat ${new Date().toLocaleDateString()}`,
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      userId: 'local',
    }
    sessions.unshift(newSession)
    saveSessions(sessions)
    return newSession
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    const sessions = loadSessions().filter((s) => s.id !== sessionId)
    saveSessions(sessions)
  }

  // WebSocket connection for real-time chat (requires backend WebSocket support)
  connectToChat(_sessionId: string, _onMessage: (message: ChatMessage) => void): WebSocket | null {
    // WebSocket backend not yet deployed — return null gracefully
    return null
  }
}

export const chatService = new ChatService()
export default chatService

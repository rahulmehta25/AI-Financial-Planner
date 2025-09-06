import { API_CONFIG } from '@/config/api'
import { apiService } from './api'
import { supabase, portfolios, holdings, auth } from '@/lib/supabase'

export interface UserProfile {
  id: string
  email: string
  firstName: string
  lastName: string
  isActive: boolean
  createdAt: string
  settings: UserSettings
  financialProfile?: FinancialProfile
}

export interface UserSettings {
  theme: 'light' | 'dark' | 'system'
  currency: string
  timezone: string
  notifications: {
    email: boolean
    push: boolean
    sms: boolean
    marketAlerts: boolean
    portfolioUpdates: boolean
    goalMilestones: boolean
  }
  privacy: {
    shareData: boolean
    analytics: boolean
    marketing: boolean
  }
}

export interface FinancialProfile {
  id: string
  age: number
  income: number
  netWorth: number
  investmentExperience: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  riskTolerance: 'conservative' | 'moderate' | 'aggressive' | 'very_aggressive'
  investmentGoals: string[]
  timeHorizon: number
  liquidityNeeds: 'low' | 'moderate' | 'high'
  dependents: number
  retirementAge: number
  monthlyExpenses: number
  emergencyFundMonths: number
  debtAmount: number
  employmentStatus: 'employed' | 'self_employed' | 'unemployed' | 'retired' | 'student'
  updatedAt: string
}

export interface DashboardData {
  user: UserProfile
  portfolioSummary: {
    totalValue: number
    dayChange: number
    dayChangePercentage: number
    topGainer?: string
    topLoser?: string
  }
  recentTransactions: Array<{
    id: string
    type: 'buy' | 'sell' | 'dividend' | 'fee'
    symbol: string
    amount: number
    date: string
  }>
  goals: Array<{
    id: string
    name: string
    targetAmount: number
    currentAmount: number
    targetDate: string
    progress: number
  }>
  alerts: Array<{
    id: string
    type: 'info' | 'warning' | 'success' | 'error'
    message: string
    date: string
    read: boolean
  }>
}

class UserService {
  async getProfile(): Promise<UserProfile> {
    try {
      return await apiService.get<UserProfile>(API_CONFIG.endpoints.user.profile)
    } catch (error) {
      console.error('Failed to fetch user profile:', error)
      throw error
    }
  }

  async updateProfile(updates: Partial<Pick<UserProfile, 'firstName' | 'lastName'>>): Promise<UserProfile> {
    try {
      return await apiService.put<UserProfile>(API_CONFIG.endpoints.user.updateProfile, updates)
    } catch (error) {
      console.error('Failed to update profile:', error)
      throw error
    }
  }

  async getSettings(): Promise<UserSettings> {
    try {
      return await apiService.get<UserSettings>(API_CONFIG.endpoints.user.settings)
    } catch (error) {
      console.error('Failed to fetch user settings:', error)
      throw error
    }
  }

  async updateSettings(settings: Partial<UserSettings>): Promise<UserSettings> {
    try {
      return await apiService.put<UserSettings>(API_CONFIG.endpoints.user.updateSettings, settings)
    } catch (error) {
      console.error('Failed to update settings:', error)
      throw error
    }
  }

  async getFinancialProfile(): Promise<FinancialProfile | null> {
    try {
      return await apiService.get<FinancialProfile>('/api/v1/financial-profiles/current')
    } catch (error: any) {
      if (error.status === 404) {
        return null // No financial profile exists yet
      }
      console.error('Failed to fetch financial profile:', error)
      throw error
    }
  }

  async createFinancialProfile(profile: Omit<FinancialProfile, 'id' | 'updatedAt'>): Promise<FinancialProfile> {
    try {
      return await apiService.post<FinancialProfile>('/api/v1/financial-profiles', profile)
    } catch (error) {
      console.error('Failed to create financial profile:', error)
      throw error
    }
  }

  async updateFinancialProfile(updates: Partial<FinancialProfile>): Promise<FinancialProfile> {
    try {
      return await apiService.put<FinancialProfile>('/api/v1/financial-profiles/current', updates)
    } catch (error) {
      console.error('Failed to update financial profile:', error)
      throw error
    }
  }

  async getDashboardData(): Promise<DashboardData> {
    try {
      // Get current user
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) throw new Error('Not authenticated')

      // Get user profile
      const { data: profile } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single()

      // Get portfolios with holdings
      const { data: userPortfolios } = await portfolios.getAll()
      
      // Calculate portfolio summary
      let totalValue = 0
      let totalCost = 0
      
      if (userPortfolios && userPortfolios.length > 0) {
        userPortfolios.forEach(portfolio => {
          if (portfolio.holdings) {
            portfolio.holdings.forEach((holding: any) => {
              totalValue += holding.current_value || (holding.quantity * (holding.current_price || holding.cost_basis))
              totalCost += holding.quantity * holding.cost_basis
            })
          }
        })
      }

      const dayChange = totalValue * 0.0087 // Mock 0.87% change for now
      const dayChangePercentage = 0.87

      // Get recent transactions
      const { data: transactions } = await supabase
        .from('transactions')
        .select('*')
        .order('transaction_date', { ascending: false })
        .limit(5)

      // Get goals
      const { data: goals } = await supabase
        .from('goals')
        .select('*')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })

      // Return real data or mock if empty
      if (!userPortfolios || userPortfolios.length === 0) {
        return this.getMockDashboardData()
      }

      return {
        user: {
          id: user.id,
          email: user.email || 'demo@financeai.com',
          firstName: profile?.full_name?.split(' ')[0] || 'Demo',
          lastName: profile?.full_name?.split(' ')[1] || 'User',
          isActive: true,
          createdAt: user.created_at || new Date().toISOString(),
          settings: this.getMockUserProfile().settings,
          financialProfile: this.getMockUserProfile().financialProfile
        },
        portfolioSummary: {
          totalValue: totalValue || 145000,
          dayChange,
          dayChangePercentage,
          topGainer: 'AAPL (+2.3%)',
          topLoser: 'BND (-0.5%)'
        },
        recentTransactions: transactions?.map(tx => ({
          id: tx.id,
          type: tx.transaction_type as 'buy' | 'sell' | 'dividend' | 'fee',
          symbol: tx.symbol,
          amount: tx.total_amount,
          date: tx.transaction_date
        })) || this.getMockDashboardData().recentTransactions,
        goals: goals?.map(goal => ({
          id: goal.id,
          name: goal.name,
          targetAmount: goal.target_amount,
          currentAmount: goal.current_amount || 0,
          targetDate: goal.target_date,
          progress: Math.round(((goal.current_amount || 0) / goal.target_amount) * 100)
        })) || this.getMockDashboardData().goals,
        alerts: this.getMockDashboardData().alerts
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
      // Return mock data as fallback
      return this.getMockDashboardData()
    }
  }

  async markAlertAsRead(alertId: string): Promise<void> {
    try {
      await apiService.put(`/api/v1/alerts/${alertId}/read`, {})
    } catch (error) {
      console.error('Failed to mark alert as read:', error)
      throw error
    }
  }

  async dismissAlert(alertId: string): Promise<void> {
    try {
      await apiService.delete(`/api/v1/alerts/${alertId}`)
    } catch (error) {
      console.error('Failed to dismiss alert:', error)
      throw error
    }
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await apiService.put('/api/v1/auth/change-password', {
        currentPassword,
        newPassword
      })
    } catch (error) {
      console.error('Failed to change password:', error)
      throw error
    }
  }

  async deleteAccount(password: string): Promise<void> {
    try {
      await apiService.delete('/api/v1/users/account', {
        body: JSON.stringify({ password })
      })
    } catch (error) {
      console.error('Failed to delete account:', error)
      throw error
    }
  }

  // Mock data methods
  private getMockUserProfile(): UserProfile {
    return {
      id: 'mock-user-123',
      email: 'demo@example.com',
      firstName: 'Demo',
      lastName: 'User',
      isActive: true,
      createdAt: '2023-01-01T00:00:00Z',
      settings: {
        theme: 'system',
        currency: 'USD',
        timezone: 'America/New_York',
        notifications: {
          email: true,
          push: true,
          sms: false,
          marketAlerts: true,
          portfolioUpdates: true,
          goalMilestones: true
        },
        privacy: {
          shareData: false,
          analytics: true,
          marketing: false
        }
      },
      financialProfile: this.getMockFinancialProfile()
    }
  }

  private getMockFinancialProfile(): FinancialProfile {
    return {
      id: 'mock-profile-123',
      age: 32,
      income: 75000,
      netWorth: 145000,
      investmentExperience: 'intermediate',
      riskTolerance: 'moderate',
      investmentGoals: ['Retirement', 'House Down Payment', 'Emergency Fund'],
      timeHorizon: 30,
      liquidityNeeds: 'moderate',
      dependents: 1,
      retirementAge: 65,
      monthlyExpenses: 4200,
      emergencyFundMonths: 4,
      debtAmount: 15000,
      employmentStatus: 'employed',
      updatedAt: new Date().toISOString()
    }
  }

  private getMockDashboardData(): DashboardData {
    return {
      user: this.getMockUserProfile(),
      portfolioSummary: {
        totalValue: 145000,
        dayChange: 1250,
        dayChangePercentage: 0.87,
        topGainer: 'AAPL (+2.3%)',
        topLoser: 'BND (-0.5%)'
      },
      recentTransactions: [
        {
          id: 'tx-1',
          type: 'buy',
          symbol: 'SPY',
          amount: 2250,
          date: new Date(Date.now() - 86400000).toISOString()
        },
        {
          id: 'tx-2',
          type: 'dividend',
          symbol: 'AAPL',
          amount: 87.50,
          date: new Date(Date.now() - 172800000).toISOString()
        },
        {
          id: 'tx-3',
          type: 'sell',
          symbol: 'MSFT',
          amount: 1875,
          date: new Date(Date.now() - 259200000).toISOString()
        }
      ],
      goals: [
        {
          id: 'goal-1',
          name: 'Emergency Fund',
          targetAmount: 25000,
          currentAmount: 15000,
          targetDate: '2024-12-31',
          progress: 60
        },
        {
          id: 'goal-2',
          name: 'House Down Payment',
          targetAmount: 60000,
          currentAmount: 45000,
          targetDate: '2026-06-01',
          progress: 75
        },
        {
          id: 'goal-3',
          name: 'Retirement Fund',
          targetAmount: 1000000,
          currentAmount: 85000,
          targetDate: '2056-01-01',
          progress: 8.5
        }
      ],
      alerts: [
        {
          id: 'alert-1',
          type: 'warning',
          message: 'Your emergency fund is below the recommended 6 months of expenses',
          date: new Date(Date.now() - 86400000).toISOString(),
          read: false
        },
        {
          id: 'alert-2',
          type: 'success',
          message: 'Congratulations! Your portfolio gained 12.3% this year',
          date: new Date(Date.now() - 172800000).toISOString(),
          read: false
        },
        {
          id: 'alert-3',
          type: 'info',
          message: 'Consider rebalancing your portfolio - stocks are now 75% of allocation',
          date: new Date(Date.now() - 259200000).toISOString(),
          read: true
        }
      ]
    }
  }
}

export const userService = new UserService()
export default userService
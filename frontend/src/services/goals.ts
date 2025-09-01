/**
 * Goals Service for managing financial goals
 */

import { supabase } from '@/lib/supabase'

export interface Goal {
  id: string
  name: string
  targetAmount: number
  currentAmount: number
  targetDate: string
  priority: 'low' | 'medium' | 'high'
  category: string
  progress: number
  description?: string
  userId?: string
  createdAt?: string
  updatedAt?: string
}

class GoalsService {
  /**
   * Get all goals for the current user
   */
  async getGoals(): Promise<Goal[]> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        // Return mock goals if not authenticated
        return this.getMockGoals()
      }

      // Try to fetch from Supabase
      const { data, error } = await supabase
        .from('goals')
        .select('*')
        .eq('user_id', user.id)
        .order('target_date', { ascending: true })

      if (error) {
        console.error('Error fetching goals:', error)
        return this.getMockGoals()
      }

      // Map and calculate progress
      return (data || []).map(goal => ({
        ...goal,
        progress: goal.current_amount > 0 ? Math.round((goal.current_amount / goal.target_amount) * 100) : 0
      }))
    } catch (error) {
      console.error('Error in getGoals:', error)
      return this.getMockGoals()
    }
  }

  /**
   * Create a new goal
   */
  async createGoal(goal: Omit<Goal, 'id' | 'progress' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<Goal> {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      
      if (!user) {
        throw new Error('User not authenticated')
      }

      const { data, error } = await supabase
        .from('goals')
        .insert({
          ...goal,
          user_id: user.id,
          current_amount: goal.currentAmount || 0
        })
        .select()
        .single()

      if (error) throw error

      return {
        ...data,
        progress: data.current_amount > 0 ? Math.round((data.current_amount / data.target_amount) * 100) : 0
      }
    } catch (error) {
      console.error('Error creating goal:', error)
      throw error
    }
  }

  /**
   * Update an existing goal
   */
  async updateGoal(id: string, updates: Partial<Goal>): Promise<Goal> {
    try {
      const { data, error } = await supabase
        .from('goals')
        .update({
          name: updates.name,
          target_amount: updates.targetAmount,
          current_amount: updates.currentAmount,
          target_date: updates.targetDate,
          priority: updates.priority,
          category: updates.category,
          description: updates.description
        })
        .eq('id', id)
        .select()
        .single()

      if (error) throw error

      return {
        ...data,
        progress: data.current_amount > 0 ? Math.round((data.current_amount / data.target_amount) * 100) : 0
      }
    } catch (error) {
      console.error('Error updating goal:', error)
      throw error
    }
  }

  /**
   * Delete a goal
   */
  async deleteGoal(id: string): Promise<void> {
    try {
      const { error } = await supabase
        .from('goals')
        .delete()
        .eq('id', id)

      if (error) throw error
    } catch (error) {
      console.error('Error deleting goal:', error)
      throw error
    }
  }

  /**
   * Update goal progress (current amount)
   */
  async updateProgress(id: string, currentAmount: number): Promise<Goal> {
    try {
      const { data, error } = await supabase
        .from('goals')
        .update({ current_amount: currentAmount })
        .eq('id', id)
        .select()
        .single()

      if (error) throw error

      return {
        ...data,
        progress: currentAmount > 0 ? Math.round((currentAmount / data.target_amount) * 100) : 0
      }
    } catch (error) {
      console.error('Error updating goal progress:', error)
      throw error
    }
  }

  /**
   * Get goals by category
   */
  async getGoalsByCategory(category: string): Promise<Goal[]> {
    try {
      const goals = await this.getGoals()
      return goals.filter(goal => goal.category === category)
    } catch (error) {
      console.error('Error fetching goals by category:', error)
      return []
    }
  }

  /**
   * Get goal statistics
   */
  async getGoalStatistics() {
    try {
      const goals = await this.getGoals()
      
      const totalGoals = goals.length
      const completedGoals = goals.filter(g => g.progress >= 100).length
      const totalTargetAmount = goals.reduce((sum, g) => sum + g.targetAmount, 0)
      const totalCurrentAmount = goals.reduce((sum, g) => sum + g.currentAmount, 0)
      const averageProgress = totalGoals > 0 
        ? goals.reduce((sum, g) => sum + g.progress, 0) / totalGoals 
        : 0

      return {
        totalGoals,
        completedGoals,
        inProgressGoals: totalGoals - completedGoals,
        totalTargetAmount,
        totalCurrentAmount,
        totalRemaining: totalTargetAmount - totalCurrentAmount,
        averageProgress: Math.round(averageProgress),
        categoryCounts: this.getCategoryCounts(goals)
      }
    } catch (error) {
      console.error('Error calculating goal statistics:', error)
      return {
        totalGoals: 0,
        completedGoals: 0,
        inProgressGoals: 0,
        totalTargetAmount: 0,
        totalCurrentAmount: 0,
        totalRemaining: 0,
        averageProgress: 0,
        categoryCounts: {}
      }
    }
  }

  /**
   * Helper to count goals by category
   */
  private getCategoryCounts(goals: Goal[]): Record<string, number> {
    return goals.reduce((counts, goal) => {
      counts[goal.category] = (counts[goal.category] || 0) + 1
      return counts
    }, {} as Record<string, number>)
  }

  /**
   * Mock goals for demo/testing
   */
  private getMockGoals(): Goal[] {
    return [
      {
        id: '1',
        name: 'Emergency Fund',
        targetAmount: 50000,
        currentAmount: 32000,
        targetDate: '2024-12-31',
        priority: 'high',
        category: 'Security',
        progress: 64,
        description: 'Build 6 months of expenses for emergency situations'
      },
      {
        id: '2',
        name: 'House Down Payment',
        targetAmount: 100000,
        currentAmount: 45000,
        targetDate: '2025-06-30',
        priority: 'high',
        category: 'Real Estate',
        progress: 45,
        description: '20% down payment for dream home'
      },
      {
        id: '3',
        name: 'Vacation Fund',
        targetAmount: 15000,
        currentAmount: 8500,
        targetDate: '2024-08-15',
        priority: 'medium',
        category: 'Lifestyle',
        progress: 57,
        description: 'Family vacation to Europe'
      },
      {
        id: '4',
        name: 'Retirement Fund',
        targetAmount: 1000000,
        currentAmount: 125000,
        targetDate: '2045-01-01',
        priority: 'high',
        category: 'Retirement',
        progress: 13,
        description: 'Financial independence by 65'
      },
      {
        id: '5',
        name: 'Car Purchase',
        targetAmount: 35000,
        currentAmount: 12000,
        targetDate: '2024-09-01',
        priority: 'medium',
        category: 'Transportation',
        progress: 34,
        description: 'New electric vehicle'
      }
    ]
  }
}

export const goalsService = new GoalsService()
export default goalsService
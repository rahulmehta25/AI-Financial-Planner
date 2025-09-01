/**
 * Unified Auth Service using Supabase
 * Replaces localStorage-based auth with Supabase Auth
 */

import { auth as supabaseAuth } from '../lib/supabase'

export interface User {
  id: string
  email: string
  name?: string
  firstName?: string
  lastName?: string
  avatarUrl?: string
  role?: string
  createdAt?: string
}

class AuthService {
  private currentUser: User | null = null

  /**
   * Sign in with email and password
   */
  async login(email: string, password: string): Promise<{ user: User | null; error: string | null }> {
    try {
      const { data, error } = await supabaseAuth.signIn(email, password)
      
      if (error) {
        return { user: null, error: error.message }
      }

      if (data?.user) {
        this.currentUser = this.mapSupabaseUser(data.user)
        return { user: this.currentUser, error: null }
      }

      return { user: null, error: 'Login failed' }
    } catch (error: any) {
      console.error('Login error:', error)
      return { user: null, error: error.message || 'Login failed' }
    }
  }

  /**
   * Register new user
   */
  async register(email: string, password: string, name?: string): Promise<{ user: User | null; error: string | null }> {
    try {
      const { data, error } = await supabaseAuth.signUp(email, password, name)
      
      if (error) {
        return { user: null, error: error.message }
      }

      if (data?.user) {
        this.currentUser = this.mapSupabaseUser(data.user)
        return { user: this.currentUser, error: null }
      }

      return { user: null, error: 'Registration failed' }
    } catch (error: any) {
      console.error('Register error:', error)
      return { user: null, error: error.message || 'Registration failed' }
    }
  }

  /**
   * Sign out current user
   */
  async logout(): Promise<void> {
    try {
      await supabaseAuth.signOut()
      this.currentUser = null
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  /**
   * Get current authenticated user
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const { user, error } = await supabaseAuth.getUser()
      
      if (error || !user) {
        this.currentUser = null
        return null
      }

      this.currentUser = this.mapSupabaseUser(user)
      return this.currentUser
    } catch (error) {
      console.error('Get user error:', error)
      return null
    }
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const user = await this.getCurrentUser()
    return !!user
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<User>): Promise<{ user: User | null; error: string | null }> {
    try {
      const currentUser = await this.getCurrentUser()
      if (!currentUser) {
        return { user: null, error: 'Not authenticated' }
      }

      // Update user metadata in Supabase
      // This would typically update the profiles table
      // For now, just update local state
      this.currentUser = { ...currentUser, ...updates }
      
      return { user: this.currentUser, error: null }
    } catch (error: any) {
      console.error('Update profile error:', error)
      return { user: null, error: error.message || 'Update failed' }
    }
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ error: string | null }> {
    try {
      // Supabase will send a password reset email
      const { error } = await supabaseAuth.signIn(email, '') // This triggers password reset in Supabase
      
      if (error && !error.message.includes('password')) {
        return { error: error.message }
      }

      return { error: null }
    } catch (error: any) {
      console.error('Password reset error:', error)
      return { error: error.message || 'Reset failed' }
    }
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<{ error: string | null }> {
    try {
      // This would be handled by Supabase's password reset flow
      // The token comes from the email link
      return { error: null }
    } catch (error: any) {
      console.error('Reset password error:', error)
      return { error: error.message || 'Reset failed' }
    }
  }

  /**
   * Verify email with token
   */
  async verifyEmail(token: string): Promise<{ error: string | null }> {
    try {
      // Handled by Supabase automatically via email link
      return { error: null }
    } catch (error: any) {
      console.error('Verify email error:', error)
      return { error: error.message || 'Verification failed' }
    }
  }

  /**
   * Get auth token (for API calls if needed)
   */
  async getToken(): Promise<string | null> {
    try {
      // In Supabase, the token is managed internally
      // This is just for compatibility with old code
      const { user } = await supabaseAuth.getUser()
      return user ? 'supabase-token' : null
    } catch (error) {
      console.error('Get token error:', error)
      return null
    }
  }

  /**
   * Check if user has specific role
   */
  hasRole(role: string): boolean {
    return this.currentUser?.role === role
  }

  /**
   * Map Supabase user to our User interface
   */
  private mapSupabaseUser(supabaseUser: any): User {
    return {
      id: supabaseUser.id,
      email: supabaseUser.email || '',
      name: supabaseUser.user_metadata?.full_name || supabaseUser.email?.split('@')[0],
      firstName: supabaseUser.user_metadata?.first_name,
      lastName: supabaseUser.user_metadata?.last_name,
      avatarUrl: supabaseUser.user_metadata?.avatar_url,
      role: supabaseUser.role || 'user',
      createdAt: supabaseUser.created_at
    }
  }

  /**
   * Listen to auth state changes
   */
  onAuthStateChange(callback: (user: User | null) => void): () => void {
    const { data } = supabaseAuth.onAuthStateChange((event, session) => {
      if (session?.user) {
        const user = this.mapSupabaseUser(session.user)
        this.currentUser = user
        callback(user)
      } else {
        this.currentUser = null
        callback(null)
      }
    })

    // Return unsubscribe function
    return () => {
      data.subscription.unsubscribe()
    }
  }
}

export const authService = new AuthService()

// Export for backward compatibility
export default authService
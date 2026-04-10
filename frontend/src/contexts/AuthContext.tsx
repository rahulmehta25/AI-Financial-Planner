import React, { createContext, useContext, useEffect, useState } from 'react'
import { supabase, auth } from '../lib/supabase'
import { User } from '@supabase/supabase-js'

interface AuthContextType {
  user: User | null
  loading: boolean
  isLoading: boolean  // Alias for compatibility
  isAuthenticated: boolean
  signUp: (email: string, password: string, fullName?: string) => Promise<any>
  signIn: (email: string, password: string) => Promise<any>
  signOut: () => Promise<any>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  isLoading: true,
  isAuthenticated: false,
  signUp: async () => {},
  signIn: async () => {},
  signOut: async () => {},
})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    auth.getUser().then(({ user }) => {
      setUser(user)
      setLoading(false)
    })

    // Listen for auth changes
    const subscription = auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null)
      setLoading(false)
    })

    return () => subscription.data.subscription.unsubscribe()
  }, [])

  const signUp = async (email: string, password: string, fullName?: string) => {
    const result = await auth.signUp(email, password, fullName)
    if (result.data?.user) {
      setUser(result.data.user)
    }
    return result
  }

  const signIn = async (email: string, password: string) => {
    const result = await auth.signIn(email, password)
    if (result.data?.user) {
      setUser(result.data.user)
    }
    return result
  }

  const signOut = async () => {
    const result = await auth.signOut()
    setUser(null)
    return result
  }

  const updateProfile = async (updates: any) => {
    // Placeholder for profile updates
    // In production, this would update the user profile in Supabase
    if (user) {
      setUser({ ...user, ...updates })
    }
    return { error: null }
  }

  const value = {
    user,
    loading,
    isLoading: loading,  // Alias for compatibility
    isAuthenticated: !!user,
    signUp,
    signIn,
    signOut,
    logout: signOut,  // Alias for compatibility
    login: signIn,    // Alias for compatibility
    register: signUp, // Alias for compatibility
    signup: signUp,   // Alias for compatibility
    updateProfile,
    token: null,      // Placeholder for token (Supabase handles this internally)
    error: null,      // Placeholder for error state
    clearError: () => {} // Placeholder for clearError function
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
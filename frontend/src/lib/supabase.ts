import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
  }
})

// Database Types
export type Profile = {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export type Portfolio = {
  id: string
  user_id: string
  name: string
  description?: string
  currency: string
  is_default: boolean
  created_at: string
  updated_at: string
}

export type Holding = {
  id: string
  portfolio_id: string
  symbol: string
  quantity: number
  cost_basis: number
  purchase_date: string
  asset_type: 'stock' | 'etf' | 'crypto' | 'bond'
  notes?: string
  current_price?: number
  current_value?: number
  gain_loss?: number
  gain_loss_percent?: number
}

export type Transaction = {
  id: string
  portfolio_id: string
  symbol: string
  transaction_type: 'buy' | 'sell' | 'dividend'
  quantity: number
  price: number
  total_amount: number
  transaction_date: string
  notes?: string
  created_at: string
}

export type MarketData = {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  previousClose: number
  open: number
  dayHigh: number
  dayLow: number
  volume: number
  marketCap?: number
  fiftyTwoWeekHigh?: number
  fiftyTwoWeekLow?: number
  dividendYield?: number
  pe?: number
  eps?: number
  timestamp: string
}

// Helper functions for market data
export async function fetchMarketData(action: string, symbols?: string | string[], period?: string) {
  try {
    const { data, error } = await supabase.functions.invoke('get-market-data', {
      body: { action, symbols, period }
    })
    
    if (error) throw error
    return data
  } catch (error) {
    console.error('Error fetching market data:', error)
    throw error
  }
}

// Auth helpers
export const auth = {
  signUp: async (email: string, password: string, fullName?: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          full_name: fullName,
        }
      }
    })
    return { data, error }
  },

  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  },

  signOut: async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  },

  getUser: async () => {
    const { data: { user }, error } = await supabase.auth.getUser()
    return { user, error }
  },

  onAuthStateChange: (callback: (event: any, session: any) => void) => {
    return supabase.auth.onAuthStateChange(callback)
  }
}

// Portfolio helpers
export const portfolios = {
  getAll: async () => {
    const { data, error } = await supabase
      .from('portfolios')
      .select('*, holdings(*)')
      .order('created_at', { ascending: false })
    
    return { data, error }
  },

  getById: async (id: string) => {
    const { data, error } = await supabase
      .from('portfolios')
      .select('*, holdings(*)')
      .eq('id', id)
      .single()
    
    return { data, error }
  },

  create: async (portfolio: Partial<Portfolio>) => {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) throw new Error('User not authenticated')

    const { data, error } = await supabase
      .from('portfolios')
      .insert({
        ...portfolio,
        user_id: user.id,
      })
      .select()
      .single()
    
    return { data, error }
  },

  update: async (id: string, updates: Partial<Portfolio>) => {
    const { data, error } = await supabase
      .from('portfolios')
      .update(updates)
      .eq('id', id)
      .select()
      .single()
    
    return { data, error }
  },

  delete: async (id: string) => {
    const { error } = await supabase
      .from('portfolios')
      .delete()
      .eq('id', id)
    
    return { error }
  }
}

// Holdings helpers
export const holdings = {
  create: async (holding: Partial<Holding>) => {
    const { data, error } = await supabase
      .from('holdings')
      .insert(holding)
      .select()
      .single()
    
    return { data, error }
  },

  update: async (id: string, updates: Partial<Holding>) => {
    const { data, error } = await supabase
      .from('holdings')
      .update(updates)
      .eq('id', id)
      .select()
      .single()
    
    return { data, error }
  },

  delete: async (id: string) => {
    const { error } = await supabase
      .from('holdings')
      .delete()
      .eq('id', id)
    
    return { error }
  },

  getByPortfolio: async (portfolioId: string) => {
    const { data, error } = await supabase
      .from('holdings')
      .select('*')
      .eq('portfolio_id', portfolioId)
      .order('symbol', { ascending: true })
    
    return { data, error }
  }
}

// Transactions helpers
export const transactions = {
  create: async (transaction: Partial<Transaction>) => {
    const { data, error } = await supabase
      .from('transactions')
      .insert(transaction)
      .select()
      .single()
    
    return { data, error }
  },

  getByPortfolio: async (portfolioId: string) => {
    const { data, error } = await supabase
      .from('transactions')
      .select('*')
      .eq('portfolio_id', portfolioId)
      .order('transaction_date', { ascending: false })
    
    return { data, error }
  }
}
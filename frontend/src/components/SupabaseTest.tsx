'use client'

import { useState, useEffect } from 'react'
import { supabase, auth, portfolios, fetchMarketData } from '@/lib/supabase'
import { useAuth } from '@/contexts/AuthContext'

export default function SupabaseTest() {
  const { user, signUp, signIn, signOut } = useAuth()
  const [email, setEmail] = useState('test@example.com')
  const [password, setPassword] = useState('test123456')
  const [portfolioData, setPortfolioData] = useState<any>(null)
  const [marketData, setMarketData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleSignUp = async () => {
    setLoading(true)
    const { data, error } = await signUp(email, password, 'Test User')
    if (error) {
      setMessage(`Sign up error: ${error.message}`)
    } else {
      setMessage('Sign up successful! Check your email to confirm.')
    }
    setLoading(false)
  }

  const handleSignIn = async () => {
    setLoading(true)
    const { data, error } = await signIn(email, password)
    if (error) {
      setMessage(`Sign in error: ${error.message}`)
    } else {
      setMessage('Sign in successful!')
    }
    setLoading(false)
  }

  const handleSignOut = async () => {
    setLoading(true)
    const { error } = await signOut()
    if (error) {
      setMessage(`Sign out error: ${error.message}`)
    } else {
      setMessage('Signed out successfully')
      setPortfolioData(null)
      setMarketData(null)
    }
    setLoading(false)
  }

  const fetchPortfolios = async () => {
    setLoading(true)
    const { data, error } = await portfolios.getAll()
    if (error) {
      setMessage(`Portfolio fetch error: ${error.message}`)
    } else {
      setPortfolioData(data)
      setMessage(`Found ${data?.length || 0} portfolios`)
    }
    setLoading(false)
  }

  const createTestPortfolio = async () => {
    setLoading(true)
    const { data, error } = await portfolios.create({
      name: 'Test Portfolio',
      description: 'Created via Supabase test',
      currency: 'USD'
    })
    if (error) {
      setMessage(`Create portfolio error: ${error.message}`)
    } else {
      setMessage('Portfolio created successfully!')
      fetchPortfolios()
    }
    setLoading(false)
  }

  const testMarketData = async () => {
    setLoading(true)
    try {
      const data = await fetchMarketData('quote', 'AAPL,MSFT,GOOGL')
      setMarketData(data)
      setMessage('Market data fetched successfully!')
    } catch (error: any) {
      setMessage(`Market data error: ${error.message}`)
    }
    setLoading(false)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Supabase Integration Test</h2>
      
      {/* Status Message */}
      {message && (
        <div className={`p-3 mb-4 rounded ${message.includes('error') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
          {message}
        </div>
      )}

      {/* Auth Status */}
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <h3 className="font-semibold mb-2">Authentication Status</h3>
        {user ? (
          <div>
            <p className="text-green-600">✓ Logged in as: {user.email}</p>
            <p className="text-sm text-gray-600">User ID: {user.id}</p>
          </div>
        ) : (
          <p className="text-gray-600">Not logged in</p>
        )}
      </div>

      {/* Auth Controls */}
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Authentication</h3>
        {!user ? (
          <div className="space-y-2">
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="px-3 py-2 border rounded mr-2"
            />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="px-3 py-2 border rounded mr-2"
            />
            <button
              onClick={handleSignUp}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 mr-2"
            >
              Sign Up
            </button>
            <button
              onClick={handleSignIn}
              disabled={loading}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50"
            >
              Sign In
            </button>
          </div>
        ) : (
          <button
            onClick={handleSignOut}
            disabled={loading}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50"
          >
            Sign Out
          </button>
        )}
      </div>

      {/* Database Operations */}
      {user && (
        <div className="mb-6">
          <h3 className="font-semibold mb-2">Database Operations</h3>
          <div className="space-x-2">
            <button
              onClick={fetchPortfolios}
              disabled={loading}
              className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50"
            >
              Fetch Portfolios
            </button>
            <button
              onClick={createTestPortfolio}
              disabled={loading}
              className="px-4 py-2 bg-indigo-500 text-white rounded hover:bg-indigo-600 disabled:opacity-50"
            >
              Create Test Portfolio
            </button>
          </div>

          {portfolioData && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h4 className="font-semibold mb-2">Portfolios:</h4>
              <pre className="text-sm overflow-auto">
                {JSON.stringify(portfolioData, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Market Data Test */}
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Market Data (Edge Function)</h3>
        <button
          onClick={testMarketData}
          disabled={loading}
          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50"
        >
          Test Market Data API
        </button>

        {marketData && (
          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h4 className="font-semibold mb-2">Market Data:</h4>
            <pre className="text-sm overflow-auto">
              {JSON.stringify(marketData, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="text-center text-gray-600">
          Loading...
        </div>
      )}
    </div>
  )
}
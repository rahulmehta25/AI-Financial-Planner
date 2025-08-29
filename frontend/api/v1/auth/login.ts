import type { VercelRequest, VercelResponse } from '@vercel/node'

interface LoginRequest {
  email: string
  password: string
}

interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    email: string
    firstName: string
    lastName: string
    isActive: boolean
    createdAt: string
  }
}

import { getUser } from './shared-users'

const generateToken = (userId: string, type: 'access' | 'refresh'): string => {
  const prefix = type === 'access' ? 'acc' : 'ref'
  const timestamp = Date.now()
  const random = Math.random().toString(36).substr(2, 16)
  return `${prefix}_${timestamp}_${userId}_${random}`
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({
      detail: 'Method not allowed'
    })
  }
  
  try {
    const { email, password }: LoginRequest = req.body
    
    if (!email || !password) {
      return res.status(400).json({
        detail: 'Email and password are required'
      })
    }
    
    // Check if user exists
    const user = getUser(email)
    if (!user) {
      return res.status(401).json({
        detail: 'Invalid email or password'
      })
    }
    
    // Verify password (in production, compare with hashed password)
    if (user.password !== password) {
      return res.status(401).json({
        detail: 'Invalid email or password'
      })
    }
    
    // Generate tokens
    const accessToken = generateToken(user.id, 'access')
    const refreshToken = generateToken(user.id, 'refresh')
    
    const response: AuthResponse = {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'Bearer',
      expires_in: 3600, // 1 hour
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        isActive: user.isActive || true,
        createdAt: user.createdAt
      }
    }
    
    console.log('User logged in:', user.email)
    return res.status(200).json(response)
  } catch (error) {
    console.error('Login error:', error)
    return res.status(500).json({
      detail: 'An error occurred during login'
    })
  }
}
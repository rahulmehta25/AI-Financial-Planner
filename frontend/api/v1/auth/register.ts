import type { VercelRequest, VercelResponse } from '@vercel/node'

interface RegisterRequest {
  email: string
  password: string
  firstName: string
  lastName: string
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
    createdAt: string
  }
}

import { users, addUser, userExists, User } from './shared-users'

const generateToken = (userId: string, type: 'access' | 'refresh'): string => {
  const prefix = type === 'access' ? 'acc' : 'ref'
  const timestamp = Date.now()
  const random = Math.random().toString(36).substr(2, 16)
  return `${prefix}_${timestamp}_${userId}_${random}`
}

const generateUserId = (): string => {
  return `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const validatePassword = (password: string): { valid: boolean; message?: string } => {
  if (password.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters long' }
  }
  if (!/(?=.*[A-Z])/.test(password)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter' }
  }
  if (!/(?=.*[a-z])/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' }
  }
  if (!/(?=.*\d)/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' }
  }
  if (!/(?=.*[!@#$%^&*(),.?":{}|<>])/.test(password)) {
    return { valid: false, message: 'Password must contain at least one special character' }
  }
  return { valid: true }
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
    const { email, password, firstName, lastName }: RegisterRequest = req.body
    
    // Validate required fields
    if (!email || !password || !firstName || !lastName) {
      return res.status(400).json({
        detail: 'All fields are required'
      })
    }
    
    // Validate email format
    if (!validateEmail(email)) {
      return res.status(400).json({
        detail: 'Invalid email format'
      })
    }
    
    // Validate password strength
    const passwordValidation = validatePassword(password)
    if (!passwordValidation.valid) {
      return res.status(400).json({
        detail: passwordValidation.message
      })
    }
    
    // Check if user already exists
    if (userExists(email)) {
      return res.status(409).json({
        detail: 'A user with this email already exists'
      })
    }
    
    // Create new user
    const userId = generateUserId()
    const newUser: User = {
      id: userId,
      email: email.toLowerCase(),
      password, // In production, this would be hashed
      firstName: firstName.trim(),
      lastName: lastName.trim(),
      createdAt: new Date().toISOString(),
      isActive: true
    }
    
    // Store user
    addUser(newUser)
    console.log('New user registered:', newUser.email)
    
    // Generate tokens
    const accessToken = generateToken(userId, 'access')
    const refreshToken = generateToken(userId, 'refresh')
    
    const response: AuthResponse = {
      access_token: accessToken,
      refresh_token: refreshToken,
      token_type: 'Bearer',
      expires_in: 3600, // 1 hour
      user: {
        id: newUser.id,
        email: newUser.email,
        firstName: newUser.firstName,
        lastName: newUser.lastName,
        createdAt: newUser.createdAt
      }
    }
    
    return res.status(201).json(response)
  } catch (error) {
    console.error('Registration error:', error)
    return res.status(500).json({
      detail: 'An error occurred during registration'
    })
  }
}
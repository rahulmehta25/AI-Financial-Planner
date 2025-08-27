import type { VercelRequest, VercelResponse } from '@vercel/node'

interface LoginRequest {
  email: string
  password: string
}

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

interface RefreshRequest {
  refresh_token: string
}

// Mock user database - combines login and register users
const mockUsers: { [email: string]: any } = {
  'demo@example.com': {
    id: 'user_demo_123',
    email: 'demo@example.com',
    password: 'demo123', // In production, this would be hashed
    firstName: 'Demo',
    lastName: 'User',
    createdAt: '2024-01-01T00:00:00Z'
  },
  'john@example.com': {
    id: 'user_john_456',
    email: 'john@example.com', 
    password: 'password123',
    firstName: 'John',
    lastName: 'Doe',
    createdAt: '2024-01-15T00:00:00Z'
  }
}

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
  if (password.length < 6) {
    return { valid: false, message: 'Password must be at least 6 characters long' }
  }
  if (!/(?=.*[a-z])/.test(password)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter' }
  }
  if (!/(?=.*\d)/.test(password)) {
    return { valid: false, message: 'Password must contain at least one number' }
  }
  return { valid: true }
}

const extractTokenFromHeader = (authHeader: string): string | null => {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null
  }
  return authHeader.substring(7)
}

const extractUserIdFromToken = (token: string): string | null => {
  try {
    const parts = token.split('_')
    if (parts.length >= 4 && (parts[0] === 'acc' || parts[0] === 'ref')) {
      return parts[2]
    }
    return null
  } catch {
    return null
  }
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, DELETE, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  const { operation } = req.query
  
  try {
    if (req.method === 'POST') {
      // Handle login, register, and refresh operations
      const operationType = operation as string || req.body.operation || 'login'
      
      switch (operationType) {
        case 'login': {
          const { email, password }: LoginRequest = req.body
          
          if (!email || !password) {
            return res.status(400).json({
              detail: 'Email and password are required'
            })
          }
          
          // Check if user exists
          const user = mockUsers[email as keyof typeof mockUsers]
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
              createdAt: user.createdAt
            }
          }
          
          return res.status(200).json(response)
        }
        
        case 'register': {
          const { email, password, firstName, lastName }: RegisterRequest = req.body
          
          // Validate required fields
          if (!email || !password || !firstName || !lastName) {
            return res.status(400).json({
              detail: 'All fields are required: email, password, firstName, lastName'
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
          if (mockUsers[email.toLowerCase()]) {
            return res.status(409).json({
              detail: 'A user with this email already exists'
            })
          }
          
          // Create new user
          const userId = generateUserId()
          const newUser = {
            id: userId,
            email: email.toLowerCase(),
            password, // In production, this would be hashed
            firstName: firstName.trim(),
            lastName: lastName.trim(),
            createdAt: new Date().toISOString()
          }
          
          // Store user (in production, save to database)
          mockUsers[email.toLowerCase()] = newUser
          
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
        }
        
        case 'refresh': {
          const { refresh_token }: RefreshRequest = req.body
          
          if (!refresh_token) {
            return res.status(400).json({
              detail: 'Refresh token is required'
            })
          }
          
          const userId = extractUserIdFromToken(refresh_token)
          if (!userId) {
            return res.status(401).json({
              detail: 'Invalid refresh token'
            })
          }
          
          // Find user by ID (in production, query database)
          const user = Object.values(mockUsers).find(u => u.id === userId)
          if (!user) {
            return res.status(401).json({
              detail: 'User not found'
            })
          }
          
          // Generate new tokens
          const accessToken = generateToken(userId, 'access')
          const newRefreshToken = generateToken(userId, 'refresh')
          
          const response: AuthResponse = {
            access_token: accessToken,
            refresh_token: newRefreshToken,
            token_type: 'Bearer',
            expires_in: 3600, // 1 hour
            user: {
              id: user.id,
              email: user.email,
              firstName: user.firstName,
              lastName: user.lastName,
              createdAt: user.createdAt
            }
          }
          
          return res.status(200).json(response)
        }
        
        default:
          return res.status(400).json({
            error: 'Invalid operation. Supported operations: login, register, refresh'
          })
      }
    } else if (req.method === 'DELETE') {
      // Handle logout
      const authHeader = req.headers.authorization as string
      const token = extractTokenFromHeader(authHeader)
      
      if (!token) {
        return res.status(401).json({
          detail: 'Authorization token required'
        })
      }
      
      // In production, you would invalidate the token in your token store/database
      // For now, just return success
      return res.status(200).json({
        message: 'Successfully logged out'
      })
    } else {
      return res.status(405).json({ error: 'Method not allowed' })
    }
    
  } catch (error) {
    console.error('Auth API error:', error)
    res.status(500).json({
      error: 'Internal server error',
      message: 'Authentication operation failed'
    })
  }
}
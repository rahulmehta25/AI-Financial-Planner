import type { VercelRequest, VercelResponse } from '@vercel/node'

interface UserProfile {
  id: string
  email: string
  firstName: string
  lastName: string
  createdAt: string
  profile?: {
    age?: number
    occupation?: string
    income?: number
    riskTolerance?: 'conservative' | 'moderate' | 'aggressive'
    financialGoals?: string[]
    investmentExperience?: 'beginner' | 'intermediate' | 'advanced'
  }
  preferences?: {
    currency?: 'USD' | 'EUR' | 'GBP'
    notifications?: {
      email: boolean
      push: boolean
      sms: boolean
    }
    theme?: 'light' | 'dark' | 'auto'
  }
}

interface UpdateProfileRequest {
  firstName?: string
  lastName?: string
  profile?: {
    age?: number
    occupation?: string
    income?: number
    riskTolerance?: 'conservative' | 'moderate' | 'aggressive'
    financialGoals?: string[]
    investmentExperience?: 'beginner' | 'intermediate' | 'advanced'
  }
  preferences?: {
    currency?: 'USD' | 'EUR' | 'GBP'
    notifications?: {
      email: boolean
      push: boolean
      sms: boolean
    }
    theme?: 'light' | 'dark' | 'auto'
  }
}

// Mock user database with extended profiles
const mockUserProfiles: { [userId: string]: UserProfile } = {
  'user_demo_123': {
    id: 'user_demo_123',
    email: 'demo@example.com',
    firstName: 'Demo',
    lastName: 'User',
    createdAt: '2024-01-01T00:00:00Z',
    profile: {
      age: 32,
      occupation: 'Software Engineer',
      income: 85000,
      riskTolerance: 'moderate',
      financialGoals: ['retirement', 'house_down_payment', 'emergency_fund'],
      investmentExperience: 'intermediate'
    },
    preferences: {
      currency: 'USD',
      notifications: {
        email: true,
        push: true,
        sms: false
      },
      theme: 'light'
    }
  },
  'user_john_456': {
    id: 'user_john_456',
    email: 'john@example.com',
    firstName: 'John',
    lastName: 'Doe',
    createdAt: '2024-01-15T00:00:00Z',
    profile: {
      age: 28,
      occupation: 'Marketing Manager',
      income: 72000,
      riskTolerance: 'aggressive',
      financialGoals: ['retirement', 'travel_fund'],
      investmentExperience: 'beginner'
    },
    preferences: {
      currency: 'USD',
      notifications: {
        email: true,
        push: false,
        sms: true
      },
      theme: 'dark'
    }
  }
}

const extractUserIdFromToken = (token: string): string | null => {
  try {
    const parts = token.split('_')
    if (parts.length >= 4 && parts[0] === 'acc') {
      return parts[2]
    }
    return null
  } catch {
    return null
  }
}

const extractTokenFromHeader = (authHeader: string): string | null => {
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return null
  }
  return authHeader.substring(7)
}

const validateProfileUpdate = (update: UpdateProfileRequest): { valid: boolean; errors: string[] } => {
  const errors: string[] = []
  
  if (update.profile?.age !== undefined) {
    if (update.profile.age < 18 || update.profile.age > 100) {
      errors.push('Age must be between 18 and 100')
    }
  }
  
  if (update.profile?.income !== undefined) {
    if (update.profile.income < 0) {
      errors.push('Income cannot be negative')
    }
  }
  
  if (update.profile?.riskTolerance !== undefined) {
    if (!['conservative', 'moderate', 'aggressive'].includes(update.profile.riskTolerance)) {
      errors.push('Risk tolerance must be conservative, moderate, or aggressive')
    }
  }
  
  if (update.profile?.investmentExperience !== undefined) {
    if (!['beginner', 'intermediate', 'advanced'].includes(update.profile.investmentExperience)) {
      errors.push('Investment experience must be beginner, intermediate, or advanced')
    }
  }
  
  if (update.preferences?.currency !== undefined) {
    if (!['USD', 'EUR', 'GBP'].includes(update.preferences.currency)) {
      errors.push('Currency must be USD, EUR, or GBP')
    }
  }
  
  if (update.preferences?.theme !== undefined) {
    if (!['light', 'dark', 'auto'].includes(update.preferences.theme)) {
      errors.push('Theme must be light, dark, or auto')
    }
  }
  
  return { valid: errors.length === 0, errors }
}

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, DELETE, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  // Extract and validate token for all operations
  const authHeader = req.headers.authorization as string
  const token = extractTokenFromHeader(authHeader)
  
  if (!token) {
    return res.status(401).json({
      detail: 'Authorization token required'
    })
  }
  
  const userId = extractUserIdFromToken(token)
  if (!userId) {
    return res.status(401).json({
      detail: 'Invalid token format'
    })
  }
  
  const { operation } = req.query
  
  try {
    const operationType = operation as string || 'profile'
    
    switch (operationType) {
      case 'profile': {
        if (req.method === 'GET') {
          // Get user profile
          const userProfile = mockUserProfiles[userId]
          
          if (!userProfile) {
            return res.status(404).json({
              detail: 'User profile not found'
            })
          }
          
          return res.status(200).json(userProfile)
          
        } else if (req.method === 'PUT') {
          // Update user profile
          const currentProfile = mockUserProfiles[userId]
          
          if (!currentProfile) {
            return res.status(404).json({
              detail: 'User profile not found'
            })
          }
          
          const updateData: UpdateProfileRequest = req.body
          
          // Validate the update
          const validation = validateProfileUpdate(updateData)
          if (!validation.valid) {
            return res.status(400).json({
              detail: 'Validation errors',
              errors: validation.errors
            })
          }
          
          // Merge the updates
          const updatedProfile: UserProfile = {
            ...currentProfile,
            ...(updateData.firstName && { firstName: updateData.firstName }),
            ...(updateData.lastName && { lastName: updateData.lastName }),
            profile: {
              ...currentProfile.profile,
              ...updateData.profile
            },
            preferences: {
              ...currentProfile.preferences,
              ...updateData.preferences,
              ...(updateData.preferences?.notifications && {
                notifications: {
                  ...currentProfile.preferences?.notifications,
                  ...updateData.preferences.notifications
                }
              })
            }
          }
          
          // Save the updated profile
          mockUserProfiles[userId] = updatedProfile
          
          return res.status(200).json(updatedProfile)
          
        } else {
          return res.status(405).json({ error: 'Method not allowed for profile operation' })
        }
      }
      
      case 'settings': {
        if (req.method === 'GET') {
          // Get user settings/preferences only
          const userProfile = mockUserProfiles[userId]
          
          if (!userProfile) {
            return res.status(404).json({
              detail: 'User not found'
            })
          }
          
          return res.status(200).json({
            preferences: userProfile.preferences || {},
            profile: {
              riskTolerance: userProfile.profile?.riskTolerance,
              investmentExperience: userProfile.profile?.investmentExperience
            }
          })
          
        } else if (req.method === 'PUT') {
          // Update settings only
          const currentProfile = mockUserProfiles[userId]
          
          if (!currentProfile) {
            return res.status(404).json({
              detail: 'User not found'
            })
          }
          
          const { preferences } = req.body
          
          if (preferences) {
            currentProfile.preferences = {
              ...currentProfile.preferences,
              ...preferences,
              ...(preferences.notifications && {
                notifications: {
                  ...currentProfile.preferences?.notifications,
                  ...preferences.notifications
                }
              })
            }
            
            mockUserProfiles[userId] = currentProfile
          }
          
          return res.status(200).json({
            preferences: currentProfile.preferences,
            message: 'Settings updated successfully'
          })
          
        } else {
          return res.status(405).json({ error: 'Method not allowed for settings operation' })
        }
      }
      
      case 'delete': {
        if (req.method !== 'DELETE') {
          return res.status(405).json({ error: 'Method not allowed for delete operation' })
        }
        
        // In a real app, this would mark the account for deletion and handle cleanup
        delete mockUserProfiles[userId]
        
        return res.status(200).json({
          message: 'User account deletion initiated. This action cannot be undone.'
        })
      }
      
      default:
        return res.status(400).json({
          error: 'Invalid operation. Supported operations: profile, settings, delete'
        })
    }
    
  } catch (error) {
    console.error('User API error:', error)
    res.status(500).json({
      error: 'Internal server error',
      message: 'Failed to process user request'
    })
  }
}
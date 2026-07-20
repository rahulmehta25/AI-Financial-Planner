// Shared user storage for demo purposes
// In production, this would be a database

export interface User {
  id: string
  email: string
  password: string
  firstName: string
  lastName: string
  isActive: boolean
  createdAt: string
}

// Initialize with demo users
export const users: Map<string, User> = new Map([
  ['demo@example.com', {
    id: 'user_demo_123',
    email: 'demo@example.com',
    password: 'Demo123!@#',
    firstName: 'Demo',
    lastName: 'User',
    isActive: true,
    createdAt: '2024-01-01T00:00:00Z'
  }],
  ['test@example.com', {
    id: 'user_test_456',
    email: 'test@example.com',
    password: 'Test123!@#',
    firstName: 'Test',
    lastName: 'User',
    isActive: true,
    createdAt: '2024-01-15T00:00:00Z'
  }]
])

// Helper functions
export const addUser = (user: User): void => {
  users.set(user.email.toLowerCase(), user)
}

export const getUser = (email: string): User | undefined => {
  return users.get(email.toLowerCase())
}

export const userExists = (email: string): boolean => {
  return users.has(email.toLowerCase())
}
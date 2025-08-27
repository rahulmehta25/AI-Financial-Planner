import type { VercelRequest, VercelResponse } from '@vercel/node'

interface HealthResponse {
  status: string
  timestamp: string
  version: string
  services: {
    api: string
    database: string
    cache: string
  }
  uptime: number
}

const startTime = Date.now()

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Enable CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
  
  if (req.method === 'OPTIONS') {
    res.status(200).end()
    return
  }
  
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }
  
  const uptime = Date.now() - startTime
  
  const healthData: HealthResponse = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0-serverless',
    services: {
      api: 'operational',
      database: 'mock',
      cache: 'mock'
    },
    uptime: uptime
  }
  
  res.status(200).json(healthData)
}
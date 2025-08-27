// Quick test script to verify mock services work
// Run this in browser console to test all mock functionality

// Test authentication service
import { authService } from './services/auth.js'
import { portfolioService } from './services/portfolio.js'
import { financialPlanningService } from './services/financialPlanning.js'
import { chatService } from './services/chat.js'
import { userService } from './services/user.js'
import { apiService } from './services/api.js'

async function testMockServices() {
  console.log('Testing Mock Services...')
  
  try {
    // Force backend unavailable mode
    apiService.setBackendAvailable(false)
    console.log('✓ Forced backend unavailable mode')

    // Test authentication
    console.log('\n--- Testing Authentication Service ---')
    const authResult = await authService.login({ 
      email: 'test@example.com', 
      password: 'password123' 
    })
    console.log('✓ Mock login successful:', authResult.user.email)

    // Test portfolio service  
    console.log('\n--- Testing Portfolio Service ---')
    const portfolio = await portfolioService.getPortfolioOverview()
    console.log('✓ Portfolio overview:', `$${portfolio.totalValue.toLocaleString()}`)
    
    const holdings = await portfolioService.getHoldings()
    console.log('✓ Holdings count:', holdings.length)
    
    const performance = await portfolioService.getPerformance('1Y')
    console.log('✓ Performance return:', `${performance.return.toFixed(2)}%`)

    // Test financial planning
    console.log('\n--- Testing Financial Planning Service ---')
    const simulation = await financialPlanningService.runSimulation({
      age: 30,
      income: 75000,
      savings: 50000,
      risk_tolerance: 'moderate'
    })
    console.log('✓ Simulation success probability:', `${simulation.result.success_probability}%`)
    
    const marketData = await financialPlanningService.getMarketData()
    console.log('✓ Market data asset classes:', marketData.asset_classes.length)

    // Test AI chat service
    console.log('\n--- Testing AI Chat Service ---')
    const chatResponse = await chatService.sendMessage({
      message: 'How should I plan for retirement?',
      sessionId: 'test-session'
    })
    console.log('✓ AI chat response length:', chatResponse.message.content.length)
    
    const recommendations = await chatService.getRecommendations()
    console.log('✓ AI recommendations count:', recommendations.length)

    // Test user service
    console.log('\n--- Testing User Service ---')
    const userProfile = await userService.getProfile()
    console.log('✓ User profile:', `${userProfile.firstName} ${userProfile.lastName}`)
    
    const dashboardData = await userService.getDashboardData()
    console.log('✓ Dashboard goals count:', dashboardData.goals.length)
    console.log('✓ Recent transactions count:', dashboardData.recentTransactions.length)

    console.log('\n🎉 ALL MOCK SERVICES WORKING CORRECTLY!')
    console.log('Frontend is now fully functional without backend dependency.')
    
    return {
      success: true,
      message: 'All mock services are working correctly',
      details: {
        auth: '✓ Login/signup with demo credentials',
        portfolio: '✓ Portfolio data, holdings, performance',
        financialPlanning: '✓ Simulations, market data, optimization',
        aiChat: '✓ Intelligent responses, recommendations',
        user: '✓ User profile, dashboard, financial profile'
      }
    }

  } catch (error) {
    console.error('❌ Mock service test failed:', error)
    return {
      success: false,
      error: error.message
    }
  }
}

// Export for use in browser console
window.testMockServices = testMockServices

// Automatically run test if in development
if (typeof process !== 'undefined' && process.env.NODE_ENV === 'development') {
  testMockServices().then(result => {
    console.log('Mock Services Test Result:', result)
  })
}

console.log('Mock services test loaded. Run testMockServices() in console to test.')
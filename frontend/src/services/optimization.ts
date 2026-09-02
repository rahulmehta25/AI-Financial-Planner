import { apiClient } from './api';

// Types for optimization service
export interface OptimizationRequest {
  constraints: {
    esg?: {
      enabled: boolean;
      minESGScore: number;
      excludeSectors: string[];
      sustainabilityFocus: 'none' | 'moderate' | 'high';
      carbonNeutralOnly: boolean;
      socialImpactWeight: number;
      governanceWeight: number;
    };
    sectors?: {
      enabled: boolean;
      sectors: {
        [key: string]: {
          min: number;
          max: number;
          enabled: boolean;
        };
      };
    };
    risk?: {
      maxRisk: number;
      minReturn: number;
      maxDrawdown: number;
      concentrationLimit: number;
      rebalanceThreshold: number;
    };
  };
  preferences: {
    riskTolerance: number;
    targetReturn: number;
    timeHorizon: number;
    liquidityNeeds: number;
  };
  currentPortfolio?: {
    holdings: Array<{
      symbol: string;
      shares: number;
      currentPrice: number;
      allocation: number;
    }>;
  };
}

export interface PortfolioPoint {
  risk: number;
  return: number;
  sharpeRatio: number;
  volatility: number;
  expectedReturn: number;
  weights: { [key: string]: number };
  allocations?: Array<{
    symbol: string;
    name: string;
    allocation: number;
    expectedReturn: number;
    risk: number;
  }>;
}

export interface EfficientFrontierData {
  portfolios: PortfolioPoint[];
  optimalPortfolio: PortfolioPoint;
  currentPortfolio?: PortfolioPoint;
  riskFreeRate: number;
  marketData: {
    symbols: string[];
    correlationMatrix: number[][];
    expectedReturns: { [key: string]: number };
    risks: { [key: string]: number };
  };
}

export interface OptimizationResult {
  efficientFrontier: EfficientFrontierData;
  recommendedAllocation: {
    assets: Array<{
      symbol: string;
      name: string;
      allocation: number;
      expectedReturn: number;
      risk: number;
      esgScore?: number;
      sector: string;
    }>;
    totalExpectedReturn: number;
    totalRisk: number;
    sharpeRatio: number;
  };
  analysis: {
    diversificationScore: number;
    constraintsSatisfied: boolean;
    warnings: string[];
    recommendations: string[];
  };
}

export interface RebalancingPlan {
  transactions: Array<{
    symbol: string;
    action: 'buy' | 'sell';
    shares: number;
    currentAllocation: number;
    targetAllocation: number;
    estimatedCost: number;
    taxImplications?: {
      gainLoss: number;
      taxLiability: number;
    };
  }>;
  summary: {
    totalCost: number;
    totalTaxLiability: number;
    estimatedTimeToExecute: string;
    complexityScore: number;
  };
}

export interface BacktestResult {
  portfolioValue: Array<{
    date: string;
    value: number;
    dailyReturn: number;
  }>;
  metrics: {
    totalReturn: number;
    annualizedReturn: number;
    volatility: number;
    sharpeRatio: number;
    maxDrawdown: number;
    winRate: number;
  };
  benchmark?: {
    totalReturn: number;
    annualizedReturn: number;
    volatility: number;
    sharpeRatio: number;
  };
}

class OptimizationService {
  // Mock data for development - replace with real API calls
  private generateMockEfficientFrontier(): EfficientFrontierData {
    const portfolios: PortfolioPoint[] = [];
    
    // Generate 50 points along the efficient frontier
    for (let i = 0; i <= 50; i++) {
      const risk = (i / 50) * 25 + 5; // Risk from 5% to 30%
      const baseReturn = Math.sqrt(risk - 5) * 2.2 + 3; // Curved relationship
      const noise = (Math.random() - 0.5) * 0.3;
      const expectedReturn = baseReturn + noise;
      const sharpeRatio = (expectedReturn - 2) / risk; // Assuming 2% risk-free rate
      
      portfolios.push({
        risk: Number(risk.toFixed(2)),
        return: Number(expectedReturn.toFixed(2)),
        sharpeRatio: Number(sharpeRatio.toFixed(3)),
        volatility: risk,
        expectedReturn,
        weights: {
          'VTI': Math.random() * 0.6 + 0.2,
          'VTIAX': Math.random() * 0.3 + 0.1,
          'BND': Math.random() * 0.4 + 0.1,
          'VNQ': Math.random() * 0.15 + 0.05,
          'VMFXX': Math.random() * 0.1
        }
      });
    }

    // Find optimal portfolio (highest Sharpe ratio)
    const optimalPortfolio = portfolios.reduce((best, current) => 
      current.sharpeRatio > best.sharpeRatio ? current : best
    );

    return {
      portfolios: portfolios.sort((a, b) => a.risk - b.risk),
      optimalPortfolio,
      riskFreeRate: 2.0,
      marketData: {
        symbols: ['VTI', 'VTIAX', 'BND', 'VNQ', 'VMFXX'],
        correlationMatrix: [
          [1.00, 0.85, -0.20, 0.70, 0.05],
          [0.85, 1.00, -0.15, 0.65, 0.10],
          [-0.20, -0.15, 1.00, 0.20, 0.15],
          [0.70, 0.65, 0.20, 1.00, 0.05],
          [0.05, 0.10, 0.15, 0.05, 1.00]
        ],
        expectedReturns: {
          'VTI': 8.5,
          'VTIAX': 7.2,
          'BND': 4.1,
          'VNQ': 6.8,
          'VMFXX': 2.1
        },
        risks: {
          'VTI': 18.0,
          'VTIAX': 20.0,
          'BND': 6.0,
          'VNQ': 22.0,
          'VMFXX': 1.0
        }
      }
    };
  }

  async optimizePortfolio(request: OptimizationRequest): Promise<OptimizationResult> {
    try {
      // In a real implementation, this would call the backend API
      // const response = await apiClient.post('/portfolio/optimize', request);
      // return response.data;

      // Mock implementation for demo
      await new Promise(resolve => setTimeout(resolve, 1500)); // Simulate API delay

      const efficientFrontier = this.generateMockEfficientFrontier();
      
      const recommendedAllocation = {
        assets: [
          {
            symbol: 'VTI',
            name: 'Total Stock Market ETF',
            allocation: 45.0,
            expectedReturn: 8.5,
            risk: 18.0,
            esgScore: 7.2,
            sector: 'Diversified'
          },
          {
            symbol: 'VTIAX',
            name: 'International Stock ETF',
            allocation: 20.0,
            expectedReturn: 7.2,
            risk: 20.0,
            esgScore: 6.8,
            sector: 'International'
          },
          {
            symbol: 'BND',
            name: 'Total Bond Market ETF',
            allocation: 25.0,
            expectedReturn: 4.1,
            risk: 6.0,
            esgScore: 8.0,
            sector: 'Fixed Income'
          },
          {
            symbol: 'VNQ',
            name: 'Real Estate ETF',
            allocation: 7.0,
            expectedReturn: 6.8,
            risk: 22.0,
            esgScore: 5.5,
            sector: 'Real Estate'
          },
          {
            symbol: 'VMFXX',
            name: 'Money Market Fund',
            allocation: 3.0,
            expectedReturn: 2.1,
            risk: 1.0,
            esgScore: 9.0,
            sector: 'Cash'
          }
        ],
        totalExpectedReturn: 6.85,
        totalRisk: 12.3,
        sharpeRatio: 0.39
      };

      return {
        efficientFrontier,
        recommendedAllocation,
        analysis: {
          diversificationScore: 0.85,
          constraintsSatisfied: true,
          warnings: [],
          recommendations: [
            'Consider increasing international allocation for better diversification',
            'ESG constraints are well satisfied with current allocation',
            'Risk level is within your specified tolerance'
          ]
        }
      };
    } catch (error) {
      console.error('Portfolio optimization failed:', error);
      throw new Error('Failed to optimize portfolio. Please try again.');
    }
  }

  async getEfficientFrontier(
    assets: string[],
    constraints: OptimizationRequest['constraints']
  ): Promise<EfficientFrontierData> {
    try {
      // In production: const response = await apiClient.post('/portfolio/efficient-frontier', { assets, constraints });
      // return response.data;

      await new Promise(resolve => setTimeout(resolve, 1000));
      return this.generateMockEfficientFrontier();
    } catch (error) {
      console.error('Failed to generate efficient frontier:', error);
      throw new Error('Failed to generate efficient frontier data.');
    }
  }

  async generateRebalancingPlan(
    currentHoldings: Array<{ symbol: string; shares: number; currentPrice: number }>,
    targetAllocations: Array<{ symbol: string; targetAllocation: number }>
  ): Promise<RebalancingPlan> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 800));

      const transactions = [
        {
          symbol: 'VTI',
          action: 'buy' as const,
          shares: 10,
          currentAllocation: 40.0,
          targetAllocation: 45.0,
          estimatedCost: 2500.00,
          taxImplications: {
            gainLoss: 0,
            taxLiability: 0
          }
        },
        {
          symbol: 'BND',
          action: 'sell' as const,
          shares: 5,
          currentAllocation: 30.0,
          targetAllocation: 25.0,
          estimatedCost: 500.00,
          taxImplications: {
            gainLoss: 25.00,
            taxLiability: 3.75
          }
        }
      ];

      return {
        transactions,
        summary: {
          totalCost: 2000.00,
          totalTaxLiability: 3.75,
          estimatedTimeToExecute: '2-3 business days',
          complexityScore: 0.3
        }
      };
    } catch (error) {
      console.error('Failed to generate rebalancing plan:', error);
      throw new Error('Failed to generate rebalancing plan.');
    }
  }

  async backtestPortfolio(
    allocations: Array<{ symbol: string; allocation: number }>,
    startDate: string,
    endDate: string
  ): Promise<BacktestResult> {
    try {
      // Mock implementation
      await new Promise(resolve => setTimeout(resolve, 1200));

      const portfolioValue = [];
      const startValue = 100000;
      let currentValue = startValue;

      // Generate daily values over the period
      const start = new Date(startDate);
      const end = new Date(endDate);
      const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));

      for (let i = 0; i <= days; i += 7) { // Weekly data points
        const date = new Date(start.getTime() + i * 24 * 60 * 60 * 1000);
        const volatility = 0.15; // 15% annual volatility
        const dailyReturn = (Math.random() - 0.5) * volatility / Math.sqrt(252);
        currentValue *= (1 + dailyReturn);

        portfolioValue.push({
          date: date.toISOString().split('T')[0],
          value: Math.round(currentValue),
          dailyReturn: Number((dailyReturn * 100).toFixed(3))
        });
      }

      const totalReturn = (currentValue - startValue) / startValue;
      const annualizedReturn = Math.pow(1 + totalReturn, 365 / days) - 1;

      return {
        portfolioValue,
        metrics: {
          totalReturn: Number((totalReturn * 100).toFixed(2)),
          annualizedReturn: Number((annualizedReturn * 100).toFixed(2)),
          volatility: 12.5,
          sharpeRatio: 0.85,
          maxDrawdown: -8.2,
          winRate: 58.3
        },
        benchmark: {
          totalReturn: 7.2,
          annualizedReturn: 7.8,
          volatility: 15.2,
          sharpeRatio: 0.48
        }
      };
    } catch (error) {
      console.error('Backtest failed:', error);
      throw new Error('Failed to run portfolio backtest.');
    }
  }

  async executeRebalancing(plan: RebalancingPlan): Promise<{ success: boolean; executedTransactions: number }> {
    try {
      // In production, this would execute trades through broker API
      await new Promise(resolve => setTimeout(resolve, 2000));

      return {
        success: true,
        executedTransactions: plan.transactions.length
      };
    } catch (error) {
      console.error('Failed to execute rebalancing:', error);
      throw new Error('Failed to execute rebalancing plan.');
    }
  }

  // Utility methods
  calculatePortfolioMetrics(
    allocations: Array<{ symbol: string; allocation: number; expectedReturn: number; risk: number }>,
    correlationMatrix?: number[][]
  ) {
    const totalExpectedReturn = allocations.reduce(
      (sum, asset) => sum + (asset.allocation / 100) * asset.expectedReturn, 
      0
    );

    // Simplified risk calculation without correlation matrix
    const totalRisk = Math.sqrt(
      allocations.reduce(
        (sum, asset) => sum + Math.pow((asset.allocation / 100) * asset.risk, 2), 
        0
      )
    );

    const riskFreeRate = 2.0;
    const sharpeRatio = (totalExpectedReturn - riskFreeRate) / totalRisk;

    return {
      expectedReturn: Number(totalExpectedReturn.toFixed(2)),
      risk: Number(totalRisk.toFixed(2)),
      sharpeRatio: Number(sharpeRatio.toFixed(3))
    };
  }
}

export const optimizationService = new OptimizationService();
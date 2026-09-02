/**
 * Tax Optimization Service - Frontend API client for tax optimization features
 * Connects to the backend tax optimization engine
 */

import { apiClient } from './api';

// Types for API requests and responses
export interface TaxHarvestingRequest {
  userId: string;
  filters?: {
    minLossAmount?: number;
    accountTypes?: string[];
    riskLevel?: 'low' | 'medium' | 'high';
  };
}

export interface TaxHarvestingResponse {
  opportunities: TaxHarvestingOpportunity[];
  summary: {
    totalPotentialLoss: number;
    totalTaxSavings: number;
    washSaleRisks: number;
    ytdHarvested: number;
  };
}

export interface TaxHarvestingOpportunity {
  id: string;
  security: {
    symbol: string;
    name: string;
    sector: string;
  };
  position: {
    shares: number;
    costBasis: number;
    currentValue: number;
    unrealizedLoss: number;
  };
  taxSavings: number;
  washSaleRisk: boolean;
  recommendation: string;
}

export interface RothConversionRequest {
  userId: string;
  conversionAmount: number;
  currentAge: number;
  retirementAge: number;
  traditionalBalance: number;
  rothBalance: number;
  currentIncome: number;
  filingStatus: string;
}

export interface RothConversionResponse {
  scenarios: RothConversionScenario[];
  recommendedScenario: string;
  taxImplications: {
    immediateTC: number;
    longTermBenefit: number;
    breakEvenYear: number;
  };
}

export interface RothConversionScenario {
  id: string;
  name: string;
  conversionAmount: number;
  taxCost: number;
  projectedBenefit: number;
  rmdImpact: number;
}

export interface AssetLocationRequest {
  userId: string;
  accounts: AccountAllocation[];
  targetAllocation: AssetAllocation[];
}

export interface AssetLocationResponse {
  currentTaxDrag: number;
  optimizedTaxDrag: number;
  recommendations: LocationRecommendation[];
  projectedSavings: number;
}

export interface AccountAllocation {
  accountId: string;
  accountType: 'taxable' | 'tax_deferred' | 'tax_free';
  balance: number;
  holdings: AssetHolding[];
}

export interface AssetAllocation {
  assetClass: string;
  targetPercent: number;
}

export interface AssetHolding {
  assetClass: string;
  amount: number;
  taxEfficiency: 'high' | 'medium' | 'low';
}

export interface LocationRecommendation {
  id: string;
  type: 'move' | 'rebalance';
  assetClass: string;
  fromAccount: string;
  toAccount: string;
  amount: number;
  taxSavings: number;
  reasoning: string;
}

export interface TaxBracketRequest {
  userId: string;
  income: number;
  filingStatus: string;
  state: string;
  deductions?: number;
}

export interface TaxBracketResponse {
  federalTax: number;
  stateTax: number;
  effectiveRate: number;
  marginalRate: number;
  brackets: TaxBracketInfo[];
  optimizationSuggestions: TaxOptimizationSuggestion[];
}

export interface TaxBracketInfo {
  rate: number;
  min: number;
  max: number;
  taxInBracket: number;
}

export interface TaxOptimizationSuggestion {
  id: string;
  type: string;
  title: string;
  description: string;
  potentialSavings: number;
  priority: 'high' | 'medium' | 'low';
}

/**
 * Tax Optimization API Service
 */
export class TaxOptimizationService {
  private static instance: TaxOptimizationService;
  
  static getInstance(): TaxOptimizationService {
    if (!TaxOptimizationService.instance) {
      TaxOptimizationService.instance = new TaxOptimizationService();
    }
    return TaxOptimizationService.instance;
  }

  /**
   * Get tax loss harvesting opportunities
   */
  async getHarvestingOpportunities(request: TaxHarvestingRequest): Promise<TaxHarvestingResponse> {
    try {
      const response = await apiClient.post('/api/v1/tax/harvesting/opportunities', request);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch harvesting opportunities:', error);
      // Return mock data for development
      return this.getMockHarvestingOpportunities();
    }
  }

  /**
   * Execute tax loss harvesting
   */
  async executeHarvesting(opportunityId: string, action: 'harvest' | 'schedule'): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.post(`/api/v1/tax/harvesting/execute/${opportunityId}`, { action });
      return response.data;
    } catch (error) {
      console.error('Failed to execute harvesting:', error);
      throw error;
    }
  }

  /**
   * Calculate Roth conversion scenarios
   */
  async calculateRothConversion(request: RothConversionRequest): Promise<RothConversionResponse> {
    try {
      const response = await apiClient.post('/api/v1/tax/roth/calculate', request);
      return response.data;
    } catch (error) {
      console.error('Failed to calculate Roth conversion:', error);
      // Return mock data for development
      return this.getMockRothConversion();
    }
  }

  /**
   * Get asset location optimization recommendations
   */
  async getAssetLocationRecommendations(request: AssetLocationRequest): Promise<AssetLocationResponse> {
    try {
      const response = await apiClient.post('/api/v1/tax/asset-location/optimize', request);
      return response.data;
    } catch (error) {
      console.error('Failed to get asset location recommendations:', error);
      // Return mock data for development
      return this.getMockAssetLocationRecommendations();
    }
  }

  /**
   * Calculate tax brackets and optimization suggestions
   */
  async calculateTaxBrackets(request: TaxBracketRequest): Promise<TaxBracketResponse> {
    try {
      const response = await apiClient.post('/api/v1/tax/brackets/calculate', request);
      return response.data;
    } catch (error) {
      console.error('Failed to calculate tax brackets:', error);
      // Return mock data for development
      return this.getMockTaxBrackets();
    }
  }

  /**
   * Get comprehensive tax optimization summary
   */
  async getTaxOptimizationSummary(userId: string): Promise<{
    totalPotentialSavings: number;
    ytdHarvesting: number;
    taxDragReduction: number;
    efficiencyScore: number;
    recommendedActions: number;
  }> {
    try {
      const response = await apiClient.get(`/api/v1/tax/summary/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get tax optimization summary:', error);
      // Return mock data for development
      return {
        totalPotentialSavings: 12850,
        ytdHarvesting: 8450,
        taxDragReduction: 2100,
        efficiencyScore: 82,
        recommendedActions: 5
      };
    }
  }

  // Mock data methods for development
  private getMockHarvestingOpportunities(): TaxHarvestingResponse {
    return {
      opportunities: [
        {
          id: '1',
          security: {
            symbol: 'VTI',
            name: 'Vanguard Total Stock Market ETF',
            sector: 'Broad Market'
          },
          position: {
            shares: 500,
            costBasis: 220.50,
            currentValue: 195.25,
            unrealizedLoss: -12625
          },
          taxSavings: 3156,
          washSaleRisk: false,
          recommendation: 'Harvest immediately - significant loss with high tax savings'
        }
      ],
      summary: {
        totalPotentialLoss: 14620,
        totalTaxSavings: 3655,
        washSaleRisks: 1,
        ytdHarvested: 8450
      }
    };
  }

  private getMockRothConversion(): RothConversionResponse {
    return {
      scenarios: [
        {
          id: 'current',
          name: 'Current Strategy',
          conversionAmount: 0,
          taxCost: 0,
          projectedBenefit: 485000,
          rmdImpact: 0
        },
        {
          id: 'moderate',
          name: 'Moderate Conversion',
          conversionAmount: 50000,
          taxCost: 12000,
          projectedBenefit: 525000,
          rmdImpact: 15000
        }
      ],
      recommendedScenario: 'moderate',
      taxImplications: {
        immediateTC: 12000,
        longTermBenefit: 40000,
        breakEvenYear: 2032
      }
    };
  }

  private getMockAssetLocationRecommendations(): AssetLocationResponse {
    return {
      currentTaxDrag: 3200,
      optimizedTaxDrag: 1100,
      projectedSavings: 2100,
      recommendations: [
        {
          id: '1',
          type: 'move',
          assetClass: 'REITs',
          fromAccount: 'Taxable',
          toAccount: 'Traditional 401k',
          amount: 50000,
          taxSavings: 900,
          reasoning: 'REITs generate high taxable distributions better suited for tax-deferred accounts'
        }
      ]
    };
  }

  private getMockTaxBrackets(): TaxBracketResponse {
    return {
      federalTax: 15240,
      stateTax: 3800,
      effectiveRate: 19.04,
      marginalRate: 22,
      brackets: [
        { rate: 10, min: 0, max: 23200, taxInBracket: 2320 },
        { rate: 12, min: 23200, max: 94300, taxInBracket: 8532 },
        { rate: 22, min: 94300, max: 201050, taxInBracket: 4388 }
      ],
      optimizationSuggestions: [
        {
          id: '1',
          type: 'contribution',
          title: 'Maximize 401(k) Contribution',
          description: 'Increase contribution to reduce taxable income',
          potentialSavings: 5060,
          priority: 'high'
        }
      ]
    };
  }
}

// Export singleton instance
export const taxOptimizationService = TaxOptimizationService.getInstance();
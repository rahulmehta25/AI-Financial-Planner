import { apiService } from './api';

export interface MonteCarloRequest {
  // Basic Parameters
  timeHorizon: number;
  initialInvestment: number;
  monthlyContribution: number;
  
  // Market Parameters
  expectedReturn: number;
  volatility: number;
  riskFreeRate: number;
  
  // Advanced Parameters
  numSimulations: number;
  jumpIntensity: number;
  jumpSizeMean: number;
  jumpSizeStd: number;
  
  // Regime Parameters
  enableRegimeSwitching: boolean;
  regimeDetection: boolean;
  
  // Goal Parameters
  targetAmount?: number;
  successThreshold: number;
}

export interface MonteCarloResponse {
  simulation_id: string;
  final_values: number[];
  paths: number[][];
  timestamps: number[];
  risk_metrics: {
    'Value at Risk (95%)': number;
    'Conditional VaR (95%)': number;
    'Maximum Drawdown': number;
    'Sharpe Ratio': number;
    'Skewness': number;
    'Kurtosis': number;
  };
  success_rate?: number;
  confidence_intervals: {
    '10%': number[];
    '25%': number[];
    '50%': number[];
    '75%': number[];
    '90%': number[];
  };
  metadata: {
    computation_time: number;
    gpu_accelerated: boolean;
    regime_switches_detected: number;
    total_jumps: number;
  };
}

export interface ScenarioComparison {
  scenarios: {
    name: string;
    parameters: MonteCarloRequest;
    results: MonteCarloResponse;
  }[];
  comparison_metrics: {
    expected_returns: number[];
    volatilities: number[];
    success_rates: number[];
    vars: number[];
    sharpe_ratios: number[];
  };
}

class MonteCarloService {
  private baseURL = '/api/v1/simulation';

  /**
   * Run a Monte Carlo simulation
   */
  async runSimulation(parameters: MonteCarloRequest): Promise<MonteCarloResponse> {
    try {
      const response = await apiService.post<MonteCarloResponse>(`${this.baseURL}/monte-carlo`, {
        // Map frontend parameter names to backend expected format
        n_years: parameters.timeHorizon,
        initial_investment: parameters.initialInvestment,
        monthly_contribution: parameters.monthlyContribution,
        expected_return: parameters.expectedReturn,
        volatility: parameters.volatility,
        risk_free_rate: parameters.riskFreeRate,
        n_paths: parameters.numSimulations,
        jump_intensity: parameters.jumpIntensity,
        jump_size_mean: parameters.jumpSizeMean,
        jump_size_std: parameters.jumpSizeStd,
        enable_regime_switching: parameters.enableRegimeSwitching,
        regime_detection: parameters.regimeDetection,
        target_amount: parameters.targetAmount,
        success_threshold: parameters.successThreshold,
      });

      return response.data;
    } catch (error: any) {
      console.error('Monte Carlo simulation failed:', error);
      throw new Error(
        error.response?.data?.message || 
        'Failed to run Monte Carlo simulation. Please check your parameters and try again.'
      );
    }
  }

  /**
   * Get simulation status (for long-running simulations)
   */
  async getSimulationStatus(simulationId: string): Promise<{
    status: 'running' | 'completed' | 'failed';
    progress?: number;
    error?: string;
    result?: MonteCarloResponse;
  }> {
    try {
      const response = await apiService.get(`${this.baseURL}/status/${simulationId}`);
      return response.data;
    } catch (error: any) {
      console.error('Failed to get simulation status:', error);
      throw new Error('Failed to retrieve simulation status');
    }
  }

  /**
   * Cancel a running simulation
   */
  async cancelSimulation(simulationId: string): Promise<void> {
    try {
      await apiService.delete(`${this.baseURL}/cancel/${simulationId}`);
    } catch (error: any) {
      console.error('Failed to cancel simulation:', error);
      throw new Error('Failed to cancel simulation');
    }
  }

  /**
   * Compare multiple scenarios
   */
  async compareScenarios(scenarios: {
    name: string;
    parameters: MonteCarloRequest;
  }[]): Promise<ScenarioComparison> {
    try {
      const response = await apiService.post<ScenarioComparison>(`${this.baseURL}/compare`, {
        scenarios: scenarios.map(scenario => ({
          name: scenario.name,
          parameters: {
            n_years: scenario.parameters.timeHorizon,
            initial_investment: scenario.parameters.initialInvestment,
            monthly_contribution: scenario.parameters.monthlyContribution,
            expected_return: scenario.parameters.expectedReturn,
            volatility: scenario.parameters.volatility,
            risk_free_rate: scenario.parameters.riskFreeRate,
            n_paths: scenario.parameters.numSimulations,
            jump_intensity: scenario.parameters.jumpIntensity,
            jump_size_mean: scenario.parameters.jumpSizeMean,
            jump_size_std: scenario.parameters.jumpSizeStd,
            enable_regime_switching: scenario.parameters.enableRegimeSwitching,
            regime_detection: scenario.parameters.regimeDetection,
            target_amount: scenario.parameters.targetAmount,
            success_threshold: scenario.parameters.successThreshold,
          }
        }))
      });

      return response.data;
    } catch (error: any) {
      console.error('Scenario comparison failed:', error);
      throw new Error('Failed to compare scenarios');
    }
  }

  /**
   * Export simulation results
   */
  async exportResults(simulationId: string, format: 'csv' | 'json' | 'pdf' = 'csv'): Promise<Blob> {
    try {
      const response = await apiService.get(`${this.baseURL}/export/${simulationId}`, {
        params: { format },
        responseType: 'blob'
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to export results:', error);
      throw new Error('Failed to export simulation results');
    }
  }

  /**
   * Get historical simulation results
   */
  async getHistoricalResults(limit: number = 10): Promise<{
    simulations: Array<{
      id: string;
      parameters: MonteCarloRequest;
      results: MonteCarloResponse;
      created_at: string;
    }>;
  }> {
    try {
      const response = await apiService.get(`${this.baseURL}/history`, {
        params: { limit }
      });

      return response.data;
    } catch (error: any) {
      console.error('Failed to get historical results:', error);
      throw new Error('Failed to retrieve historical simulation results');
    }
  }

  /**
   * Validate simulation parameters
   */
  validateParameters(parameters: MonteCarloRequest): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Basic validation
    if (parameters.timeHorizon <= 0 || parameters.timeHorizon > 50) {
      errors.push('Time horizon must be between 1 and 50 years');
    }

    if (parameters.initialInvestment < 0) {
      errors.push('Initial investment cannot be negative');
    }

    if (parameters.monthlyContribution < 0) {
      errors.push('Monthly contribution cannot be negative');
    }

    if (parameters.expectedReturn < -0.5 || parameters.expectedReturn > 1.0) {
      errors.push('Expected return must be between -50% and 100%');
    }

    if (parameters.volatility <= 0 || parameters.volatility > 1.0) {
      errors.push('Volatility must be between 0% and 100%');
    }

    if (parameters.riskFreeRate < 0 || parameters.riskFreeRate > 0.2) {
      errors.push('Risk-free rate must be between 0% and 20%');
    }

    if (parameters.numSimulations < 100 || parameters.numSimulations > 1000000) {
      errors.push('Number of simulations must be between 100 and 1,000,000');
    }

    if (parameters.jumpIntensity < 0 || parameters.jumpIntensity > 5) {
      errors.push('Jump intensity must be between 0 and 5');
    }

    if (parameters.successThreshold <= 0 || parameters.successThreshold > 1) {
      errors.push('Success threshold must be between 0% and 100%');
    }

    // Warnings
    if (parameters.numSimulations < 1000) {
      warnings.push('Consider using at least 1,000 simulations for more accurate results');
    }

    if (parameters.expectedReturn > 0.15) {
      warnings.push('Expected return above 15% may be optimistic for most asset classes');
    }

    if (parameters.volatility > 0.3) {
      warnings.push('Volatility above 30% indicates very high risk');
    }

    if (parameters.jumpIntensity > 1 && parameters.jumpSizeMean < 0) {
      warnings.push('High jump intensity with negative mean may lead to very pessimistic outcomes');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Get suggested parameter ranges based on asset class
   */
  getSuggestedParameters(assetClass: 'stocks' | 'bonds' | 'mixed' | 'aggressive'): Partial<MonteCarloRequest> {
    const suggestions = {
      stocks: {
        expectedReturn: 0.10,
        volatility: 0.16,
        jumpIntensity: 0.1,
        jumpSizeMean: -0.05,
        jumpSizeStd: 0.2
      },
      bonds: {
        expectedReturn: 0.04,
        volatility: 0.05,
        jumpIntensity: 0.02,
        jumpSizeMean: -0.02,
        jumpSizeStd: 0.1
      },
      mixed: {
        expectedReturn: 0.07,
        volatility: 0.12,
        jumpIntensity: 0.05,
        jumpSizeMean: -0.03,
        jumpSizeStd: 0.15
      },
      aggressive: {
        expectedReturn: 0.12,
        volatility: 0.20,
        jumpIntensity: 0.15,
        jumpSizeMean: -0.08,
        jumpSizeStd: 0.25
      }
    };

    return suggestions[assetClass];
  }

  /**
   * Calculate goal achievement probability
   */
  calculateGoalProbability(results: MonteCarloResponse, targetAmount: number): {
    probability: number;
    shortfall: number;
    surplus: number;
    confidenceLevel: string;
  } {
    const successCount = results.final_values.filter(value => value >= targetAmount).length;
    const probability = successCount / results.final_values.length;
    
    const shortfalls = results.final_values
      .filter(value => value < targetAmount)
      .map(value => targetAmount - value);
    
    const surpluses = results.final_values
      .filter(value => value >= targetAmount)
      .map(value => value - targetAmount);

    const avgShortfall = shortfalls.length > 0 
      ? shortfalls.reduce((a, b) => a + b, 0) / shortfalls.length 
      : 0;
    
    const avgSurplus = surpluses.length > 0 
      ? surpluses.reduce((a, b) => a + b, 0) / surpluses.length 
      : 0;

    const getConfidenceLevel = (prob: number): string => {
      if (prob >= 0.95) return 'Very High';
      if (prob >= 0.85) return 'High';
      if (prob >= 0.70) return 'Moderate';
      if (prob >= 0.50) return 'Low';
      return 'Very Low';
    };

    return {
      probability,
      shortfall: avgShortfall,
      surplus: avgSurplus,
      confidenceLevel: getConfidenceLevel(probability)
    };
  }
}

export const monteCarloService = new MonteCarloService();
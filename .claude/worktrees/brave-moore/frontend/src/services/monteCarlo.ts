/**
 * Monte Carlo Simulation Service — runs entirely in the browser.
 * No backend required. Uses geometric Brownian motion with optional
 * jump-diffusion (Merton model) for realistic market simulation.
 */

export interface MonteCarloRequest {
  timeHorizon: number
  initialInvestment: number
  monthlyContribution: number
  expectedReturn: number
  volatility: number
  riskFreeRate: number
  numSimulations: number
  jumpIntensity: number
  jumpSizeMean: number
  jumpSizeStd: number
  enableRegimeSwitching: boolean
  regimeDetection: boolean
  targetAmount?: number
  successThreshold: number
}

export interface MonteCarloResponse {
  simulation_id: string
  final_values: number[]
  paths: number[][]
  timestamps: number[]
  risk_metrics: {
    'Value at Risk (95%)': number
    'Conditional VaR (95%)': number
    'Maximum Drawdown': number
    'Sharpe Ratio': number
    'Skewness': number
    'Kurtosis': number
  }
  success_rate?: number
  confidence_intervals: {
    '10%': number[]
    '25%': number[]
    '50%': number[]
    '75%': number[]
    '90%': number[]
  }
  metadata: {
    computation_time: number
    gpu_accelerated: boolean
    regime_switches_detected: number
    total_jumps: number
  }
}

export interface ScenarioComparison {
  scenarios: {
    name: string
    parameters: MonteCarloRequest
    results: MonteCarloResponse
  }[]
  comparison_metrics: {
    expected_returns: number[]
    volatilities: number[]
    success_rates: number[]
    vars: number[]
    sharpe_ratios: number[]
  }
}

// --- Math helpers ---

/** Box-Muller transform: uniform [0,1) → standard normal */
function randn(): number {
  const u1 = Math.random()
  const u2 = Math.random()
  return Math.sqrt(-2 * Math.log(u1 + 1e-10)) * Math.cos(2 * Math.PI * u2)
}

/** Poisson-distributed random integer with rate λ */
function poissonRandom(lambda: number): number {
  const L = Math.exp(-lambda)
  let k = 0
  let p = 1
  while (p > L) {
    k++
    p *= Math.random()
  }
  return k - 1
}

function percentile(sorted: number[], p: number): number {
  const idx = (p / 100) * (sorted.length - 1)
  const lo = Math.floor(idx)
  const hi = Math.ceil(idx)
  if (lo === hi) return sorted[lo]
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo)
}

function mean(arr: number[]): number {
  return arr.reduce((a, b) => a + b, 0) / arr.length
}

function stddev(arr: number[], mu?: number): number {
  const m = mu ?? mean(arr)
  const variance = arr.reduce((acc, v) => acc + (v - m) ** 2, 0) / arr.length
  return Math.sqrt(variance)
}

function skewness(arr: number[]): number {
  const m = mean(arr)
  const s = stddev(arr, m)
  if (s === 0) return 0
  return arr.reduce((acc, v) => acc + ((v - m) / s) ** 3, 0) / arr.length
}

function kurtosis(arr: number[]): number {
  const m = mean(arr)
  const s = stddev(arr, m)
  if (s === 0) return 0
  return arr.reduce((acc, v) => acc + ((v - m) / s) ** 4, 0) / arr.length - 3
}

// --- Core simulation ---

class MonteCarloService {
  async runSimulation(params: MonteCarloRequest): Promise<MonteCarloResponse> {
    const start = performance.now()

    const {
      timeHorizon,
      initialInvestment,
      monthlyContribution,
      expectedReturn,
      volatility,
      riskFreeRate,
      numSimulations,
      jumpIntensity,
      jumpSizeMean,
      jumpSizeStd,
      enableRegimeSwitching,
      targetAmount,
      successThreshold,
    } = params

    // Cap simulations at 5 000 to keep the UI responsive in-browser
    const nSims = Math.min(numSimulations, 5000)
    const nSteps = timeHorizon * 12 // monthly steps
    const dt = 1 / 12 // 1 month in years

    // Drift (μ - σ²/2) for GBM
    const mu = expectedReturn - 0.5 * volatility ** 2

    // Regime parameters (bear/bull)
    const bullReturn = expectedReturn * 1.2
    const bearReturn = expectedReturn * 0.4
    const bullVol = volatility * 0.9
    const bearVol = volatility * 1.5
    const transitionToBear = 0.02 // monthly probability of switching to bear
    const transitionToBull = 0.10

    const allPaths: number[][] = []
    const finalValues: number[] = []
    let totalJumps = 0
    let totalRegimeSwitches = 0

    // Only sample a subset of paths for the chart to save memory (max 200)
    const pathSampleRate = Math.max(1, Math.floor(nSims / 200))

    for (let s = 0; s < nSims; s++) {
      let value = initialInvestment
      let inBullRegime = true
      const path: number[] = [value]

      for (let t = 0; t < nSteps; t++) {
        // Regime switching
        let mu_t = mu
        let vol_t = volatility
        if (enableRegimeSwitching) {
          if (inBullRegime) {
            if (Math.random() < transitionToBear) {
              inBullRegime = false
              totalRegimeSwitches++
            }
          } else {
            if (Math.random() < transitionToBull) {
              inBullRegime = true
              totalRegimeSwitches++
            }
          }
          const r = inBullRegime ? bullReturn : bearReturn
          const v = inBullRegime ? bullVol : bearVol
          mu_t = r - 0.5 * v ** 2
          vol_t = v
        }

        // GBM step
        const dW = randn() * Math.sqrt(dt)
        let returnMultiplier = Math.exp(mu_t * dt + vol_t * dW)

        // Jump diffusion
        if (jumpIntensity > 0) {
          const nJumps = poissonRandom(jumpIntensity * dt)
          if (nJumps > 0) {
            totalJumps += nJumps
            for (let j = 0; j < nJumps; j++) {
              const jumpSize = Math.exp(jumpSizeMean + jumpSizeStd * randn()) - 1
              returnMultiplier *= 1 + jumpSize
            }
          }
        }

        // Apply return and add monthly contribution
        value = Math.max(0, value * returnMultiplier + monthlyContribution)

        if (s % pathSampleRate === 0) {
          path.push(value)
        }
      }

      finalValues.push(value)
      if (s % pathSampleRate === 0) {
        allPaths.push(path)
      }
    }

    // Timestamps (years)
    const timestamps = Array.from({ length: nSteps + 1 }, (_, i) => i / 12)

    // Sort final values for percentile calculations
    const sorted = [...finalValues].sort((a, b) => a - b)

    // Confidence intervals at each time step
    const nPathSamples = allPaths.length
    const ci: MonteCarloResponse['confidence_intervals'] = {
      '10%': [],
      '25%': [],
      '50%': [],
      '75%': [],
      '90%': [],
    }

    for (let t = 0; t <= nSteps; t++) {
      const stepValues = allPaths.map((p) => p[Math.min(t, p.length - 1)]).sort((a, b) => a - b)
      ci['10%'].push(percentile(stepValues, 10))
      ci['25%'].push(percentile(stepValues, 25))
      ci['50%'].push(percentile(stepValues, 50))
      ci['75%'].push(percentile(stepValues, 75))
      ci['90%'].push(percentile(stepValues, 90))
    }

    // Risk metrics
    const varIndex = Math.floor(0.05 * sorted.length)
    const var95 = sorted[varIndex]
    const cvar95 = mean(sorted.slice(0, varIndex + 1))

    // Sharpe ratio: annualised excess return / volatility
    const finalReturns = finalValues.map((v) => Math.log(v / (initialInvestment || 1)) / timeHorizon)
    const meanReturn = mean(finalReturns)
    const retStd = stddev(finalReturns, meanReturn)
    const sharpe = retStd > 0 ? (meanReturn - riskFreeRate) / retStd : 0

    // Max drawdown across median path
    const medianPath = ci['50%']
    let peak = medianPath[0]
    let maxDrawdown = 0
    for (const v of medianPath) {
      if (v > peak) peak = v
      const dd = (peak - v) / (peak || 1)
      if (dd > maxDrawdown) maxDrawdown = dd
    }

    const successRate = targetAmount
      ? finalValues.filter((v) => v >= targetAmount * successThreshold).length / finalValues.length
      : undefined

    const elapsed = performance.now() - start

    return {
      simulation_id: 'browser-' + Date.now(),
      final_values: sorted,
      paths: allPaths,
      timestamps,
      risk_metrics: {
        'Value at Risk (95%)': var95,
        'Conditional VaR (95%)': cvar95,
        'Maximum Drawdown': maxDrawdown,
        'Sharpe Ratio': sharpe,
        Skewness: skewness(finalValues),
        Kurtosis: kurtosis(finalValues),
      },
      success_rate: successRate,
      confidence_intervals: ci,
      metadata: {
        computation_time: Math.round(elapsed),
        gpu_accelerated: false,
        regime_switches_detected: totalRegimeSwitches,
        total_jumps: totalJumps,
      },
    }
  }

  async compareScenarios(
    scenarios: { name: string; parameters: MonteCarloRequest }[],
  ): Promise<ScenarioComparison> {
    const results = await Promise.all(scenarios.map((s) => this.runSimulation(s.parameters)))

    return {
      scenarios: scenarios.map((s, i) => ({ name: s.name, parameters: s.parameters, results: results[i] })),
      comparison_metrics: {
        expected_returns: results.map((r) => mean(r.final_values)),
        volatilities: results.map((r) => stddev(r.final_values)),
        success_rates: results.map((r) => r.success_rate ?? 0),
        vars: results.map((r) => r.risk_metrics['Value at Risk (95%)']),
        sharpe_ratios: results.map((r) => r.risk_metrics['Sharpe Ratio']),
      },
    }
  }

  validateParameters(parameters: MonteCarloRequest): {
    isValid: boolean
    errors: string[]
    warnings: string[]
  } {
    const errors: string[] = []
    const warnings: string[] = []

    if (parameters.timeHorizon <= 0 || parameters.timeHorizon > 50)
      errors.push('Time horizon must be between 1 and 50 years')
    if (parameters.initialInvestment < 0) errors.push('Initial investment cannot be negative')
    if (parameters.monthlyContribution < 0) errors.push('Monthly contribution cannot be negative')
    if (parameters.expectedReturn < -0.5 || parameters.expectedReturn > 1.0)
      errors.push('Expected return must be between -50% and 100%')
    if (parameters.volatility <= 0 || parameters.volatility > 1.0)
      errors.push('Volatility must be between 0% and 100%')
    if (parameters.riskFreeRate < 0 || parameters.riskFreeRate > 0.2)
      errors.push('Risk-free rate must be between 0% and 20%')
    if (parameters.numSimulations < 100 || parameters.numSimulations > 1000000)
      errors.push('Number of simulations must be between 100 and 1,000,000')
    if (parameters.successThreshold <= 0 || parameters.successThreshold > 1)
      errors.push('Success threshold must be between 0% and 100%')

    if (parameters.numSimulations < 1000)
      warnings.push('Consider using at least 1,000 simulations for more accurate results')
    if (parameters.expectedReturn > 0.15)
      warnings.push('Expected return above 15% may be optimistic for most asset classes')
    if (parameters.volatility > 0.3) warnings.push('Volatility above 30% indicates very high risk')

    return { isValid: errors.length === 0, errors, warnings }
  }

  getSuggestedParameters(assetClass: 'stocks' | 'bonds' | 'mixed' | 'aggressive'): Partial<MonteCarloRequest> {
    return {
      stocks: { expectedReturn: 0.10, volatility: 0.16, jumpIntensity: 0.1, jumpSizeMean: -0.05, jumpSizeStd: 0.2 },
      bonds: { expectedReturn: 0.04, volatility: 0.05, jumpIntensity: 0.02, jumpSizeMean: -0.02, jumpSizeStd: 0.1 },
      mixed: { expectedReturn: 0.07, volatility: 0.12, jumpIntensity: 0.05, jumpSizeMean: -0.03, jumpSizeStd: 0.15 },
      aggressive: { expectedReturn: 0.12, volatility: 0.20, jumpIntensity: 0.15, jumpSizeMean: -0.08, jumpSizeStd: 0.25 },
    }[assetClass]
  }

  calculateGoalProbability(
    results: MonteCarloResponse,
    targetAmount: number,
  ): { probability: number; shortfall: number; surplus: number; confidenceLevel: string } {
    const successes = results.final_values.filter((v) => v >= targetAmount)
    const failures = results.final_values.filter((v) => v < targetAmount)
    const probability = successes.length / results.final_values.length
    const avgShortfall = failures.length > 0 ? mean(failures.map((v) => targetAmount - v)) : 0
    const avgSurplus = successes.length > 0 ? mean(successes.map((v) => v - targetAmount)) : 0

    const confidenceLevel =
      probability >= 0.95
        ? 'Very High'
        : probability >= 0.85
          ? 'High'
          : probability >= 0.7
            ? 'Moderate'
            : probability >= 0.5
              ? 'Low'
              : 'Very Low'

    return { probability, shortfall: avgShortfall, surplus: avgSurplus, confidenceLevel }
  }
}

export const monteCarloService = new MonteCarloService()

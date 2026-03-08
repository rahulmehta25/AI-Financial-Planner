export interface DemoHolding {
  id: string
  symbol: string
  name: string
  shares: number
  avgCost: number
  currentPrice: number
  marketValue: number
  gain: number
  gainPercent: number
  dayChange: number
  dayChangePercent: number
  sector: string
  allocation: number
}

export interface DemoGoal {
  id: string
  name: string
  currentAmount: number
  targetAmount: number
  progress: number
  category: string
  priority: 'high' | 'medium' | 'low'
  targetDate: string
  icon: string
}

export const DEMO_HOLDINGS: DemoHolding[] = [
  {
    id: 'h1', symbol: 'NVDA', name: 'NVIDIA Corp.', shares: 120,
    avgCost: 420.15, currentPrice: 721.28, marketValue: 86554,
    gain: 36135, gainPercent: 71.7, dayChange: 1842, dayChangePercent: 2.17, sector: 'Technology', allocation: 35.1,
  },
  {
    id: 'h2', symbol: 'VTI', name: 'Vanguard Total Market ETF', shares: 145,
    avgCost: 215.80, currentPrice: 268.15, marketValue: 38882,
    gain: 7591, gainPercent: 24.3, dayChange: 312, dayChangePercent: 0.81, sector: 'Broad Market', allocation: 15.7,
  },
  {
    id: 'h3', symbol: 'MSFT', name: 'Microsoft Corp.', shares: 100,
    avgCost: 285.40, currentPrice: 378.91, marketValue: 37891,
    gain: 9351, gainPercent: 32.8, dayChange: -189, dayChangePercent: -0.50, sector: 'Technology', allocation: 15.3,
  },
  {
    id: 'h4', symbol: 'AAPL', name: 'Apple Inc.', shares: 150,
    avgCost: 142.50, currentPrice: 178.72, marketValue: 26808,
    gain: 5433, gainPercent: 25.4, dayChange: 402, dayChangePercent: 1.52, sector: 'Technology', allocation: 10.9,
  },
  {
    id: 'h5', symbol: 'BRK.B', name: 'Berkshire Hathaway B', shares: 55,
    avgCost: 342.60, currentPrice: 408.23, marketValue: 22453,
    gain: 3610, gainPercent: 19.2, dayChange: -112, dayChangePercent: -0.50, sector: 'Financials', allocation: 9.1,
  },
  {
    id: 'h6', symbol: 'AMZN', name: 'Amazon.com Inc.', shares: 65,
    avgCost: 127.80, currentPrice: 178.25, marketValue: 11586,
    gain: 3279, gainPercent: 39.5, dayChange: 232, dayChangePercent: 2.04, sector: 'Consumer Discretionary', allocation: 4.7,
  },
  {
    id: 'h7', symbol: 'GOOGL', name: 'Alphabet Inc.', shares: 80,
    avgCost: 108.20, currentPrice: 141.80, marketValue: 11344,
    gain: 2688, gainPercent: 31.1, dayChange: -91, dayChangePercent: -0.80, sector: 'Technology', allocation: 4.6,
  },
  {
    id: 'h8', symbol: 'TSLA', name: 'Tesla Inc.', shares: 45,
    avgCost: 198.30, currentPrice: 248.42, marketValue: 11179,
    gain: 2255, gainPercent: 25.3, dayChange: 335, dayChangePercent: 3.09, sector: 'Consumer Discretionary', allocation: 4.5,
  },
]

export const DEMO_TOTAL_VALUE = DEMO_HOLDINGS.reduce((sum, h) => sum + h.marketValue, 0)
export const DEMO_TOTAL_GAIN = DEMO_HOLDINGS.reduce((sum, h) => sum + h.gain, 0)
export const DEMO_TOTAL_COST = DEMO_HOLDINGS.reduce((sum, h) => sum + h.avgCost * h.shares, 0)
export const DEMO_DAY_CHANGE = DEMO_HOLDINGS.reduce((sum, h) => sum + h.dayChange, 0)

export const DEMO_GOALS: DemoGoal[] = [
  {
    id: 'g1', name: 'Retirement', currentAmount: 1200000, targetAmount: 2000000,
    progress: 60, category: 'Retirement', priority: 'high', targetDate: '2050-01-01', icon: 'sunset',
  },
  {
    id: 'g2', name: 'Emergency Fund', currentAmount: 18000, targetAmount: 25000,
    progress: 72, category: 'Security', priority: 'high', targetDate: '2026-12-31', icon: 'shield',
  },
  {
    id: 'g3', name: 'House Down Payment', currentAmount: 45000, targetAmount: 80000,
    progress: 56, category: 'Real Estate', priority: 'medium', targetDate: '2028-06-01', icon: 'home',
  },
]

export const DEMO_RECENT_TRANSACTIONS = [
  { id: 'tx1', type: 'buy' as const, symbol: 'NVDA', amount: 3606, date: new Date(Date.now() - 86400000).toISOString() },
  { id: 'tx2', type: 'dividend' as const, symbol: 'VTI', amount: 142, date: new Date(Date.now() - 172800000).toISOString() },
  { id: 'tx3', type: 'buy' as const, symbol: 'AAPL', amount: 1787, date: new Date(Date.now() - 259200000).toISOString() },
  { id: 'tx4', type: 'sell' as const, symbol: 'TSLA', amount: 2484, date: new Date(Date.now() - 432000000).toISOString() },
  { id: 'tx5', type: 'dividend' as const, symbol: 'MSFT', amount: 68, date: new Date(Date.now() - 518400000).toISOString() },
]

export const AI_ADVISOR_RESPONSES: Record<string, { question: string; answer: string }> = {
  '401k': {
    question: 'Should I increase my 401(k) contributions?',
    answer: `Based on your current portfolio of $247K and income level, increasing your 401(k) contribution is one of the most impactful moves you can make. Here's my analysis:

**Current Situation:**
- Your portfolio is well-diversified across 8 holdings
- You have strong growth exposure through NVDA, MSFT, and tech holdings
- Your retirement goal shows $1.2M of $2M target (60% progress)

**Recommendation: Yes, increase contributions.**

1. **Maximize employer match first** - This is a guaranteed 50-100% return on your money. If your employer matches up to 6%, contribute at least 6%.

2. **Consider maxing out at $23,500/year** (2026 limit) - With your current savings rate, bumping to the max could add an additional $400K+ to your retirement by age 65 through compound growth.

3. **Tax benefit** - Each additional dollar contributed reduces your taxable income now. At a 24% marginal rate, a $5,000 increase saves you $1,200 in taxes this year.

4. **Roth vs Traditional** - Given your current income, a mix of traditional (for immediate tax savings) and Roth (for tax-free growth) is optimal.

**Impact:** Increasing from 10% to 15% of salary could close the gap on your $2M retirement target 3-5 years sooner.`,
  },
  'recession': {
    question: 'How should I rebalance for a potential recession?',
    answer: `Looking at your current portfolio composition, here's a recession-preparedness analysis:

**Current Allocation Assessment:**
- Technology: 65.9% (NVDA, MSFT, AAPL, GOOGL) - High cyclical exposure
- Broad Market: 15.7% (VTI) - Diversified but still equity-heavy
- Financials: 9.1% (BRK.B) - Moderately cyclical
- Consumer: 9.2% (AMZN, TSLA) - Cyclical

**Key Concerns:**
Your portfolio is heavily tilted toward growth/tech stocks which historically decline 30-40% in recessions. Your total $247K portfolio could see a $74K-$99K drawdown in a severe downturn.

**Recommended Rebalancing Strategy:**

1. **Reduce tech concentration** from 66% to 40-45%. Consider trimming NVDA (your largest winner at +71.7%) to lock in gains.

2. **Add defensive positions:**
   - Increase VTI allocation or add a bond ETF (BND/AGG) to 15-20%
   - Add consumer staples exposure (XLP or individual names like PG, JNJ)
   - Consider a dividend-focused ETF (SCHD) for income stability

3. **Build cash buffer** - Target 10-15% cash position ($25K-$37K) to deploy during market dips.

4. **Keep BRK.B** - Berkshire acts as a defensive holding with its massive cash reserves and diversified businesses.

5. **Don't panic sell** - If you have 10+ year time horizon, staying invested through recessions has historically been the winning strategy.

**Timing consideration:** Shift gradually over 3-6 months to avoid market timing risk. Dollar-cost average into defensive positions.`,
  },
  'tax_harvesting': {
    question: 'What tax loss harvesting opportunities do I have?',
    answer: `Let me analyze your portfolio for tax loss harvesting opportunities:

**Current Portfolio Gains/Losses:**
All 8 positions are currently showing gains, which limits direct harvesting opportunities. However, here's a strategic approach:

**Positions Review:**
| Holding | Gain | Gain % |
|---------|------|--------|
| NVDA | +$36,135 | +71.7% |
| MSFT | +$9,351 | +32.8% |
| VTI | +$7,591 | +24.3% |
| AAPL | +$5,433 | +25.4% |
| BRK.B | +$3,610 | +19.2% |
| AMZN | +$3,279 | +39.5% |
| GOOGL | +$2,688 | +31.1% |
| TSLA | +$2,255 | +25.3% |

**Total Unrealized Gains: ~$70,342**

**Strategies to Consider:**

1. **Selective lot harvesting** - If you purchased shares at different times, some individual lots may be at a loss even if the overall position is positive. Check your cost basis by lot.

2. **Strategic gain realization** - Consider selling NVDA shares to realize some of your $36K gain in a lower-income year, then reinvest in a similar (but not "substantially identical") semiconductor ETF like SMH.

3. **Wash sale awareness** - If you sell for a loss, avoid repurchasing the same or substantially identical security within 30 days before or after.

4. **Year-end planning:**
   - Pair gains with charitable giving (donate appreciated NVDA shares directly)
   - Use the $3,000 annual loss deduction against ordinary income
   - Carry forward unused losses to future years

5. **Asset location optimization** - Move high-growth holdings (NVDA, TSLA) into tax-advantaged accounts (IRA/401k) and hold tax-efficient index funds (VTI) in taxable accounts.

**Estimated Tax Savings:** By implementing these strategies, you could save $3,000-$8,000 in taxes this year depending on your income bracket and state.`,
  },
}

export const SECTOR_ALLOCATION = [
  { name: 'Technology', value: 65.9, color: '#059669' },
  { name: 'Broad Market', value: 15.7, color: '#0284c7' },
  { name: 'Financials', value: 9.1, color: '#7c3aed' },
  { name: 'Consumer Discretionary', value: 9.2, color: '#d97706' },
]

export function runClientMonteCarlo(
  initialInvestment: number,
  monthlyContribution: number,
  years: number,
  numPaths: number = 1000,
  annualReturn: number = 0.08,
  annualVolatility: number = 0.15,
): { months: number[]; median: number[]; p10: number[]; p90: number[]; paths: number[][] } {
  const months = years * 12
  const monthlyReturn = annualReturn / 12
  const monthlyVol = annualVolatility / Math.sqrt(12)

  const allPaths: number[][] = []

  for (let p = 0; p < numPaths; p++) {
    const path: number[] = [initialInvestment]
    let value = initialInvestment
    for (let m = 1; m <= months; m++) {
      const z = gaussianRandom()
      const drift = monthlyReturn - 0.5 * monthlyVol * monthlyVol
      const shock = monthlyVol * z
      value = value * Math.exp(drift + shock) + monthlyContribution
      path.push(value)
    }
    allPaths.push(path)
  }

  const monthLabels = Array.from({ length: months + 1 }, (_, i) => i)
  const median: number[] = []
  const p10: number[] = []
  const p90: number[] = []

  for (let m = 0; m <= months; m++) {
    const values = allPaths.map(path => path[m]).sort((a, b) => a - b)
    median.push(values[Math.floor(values.length * 0.5)])
    p10.push(values[Math.floor(values.length * 0.1)])
    p90.push(values[Math.floor(values.length * 0.9)])
  }

  return { months: monthLabels, median, p10, p90, paths: allPaths }
}

function gaussianRandom(): number {
  let u = 0, v = 0
  while (u === 0) u = Math.random()
  while (v === 0) v = Math.random()
  return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v)
}

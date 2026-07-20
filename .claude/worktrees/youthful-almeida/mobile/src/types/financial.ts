export interface FinancialState {
  profile: FinancialProfile | null;
  goals: Goal[];
  simulations: Simulation[];
  portfolios: Portfolio[];
  isLoading: boolean;
  error: string | null;
}

export interface FinancialProfile {
  id: string;
  userId: string;
  currentAge: number;
  retirementAge: number;
  currentIncome: number;
  currentSavings: number;
  monthlyExpenses: number;
  riskTolerance: RiskTolerance;
  accountBuckets: AccountBucket[];
  createdAt: string;
  updatedAt: string;
}

export interface AccountBucket {
  id: string;
  name: string;
  type: AccountType;
  balance: number;
  interestRate?: number;
  isRetirement: boolean;
}

export type AccountType = 
  | 'savings'
  | 'checking'
  | 'investment'
  | '401k'
  | 'ira'
  | 'roth_ira'
  | 'other';

export type RiskTolerance = 
  | 'conservative'
  | 'moderate'
  | 'aggressive';

export interface Goal {
  id: string;
  userId: string;
  name: string;
  description?: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  priority: GoalPriority;
  category: GoalCategory;
  isActive: boolean;
  milestones: Milestone[];
  createdAt: string;
  updatedAt: string;
}

export type GoalPriority = 'low' | 'medium' | 'high';

export type GoalCategory = 
  | 'retirement'
  | 'emergency_fund'
  | 'house'
  | 'education'
  | 'vacation'
  | 'debt_payoff'
  | 'other';

export interface Milestone {
  id: string;
  name: string;
  targetAmount: number;
  targetDate: string;
  isCompleted: boolean;
  completedAt?: string;
}

export interface Simulation {
  id: string;
  userId: string;
  name: string;
  parameters: SimulationParameters;
  results: SimulationResults;
  createdAt: string;
}

export interface SimulationParameters {
  currentAge: number;
  retirementAge: number;
  currentSavings: number;
  monthlyContribution: number;
  riskTolerance: RiskTolerance;
  inflationRate: number;
  monteCarloRuns: number;
}

export interface SimulationResults {
  probabilityOfSuccess: number;
  medianBalance: number;
  worstCaseBalance: number;
  bestCaseBalance: number;
  monthlyBalances: MonthlyBalance[];
  recommendations: string[];
}

export interface MonthlyBalance {
  month: number;
  median: number;
  percentile10: number;
  percentile90: number;
}

export interface Portfolio {
  id: string;
  name: string;
  allocation: AssetAllocation;
  value: number;
  performance: PortfolioPerformance;
  holdings: Holding[];
}

export interface AssetAllocation {
  stocks: number;
  bonds: number;
  cash: number;
  alternatives: number;
}

export interface PortfolioPerformance {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

export interface Holding {
  id: string;
  symbol: string;
  name: string;
  quantity: number;
  price: number;
  value: number;
  percentOfPortfolio: number;
  gainLoss: number;
  gainLossPercent: number;
}

export interface FormWizardStep {
  id: string;
  title: string;
  subtitle?: string;
  isCompleted: boolean;
  isValid: boolean;
  data: any;
}

export interface FormWizardState {
  currentStep: number;
  steps: FormWizardStep[];
  isLoading: boolean;
  error: string | null;
}
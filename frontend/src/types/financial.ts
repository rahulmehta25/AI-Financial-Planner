// Core financial planning types
export interface PersonalInfo {
  age: number;
  retirementAge: number;
  maritalStatus: 'single' | 'married' | 'divorced' | 'widowed';
  dependents: number;
  state: string;
  zipCode: string;
}

export interface FinancialSnapshot {
  annualIncome: number;
  monthlyExpenses: number;
  totalSavings: number;
  totalDebt: number;
  monthlyDebtPayments: number;
  emergencyFund: number;
  expectedSocialSecurity: number;
  pensionValue: number;
}

export interface AccountBuckets {
  taxable: {
    balance: number;
    monthlyContribution: number;
  };
  traditional401k: {
    balance: number;
    monthlyContribution: number;
    employerMatch: number;
    employerMatchPercent: number;
  };
  roth401k: {
    balance: number;
    monthlyContribution: number;
  };
  traditionalIRA: {
    balance: number;
    monthlyContribution: number;
  };
  rothIRA: {
    balance: number;
    monthlyContribution: number;
  };
  hsa: {
    balance: number;
    monthlyContribution: number;
  };
}

export interface RiskPreference {
  riskTolerance: 'conservative' | 'moderate' | 'aggressive' | 'very_aggressive';
  timeHorizon: number;
  volatilityComfort: 1 | 2 | 3 | 4 | 5;
  marketDownturnReaction: 'sell' | 'hold' | 'buy_more';
  investmentExperience: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}

export interface RetirementGoals {
  desiredMonthlyIncome: number;
  inflationAssumption: number;
  majorExpenses: Array<{
    name: string;
    amount: number;
    year: number;
  }>;
  legacyGoal: number;
  healthcareCosts: number;
  retirementLocation: 'current' | 'lower_cost' | 'higher_cost';
}

export interface FormData {
  personalInfo: PersonalInfo;
  financialSnapshot: FinancialSnapshot;
  accountBuckets: AccountBuckets;
  riskPreference: RiskPreference;
  retirementGoals: RetirementGoals;
}

export interface SimulationResult {
  id: string;
  timestamp: string;
  probabilityOfSuccess: number;
  medianPortfolioValue: number;
  percentile10Value: number;
  percentile90Value: number;
  shortfallRisk: number;
  recommendedPortfolio: PortfolioAllocation;
  projectedAnnualIncome: number[];
  projectedPortfolioValues: number[];
  tradeOffScenarios: TradeOffScenario[];
  aiNarrative: string;
}

export interface PortfolioAllocation {
  stocks: number;
  bonds: number;
  international: number;
  realEstate: number;
  commodities: number;
  cash: number;
}

export interface TradeOffScenario {
  type: 'save_more' | 'retire_later' | 'spend_less';
  title: string;
  description: string;
  originalValue: number;
  adjustedValue: number;
  impactOnSuccess: number;
  recommendation: string;
}

export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    borderColor?: string;
    backgroundColor?: string;
    fill?: boolean;
  }>;
}

export interface APIError {
  message: string;
  code?: string;
  field?: string;
}

export interface ValidationErrors {
  [key: string]: string[];
}

// Form step types
export type FormStep = 
  | 'personal-info'
  | 'financial-snapshot' 
  | 'account-buckets'
  | 'risk-preference'
  | 'retirement-goals'
  | 'review';

export interface StepConfig {
  id: FormStep;
  title: string;
  description: string;
  estimatedTime: number; // in minutes
}

// API response types
export interface SimulationRequest {
  formData: FormData;
  scenarioType?: 'base' | 'optimistic' | 'pessimistic';
}

export interface SimulationResponse {
  success: boolean;
  data?: SimulationResult;
  error?: APIError;
}

// Loading and UI state types
export interface LoadingState {
  isSubmitting: boolean;
  isGeneratingReport: boolean;
  isExportingPDF: boolean;
  currentStep: FormStep;
}

export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  autoClose?: boolean;
}
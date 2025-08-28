// Types for multi-account management system
export interface RetirementAccount {
  id: string;
  user_id: string;
  plan_id?: string;
  account_type: AccountType;
  account_name: string;
  account_number?: string;
  financial_institution?: string;
  tax_treatment: TaxTreatment;
  is_active: boolean;
  date_opened?: string;
  date_closed?: string;
  current_balance: number;
  vested_balance?: number;
  employer_name?: string;
  employer_ein?: string;
  plan_administrator?: string;
  available_investments?: InvestmentOption[];
  current_allocation?: AssetAllocation;
  primary_beneficiaries?: Beneficiary[];
  contingent_beneficiaries?: Beneficiary[];
  loan_balance?: number;
  loan_details?: LoanDetails;
  rmd_age?: number;
  first_rmd_year?: number;
  notes?: string;
  external_account_id?: string;
  created_at: string;
  updated_at: string;
}

export enum AccountType {
  TRADITIONAL_401K = 'traditional_401k',
  ROTH_401K = 'roth_401k',
  TRADITIONAL_IRA = 'traditional_ira',
  ROTH_IRA = 'roth_ira',
  SIMPLE_IRA = 'simple_ira',
  SEP_IRA = 'sep_ira',
  EDUCATION_529 = 'education_529',
  HSA = 'hsa',
  PENSION = 'pension',
  TAXABLE = 'taxable'
}

export enum TaxTreatment {
  TAX_DEFERRED = 'tax_deferred',
  TAX_FREE = 'tax_free',
  TRIPLE_TAX_ADVANTAGE = 'triple_tax_advantage',
  AFTER_TAX = 'after_tax'
}

export enum ContributionType {
  EMPLOYEE_PRETAX = 'employee_pretax',
  EMPLOYEE_ROTH = 'employee_roth',
  EMPLOYER_MATCH = 'employer_match',
  EMPLOYER_NONELECTIVE = 'employer_nonelective',
  PROFIT_SHARING = 'profit_sharing',
  ROLLOVER = 'rollover',
  CONVERSION = 'conversion'
}

export interface ContributionLimit {
  id: string;
  tax_year: number;
  account_type: AccountType;
  regular_limit: number;
  catch_up_limit: number;
  catch_up_age: number;
  income_phase_out_start_single?: number;
  income_phase_out_end_single?: number;
  income_phase_out_start_married?: number;
  income_phase_out_end_married?: number;
  employer_match_limit?: number;
  total_plan_limit?: number;
  hsa_family_limit?: number;
}

export interface Contribution {
  id: string;
  account_id: string;
  contribution_date: string;
  contribution_type: ContributionType;
  amount: number;
  tax_year: number;
  payroll_period_start?: string;
  payroll_period_end?: string;
  compensation_amount?: number;
  match_amount?: number;
  match_vesting_percentage?: number;
  tax_deductible: boolean;
  tax_year_limit_used?: number;
  catch_up_contribution?: number;
  external_transaction_id?: string;
  notes?: string;
}

export interface Transaction {
  id: string;
  account_id: string;
  transaction_date: string;
  type: 'contribution' | 'distribution' | 'transfer' | 'dividend' | 'fee';
  category: string;
  amount: number;
  description: string;
  balance_after?: number;
  external_id?: string;
  tags?: string[];
}

export interface AccountPerformance {
  account_id: string;
  total_return: number;
  total_return_percentage: number;
  ytd_return: number;
  ytd_return_percentage: number;
  one_year_return: number;
  three_year_return: number;
  five_year_return: number;
  inception_return: number;
  dividend_yield: number;
  expense_ratio: number;
  last_updated: string;
}

export interface OptimizationSuggestion {
  id: string;
  account_id: string;
  type: 'contribution' | 'allocation' | 'tax' | 'rebalance' | 'rollover';
  priority: 'low' | 'medium' | 'high';
  title: string;
  description: string;
  potential_benefit?: number;
  effort_required: 'low' | 'medium' | 'high';
  action_items: string[];
  deadline?: string;
  resources?: Resource[];
}

export interface ContributionProgress {
  account_type: AccountType;
  current_contributions: number;
  annual_limit: number;
  catch_up_eligible: boolean;
  catch_up_limit?: number;
  employer_match_available?: number;
  employer_match_utilized?: number;
  remaining_capacity: number;
  progress_percentage: number;
  months_remaining: number;
  suggested_monthly_contribution?: number;
}

// Supporting interfaces
export interface InvestmentOption {
  symbol: string;
  name: string;
  type: 'stock' | 'bond' | 'mutual_fund' | 'etf' | 'target_date';
  expense_ratio: number;
  performance: number;
}

export interface AssetAllocation {
  stocks: number;
  bonds: number;
  cash: number;
  international: number;
  alternatives?: number;
  target_date_fund?: string;
}

export interface Beneficiary {
  name: string;
  relationship: string;
  percentage: number;
  ssn_last_four?: string;
  contact_info?: ContactInfo;
}

export interface ContactInfo {
  email?: string;
  phone?: string;
  address?: Address;
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zip_code: string;
}

export interface LoanDetails {
  original_amount: number;
  current_balance: number;
  interest_rate: number;
  monthly_payment: number;
  remaining_payments: number;
  loan_date: string;
  maturity_date: string;
}

export interface Resource {
  title: string;
  url: string;
  type: 'article' | 'calculator' | 'form' | 'video';
}

// Plaid integration types
export interface PlaidLinkConfig {
  public_key: string;
  env: 'sandbox' | 'development' | 'production';
  product: string[];
  country_codes: string[];
  client_name: string;
  language: 'en';
  webhook: string;
}

export interface PlaidAccount {
  account_id: string;
  name: string;
  type: string;
  subtype: string;
  mask: string;
  balances: {
    available: number | null;
    current: number | null;
    limit: number | null;
    iso_currency_code: string;
  };
}

export interface PlaidInstitution {
  institution_id: string;
  name: string;
  country_codes: string[];
  products: string[];
  routing_numbers: string[];
}

// API response types
export interface AccountsResponse {
  accounts: RetirementAccount[];
  total_balance: number;
  contribution_limits: ContributionLimit[];
  performance: AccountPerformance[];
  optimization_suggestions: OptimizationSuggestion[];
}

export interface ContributionTrackingResponse {
  progress: ContributionProgress[];
  tax_year: number;
  last_updated: string;
}

export interface TransactionResponse {
  transactions: Transaction[];
  total_count: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

// Component prop types
export interface AccountCardProps {
  account: RetirementAccount;
  performance?: AccountPerformance;
  suggestions?: OptimizationSuggestion[];
  onViewDetails?: (accountId: string) => void;
  onOptimize?: (accountId: string) => void;
}

export interface ContributionTrackerProps {
  progress: ContributionProgress[];
  taxYear: number;
  onContribute?: (accountType: AccountType) => void;
}

export interface TransactionListProps {
  accountId?: string;
  transactions: Transaction[];
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  onCategorize?: (transactionId: string, category: string) => void;
  filters?: TransactionFilters;
  onFilterChange?: (filters: TransactionFilters) => void;
}

export interface TransactionFilters {
  dateRange?: {
    start: string;
    end: string;
  };
  types?: string[];
  categories?: string[];
  amountRange?: {
    min?: number;
    max?: number;
  };
  search?: string;
}

export interface PlaidLinkButtonProps {
  onSuccess: (publicToken: string, metadata: any) => void;
  onExit?: (error: any, metadata: any) => void;
  onLoad?: () => void;
  className?: string;
  disabled?: boolean;
  variant?: 'default' | 'outline' | 'secondary';
}
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime, timedelta

class AccountType(Enum):
    TRADITIONAL_401K = auto()
    ROTH_401K = auto()
    ROTH_IRA = auto()
    TRADITIONAL_IRA = auto()
    HSA = auto()
    _529_PLAN = auto()

@dataclass
class ContributionRules:
    annual_contribution_limit: float
    catch_up_contribution_limit: Optional[float] = None
    catch_up_age: Optional[int] = 50
    employer_match_rate: float = 0.0
    employer_match_limit: Optional[float] = None
    vesting_schedule: Dict[int, float] = field(default_factory=lambda: {
        1: 0.2,   # 20% vested after first year
        2: 0.4,   # 40% vested after second year
        3: 0.6,   # 60% vested after third year
        4: 0.8,   # 80% vested after fourth year
        5: 1.0    # 100% vested after fifth year
    })

class AccountModelEngine:
    def __init__(self, 
                 initial_balance: float = 0.0, 
                 annual_salary: float = 50_000,
                 contribution_percentage: float = 0.10,
                 start_age: int = 25,
                 retirement_age: int = 65):
        self.initial_balance = initial_balance
        self.annual_salary = annual_salary
        self.contribution_percentage = contribution_percentage
        self.start_age = start_age
        self.retirement_age = retirement_age
        
        # Pre-defined account rules
        self.account_rules = {
            AccountType.TRADITIONAL_401K: ContributionRules(
                annual_contribution_limit=22_500,
                catch_up_contribution_limit=7_500,
                employer_match_rate=0.05,
                employer_match_limit=2_500
            ),
            AccountType.ROTH_IRA: ContributionRules(
                annual_contribution_limit=6_500,
                catch_up_contribution_limit=1_000
            ),
            AccountType.HSA: ContributionRules(
                annual_contribution_limit=3_850,  # Individual limit
                catch_up_contribution_limit=1_000
            ),
            AccountType._529_PLAN: ContributionRules(
                annual_contribution_limit=17_000,  # Annual gift tax exclusion
                catch_up_contribution_limit=None
            )
        }

    def simulate_account_growth(self, 
                                account_type: AccountType, 
                                years: int = 40, 
                                expected_return: float = 0.07, 
                                expected_salary_growth: float = 0.03) -> pd.DataFrame:
        """
        Simulate account growth with dynamic contribution, employer match, and vesting
        """
        current_balance = self.initial_balance
        current_salary = self.annual_salary
        current_age = self.start_age
        
        results = []
        rules = self.account_rules.get(account_type)
        
        for year in range(years):
            # Update age and salary
            current_age += 1
            current_salary *= (1 + expected_salary_growth)
            
            # Determine contribution amount
            annual_contribution = current_salary * self.contribution_percentage
            
            # Apply contribution limits
            if current_age >= rules.catch_up_age and rules.catch_up_contribution_limit:
                max_contribution = min(
                    rules.annual_contribution_limit + rules.catch_up_contribution_limit, 
                    annual_contribution
                )
            else:
                max_contribution = min(rules.annual_contribution_limit, annual_contribution)
            
            # Employer match calculation
            employer_match = 0
            if hasattr(rules, 'employer_match_rate'):
                match_amount = current_salary * rules.employer_match_rate
                if rules.employer_match_limit:
                    match_amount = min(match_amount, rules.employer_match_limit)
                
                # Apply vesting
                vesting_percentage = rules.vesting_schedule.get(
                    min(year + 1, max(rules.vesting_schedule.keys())), 0
                )
                employer_match = match_amount * vesting_percentage
            
            # Grow balance
            current_balance *= (1 + expected_return)
            current_balance += max_contribution + employer_match
            
            results.append({
                'age': current_age,
                'year': datetime.now().year + year,
                'balance': current_balance,
                'contribution': max_contribution,
                'employer_match': employer_match,
                'vesting_percentage': vesting_percentage
            })
        
        return pd.DataFrame(results)

    def analyze_account_performance(self, account_data: pd.DataFrame) -> Dict:
        """
        Comprehensive analysis of account performance
        """
        performance_metrics = {
            'total_contributions': account_data['contribution'].sum(),
            'total_employer_match': account_data['employer_match'].sum(),
            'final_balance': account_data['balance'].iloc[-1],
            'total_growth': account_data['balance'].iloc[-1] - self.initial_balance,
            'growth_rate': (account_data['balance'].iloc[-1] / self.initial_balance) ** (1/len(account_data)) - 1,
            'final_age': account_data['age'].iloc[-1]
        }
        
        return performance_metrics

    def generate_comparative_report(self, years: int = 40) -> pd.DataFrame:
        """
        Generate performance report for different account types
        """
        reports = {}
        for account_type in [
            AccountType.TRADITIONAL_401K, 
            AccountType.ROTH_IRA, 
            AccountType.HSA, 
            AccountType._529_PLAN
        ]:
            account_data = self.simulate_account_growth(account_type, years)
            performance = self.analyze_account_performance(account_data)
            reports[account_type.name] = performance
        
        return pd.DataFrame.from_dict(reports, orient='index')

# Example usage
if __name__ == "__main__":
    engine = AccountModelEngine(
        initial_balance=10_000, 
        annual_salary=75_000,
        contribution_percentage=0.15,
        start_age=30,
        retirement_age=65
    )
    
    report = engine.generate_comparative_report()
    print("Account Performance Comparative Report:")
    print(report)

"""
Tax Optimization Service for Wealth Management

This service provides comprehensive tax optimization strategies including:
- Tax-loss harvesting with wash sale compliance
- Tax-efficient investment strategies
- Year-end tax planning tools
- State-specific tax features

Updated for 2025 tax year with current IRS brackets and rules.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from enum import Enum
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class TaxLotMethod(Enum):
    """Tax lot identification methods"""
    FIFO = "FIFO"  # First In, First Out
    LIFO = "LIFO"  # Last In, First Out
    HIFO = "HIFO"  # Highest In, First Out
    SPECIFIC_ID = "SPECIFIC_ID"  # Specific Identification


class AccountType(Enum):
    """Investment account types for tax optimization"""
    TAXABLE = "TAXABLE"
    TRADITIONAL_IRA = "TRADITIONAL_IRA"
    ROTH_IRA = "ROTH_IRA"
    TRADITIONAL_401K = "TRADITIONAL_401K"
    ROTH_401K = "ROTH_401K"
    HSA = "HSA"


class FilingStatus(Enum):
    """Tax filing status"""
    SINGLE = "SINGLE"
    MARRIED_JOINT = "MARRIED_JOINT"
    MARRIED_SEPARATE = "MARRIED_SEPARATE"
    HEAD_OF_HOUSEHOLD = "HEAD_OF_HOUSEHOLD"


@dataclass
class TaxBracket:
    """Tax bracket structure"""
    min_income: Decimal
    max_income: Optional[Decimal]
    rate: Decimal


@dataclass
class Investment:
    """Investment holding structure"""
    symbol: str
    quantity: Decimal
    purchase_price: Decimal
    purchase_date: datetime
    current_price: Decimal
    account_type: AccountType
    tax_lot_id: Optional[str] = None


@dataclass
class TaxLossOpportunity:
    """Tax loss harvesting opportunity"""
    investment: Investment
    unrealized_loss: Decimal
    tax_savings_estimate: Decimal
    wash_sale_warning: bool
    recommended_action: str
    days_until_wash_safe: Optional[int] = None


@dataclass
class AssetLocationRecommendation:
    """Asset location optimization recommendation"""
    asset_class: str
    recommended_account: AccountType
    current_account: AccountType
    tax_efficiency_score: float
    reason: str
    potential_annual_savings: Decimal


class TaxOptimizationService:
    """Comprehensive tax optimization service"""

    # 2025 IRS Tax Brackets (projected based on inflation adjustments)
    TAX_BRACKETS_2025 = {
        FilingStatus.SINGLE: [
            TaxBracket(Decimal('0'), Decimal('11700'), Decimal('0.10')),
            TaxBracket(Decimal('11700'), Decimal('47500'), Decimal('0.12')),
            TaxBracket(Decimal('47500'), Decimal('100500'), Decimal('0.22')),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24')),
            TaxBracket(Decimal('191650'), Decimal('243725'), Decimal('0.32')),
            TaxBracket(Decimal('243725'), Decimal('609350'), Decimal('0.35')),
            TaxBracket(Decimal('609350'), None, Decimal('0.37')),
        ],
        FilingStatus.MARRIED_JOINT: [
            TaxBracket(Decimal('0'), Decimal('23400'), Decimal('0.10')),
            TaxBracket(Decimal('23400'), Decimal('95000'), Decimal('0.12')),
            TaxBracket(Decimal('95000'), Decimal('201000'), Decimal('0.22')),
            TaxBracket(Decimal('201000'), Decimal('383300'), Decimal('0.24')),
            TaxBracket(Decimal('383300'), Decimal('487450'), Decimal('0.32')),
            TaxBracket(Decimal('487450'), Decimal('731200'), Decimal('0.35')),
            TaxBracket(Decimal('731200'), None, Decimal('0.37')),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            TaxBracket(Decimal('0'), Decimal('11700'), Decimal('0.10')),
            TaxBracket(Decimal('11700'), Decimal('47500'), Decimal('0.12')),
            TaxBracket(Decimal('47500'), Decimal('100500'), Decimal('0.22')),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24')),
            TaxBracket(Decimal('191650'), Decimal('243725'), Decimal('0.32')),
            TaxBracket(Decimal('243725'), Decimal('365600'), Decimal('0.35')),
            TaxBracket(Decimal('365600'), None, Decimal('0.37')),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(Decimal('0'), Decimal('16750'), Decimal('0.10')),
            TaxBracket(Decimal('16750'), Decimal('63700'), Decimal('0.12')),
            TaxBracket(Decimal('63700'), Decimal('100500'), Decimal('0.22')),
            TaxBracket(Decimal('100500'), Decimal('191650'), Decimal('0.24')),
            TaxBracket(Decimal('191650'), Decimal('243700'), Decimal('0.32')),
            TaxBracket(Decimal('243700'), Decimal('609350'), Decimal('0.35')),
            TaxBracket(Decimal('609350'), None, Decimal('0.37')),
        ]
    }

    # 2025 Capital Gains Tax Brackets
    CAPITAL_GAINS_BRACKETS_2025 = {
        FilingStatus.SINGLE: [
            TaxBracket(Decimal('0'), Decimal('47000'), Decimal('0.00')),
            TaxBracket(Decimal('47000'), Decimal('518900'), Decimal('0.15')),
            TaxBracket(Decimal('518900'), None, Decimal('0.20')),
        ],
        FilingStatus.MARRIED_JOINT: [
            TaxBracket(Decimal('0'), Decimal('94000'), Decimal('0.00')),
            TaxBracket(Decimal('94000'), Decimal('583750'), Decimal('0.15')),
            TaxBracket(Decimal('583750'), None, Decimal('0.20')),
        ],
        FilingStatus.MARRIED_SEPARATE: [
            TaxBracket(Decimal('0'), Decimal('47000'), Decimal('0.00')),
            TaxBracket(Decimal('47000'), Decimal('291875'), Decimal('0.15')),
            TaxBracket(Decimal('291875'), None, Decimal('0.20')),
        ],
        FilingStatus.HEAD_OF_HOUSEHOLD: [
            TaxBracket(Decimal('0'), Decimal('63000'), Decimal('0.00')),
            TaxBracket(Decimal('63000'), Decimal('551350'), Decimal('0.15')),
            TaxBracket(Decimal('551350'), None, Decimal('0.20')),
        ]
    }

    # State tax rates (simplified - in reality this would be much more complex)
    STATE_TAX_RATES = {
        'CA': Decimal('0.133'),  # California top rate
        'NY': Decimal('0.109'),  # New York top rate
        'TX': Decimal('0.000'),  # No state income tax
        'FL': Decimal('0.000'),  # No state income tax
        'WA': Decimal('0.000'),  # No state income tax
        'NV': Decimal('0.000'),  # No state income tax
        'TN': Decimal('0.000'),  # No state income tax
        'NH': Decimal('0.050'),  # Interest and dividends only
        'OR': Decimal('0.099'),  # Oregon top rate
        'NJ': Decimal('0.1075'), # New Jersey top rate
    }

    def __init__(self):
        self.wash_sale_period = 30  # Days before/after for wash sale rule

    def calculate_marginal_tax_rate(self, income: Decimal, filing_status: FilingStatus,
                                  state: Optional[str] = None) -> Decimal:
        """Calculate marginal tax rate for given income and filing status"""
        brackets = self.TAX_BRACKETS_2025[filing_status]
        
        for bracket in reversed(brackets):
            if bracket.max_income is None or income > bracket.min_income:
                federal_rate = bracket.rate
                break
        else:
            federal_rate = brackets[0].rate
        
        state_rate = self.STATE_TAX_RATES.get(state, Decimal('0.05')) if state else Decimal('0')
        
        return federal_rate + state_rate

    def calculate_capital_gains_rate(self, income: Decimal, filing_status: FilingStatus,
                                   holding_period_days: int) -> Decimal:
        """Calculate capital gains tax rate"""
        if holding_period_days <= 365:
            # Short-term capital gains taxed as ordinary income
            return self.calculate_marginal_tax_rate(income, filing_status)
        
        # Long-term capital gains
        brackets = self.CAPITAL_GAINS_BRACKETS_2025[filing_status]
        
        for bracket in reversed(brackets):
            if bracket.max_income is None or income > bracket.min_income:
                return bracket.rate
        
        return brackets[0].rate

    def identify_tax_loss_opportunities(self, investments: List[Investment],
                                      income: Decimal, filing_status: FilingStatus,
                                      realized_gains_ytd: Decimal = Decimal('0'),
                                      recent_sales: Optional[List[Dict]] = None) -> List[TaxLossOpportunity]:
        """Identify tax-loss harvesting opportunities"""
        opportunities = []
        recent_sales = recent_sales or []
        
        marginal_rate = self.calculate_marginal_tax_rate(income, filing_status)
        
        for investment in investments:
            if investment.account_type != AccountType.TAXABLE:
                continue  # Tax-loss harvesting only applies to taxable accounts
            
            current_value = investment.quantity * investment.current_price
            cost_basis = investment.quantity * investment.purchase_price
            unrealized_loss = cost_basis - current_value
            
            if unrealized_loss > 0:
                # Check for wash sale risk
                wash_sale_warning, days_until_safe = self._check_wash_sale_risk(
                    investment, recent_sales
                )
                
                # Estimate tax savings
                # Use short-term rate if held <= 1 year, otherwise long-term
                holding_days = (datetime.now() - investment.purchase_date).days
                if holding_days <= 365:
                    tax_rate = marginal_rate
                else:
                    tax_rate = self.calculate_capital_gains_rate(income, filing_status, holding_days)
                
                tax_savings = min(unrealized_loss, realized_gains_ytd + Decimal('3000')) * tax_rate
                
                recommended_action = self._generate_harvest_recommendation(
                    investment, unrealized_loss, wash_sale_warning, days_until_safe
                )
                
                opportunity = TaxLossOpportunity(
                    investment=investment,
                    unrealized_loss=unrealized_loss,
                    tax_savings_estimate=tax_savings,
                    wash_sale_warning=wash_sale_warning,
                    recommended_action=recommended_action,
                    days_until_wash_safe=days_until_safe
                )
                
                opportunities.append(opportunity)
        
        # Sort by tax savings potential
        opportunities.sort(key=lambda x: x.tax_savings_estimate, reverse=True)
        return opportunities

    def _check_wash_sale_risk(self, investment: Investment,
                            recent_sales: List[Dict]) -> Tuple[bool, Optional[int]]:
        """Check for wash sale rule violations"""
        symbol = investment.symbol
        current_date = datetime.now()
        
        # Check recent sales of same or substantially identical securities
        for sale in recent_sales:
            if (sale.get('symbol') == symbol and 
                abs((current_date - sale.get('sale_date', current_date)).days) <= self.wash_sale_period):
                
                sale_date = sale.get('sale_date', current_date)
                days_until_safe = self.wash_sale_period - abs((current_date - sale_date).days)
                return True, max(0, days_until_safe)
        
        return False, None

    def _generate_harvest_recommendation(self, investment: Investment, loss: Decimal,
                                       wash_sale_warning: bool, days_until_safe: Optional[int]) -> str:
        """Generate tax-loss harvesting recommendation"""
        if wash_sale_warning:
            if days_until_safe and days_until_safe > 0:
                return f"Wait {days_until_safe} days to avoid wash sale rule, then harvest ${loss:.2f} loss"
            else:
                return f"Harvest ${loss:.2f} loss immediately (wash sale period has passed)"
        else:
            return f"Harvest ${loss:.2f} loss immediately - no wash sale concerns"

    def optimize_tax_lots(self, sales_needed: Decimal, available_lots: List[Investment],
                         method: TaxLotMethod = TaxLotMethod.HIFO,
                         target_gain_loss: Optional[str] = None) -> List[Investment]:
        """Optimize tax lot selection for sales"""
        if not available_lots:
            return []
        
        # Calculate gain/loss for each lot
        lot_performance = []
        for lot in available_lots:
            gain_loss = (lot.current_price - lot.purchase_price) * lot.quantity
            lot_performance.append((lot, gain_loss, lot.current_price - lot.purchase_price))
        
        # Sort based on method
        if method == TaxLotMethod.HIFO:
            # Highest cost basis first (minimize gains or maximize losses)
            lot_performance.sort(key=lambda x: x[0].purchase_price, reverse=True)
        elif method == TaxLotMethod.LIFO:
            # Most recent purchases first
            lot_performance.sort(key=lambda x: x[0].purchase_date, reverse=True)
        elif method == TaxLotMethod.FIFO:
            # Oldest purchases first
            lot_performance.sort(key=lambda x: x[0].purchase_date)
        
        # If targeting specific gains/losses, adjust sorting
        if target_gain_loss == "losses":
            lot_performance.sort(key=lambda x: x[1])  # Biggest losses first
        elif target_gain_loss == "gains":
            lot_performance.sort(key=lambda x: x[1], reverse=True)  # Biggest gains first
        
        # Select lots to meet sales requirement
        selected_lots = []
        remaining_to_sell = sales_needed
        
        for lot, gain_loss, per_share_gl in lot_performance:
            if remaining_to_sell <= 0:
                break
                
            lot_value = lot.quantity * lot.current_price
            if lot_value <= remaining_to_sell:
                # Take entire lot
                selected_lots.append(lot)
                remaining_to_sell -= lot_value
            else:
                # Take partial lot
                shares_needed = remaining_to_sell / lot.current_price
                partial_lot = Investment(
                    symbol=lot.symbol,
                    quantity=shares_needed,
                    purchase_price=lot.purchase_price,
                    purchase_date=lot.purchase_date,
                    current_price=lot.current_price,
                    account_type=lot.account_type,
                    tax_lot_id=f"{lot.tax_lot_id}_partial"
                )
                selected_lots.append(partial_lot)
                remaining_to_sell = Decimal('0')
        
        return selected_lots

    def recommend_asset_location(self, portfolio: Dict[str, Any],
                               tax_rate_info: Dict[str, Decimal]) -> List[AssetLocationRecommendation]:
        """Recommend optimal asset location across account types"""
        recommendations = []
        
        # Asset location rules based on tax efficiency
        asset_location_rules = {
            'bonds': {
                'preferred_accounts': [AccountType.TRADITIONAL_IRA, AccountType.TRADITIONAL_401K],
                'reason': 'Interest income taxed as ordinary income - shield from current taxes',
                'tax_inefficiency_score': 0.9
            },
            'reits': {
                'preferred_accounts': [AccountType.TRADITIONAL_IRA, AccountType.TRADITIONAL_401K],
                'reason': 'Dividend income often taxed as ordinary income',
                'tax_inefficiency_score': 0.8
            },
            'growth_stocks': {
                'preferred_accounts': [AccountType.TAXABLE, AccountType.ROTH_IRA],
                'reason': 'Long-term capital gains and step-up in basis benefits',
                'tax_inefficiency_score': 0.3
            },
            'dividend_stocks': {
                'preferred_accounts': [AccountType.TAXABLE],
                'reason': 'Qualified dividends get preferential tax treatment',
                'tax_inefficiency_score': 0.4
            },
            'international_stocks': {
                'preferred_accounts': [AccountType.TAXABLE],
                'reason': 'Foreign tax credit can be claimed',
                'tax_inefficiency_score': 0.5
            },
            'commodities': {
                'preferred_accounts': [AccountType.TRADITIONAL_IRA, AccountType.TRADITIONAL_401K],
                'reason': 'Often generate ordinary income or unfavorable tax treatment',
                'tax_inefficiency_score': 0.8
            }
        }
        
        marginal_rate = tax_rate_info.get('marginal_rate', Decimal('0.24'))
        
        for asset_class, current_allocation in portfolio.items():
            if asset_class in asset_location_rules:
                rule = asset_location_rules[asset_class]
                current_account = current_allocation.get('account_type')
                
                if current_account not in rule['preferred_accounts']:
                    # Calculate potential tax savings
                    current_value = current_allocation.get('value', Decimal('0'))
                    annual_income_estimate = current_value * Decimal('0.05')  # Assume 5% annual income
                    
                    tax_savings = annual_income_estimate * marginal_rate * rule['tax_inefficiency_score']
                    
                    recommendation = AssetLocationRecommendation(
                        asset_class=asset_class,
                        recommended_account=rule['preferred_accounts'][0],
                        current_account=current_account,
                        tax_efficiency_score=1.0 - rule['tax_inefficiency_score'],
                        reason=rule['reason'],
                        potential_annual_savings=tax_savings
                    )
                    recommendations.append(recommendation)
        
        # Sort by potential savings
        recommendations.sort(key=lambda x: x.potential_annual_savings, reverse=True)
        return recommendations

    def calculate_municipal_bond_advantage(self, yield_municipal: Decimal,
                                         yield_taxable: Decimal,
                                         marginal_tax_rate: Decimal,
                                         state_tax_rate: Decimal = Decimal('0'),
                                         is_in_state: bool = False) -> Dict[str, Any]:
        """Calculate municipal bond tax advantage"""
        # Tax-equivalent yield calculation
        effective_tax_rate = marginal_tax_rate
        if is_in_state:
            effective_tax_rate += state_tax_rate
        
        tax_equivalent_yield = yield_municipal / (1 - effective_tax_rate)
        
        advantage = tax_equivalent_yield - yield_taxable
        advantage_percentage = (advantage / yield_taxable) * 100 if yield_taxable > 0 else 0
        
        return {
            'municipal_yield': float(yield_municipal),
            'taxable_yield': float(yield_taxable),
            'tax_equivalent_yield': float(tax_equivalent_yield),
            'advantage_bps': float(advantage * 10000),  # Basis points
            'advantage_percentage': float(advantage_percentage),
            'recommendation': 'Municipal bonds' if advantage > 0 else 'Taxable bonds',
            'break_even_tax_rate': float(1 - (yield_municipal / yield_taxable)) if yield_taxable > 0 else 0
        }

    def optimize_capital_gains_timing(self, investments: List[Investment],
                                    current_income: Decimal, filing_status: FilingStatus,
                                    target_realization: Decimal) -> Dict[str, Any]:
        """Optimize timing of capital gains realization"""
        current_year = datetime.now().year
        
        # Calculate current tax situation
        current_marginal_rate = self.calculate_marginal_tax_rate(current_income, filing_status)
        
        short_term_opportunities = []
        long_term_opportunities = []
        
        for investment in investments:
            if investment.account_type != AccountType.TAXABLE:
                continue
            
            holding_days = (datetime.now() - investment.purchase_date).days
            current_value = investment.quantity * investment.current_price
            cost_basis = investment.quantity * investment.purchase_price
            unrealized_gain = current_value - cost_basis
            
            if unrealized_gain > 0:
                if holding_days <= 365:
                    days_to_long_term = 366 - holding_days
                    short_term_tax = unrealized_gain * current_marginal_rate
                    long_term_tax = unrealized_gain * self.calculate_capital_gains_rate(
                        current_income, filing_status, 366
                    )
                    tax_savings_by_waiting = short_term_tax - long_term_tax
                    
                    short_term_opportunities.append({
                        'investment': investment,
                        'unrealized_gain': unrealized_gain,
                        'days_to_long_term': days_to_long_term,
                        'tax_savings_by_waiting': tax_savings_by_waiting,
                        'short_term_tax': short_term_tax,
                        'long_term_tax': long_term_tax
                    })
                else:
                    long_term_tax = unrealized_gain * self.calculate_capital_gains_rate(
                        current_income, filing_status, holding_days
                    )
                    
                    long_term_opportunities.append({
                        'investment': investment,
                        'unrealized_gain': unrealized_gain,
                        'long_term_tax': long_term_tax,
                        'holding_days': holding_days
                    })
        
        # Sort opportunities
        short_term_opportunities.sort(key=lambda x: x['tax_savings_by_waiting'], reverse=True)
        long_term_opportunities.sort(key=lambda x: x['long_term_tax'])
        
        return {
            'short_term_opportunities': short_term_opportunities,
            'long_term_opportunities': long_term_opportunities,
            'current_marginal_rate': float(current_marginal_rate),
            'recommendations': self._generate_timing_recommendations(
                short_term_opportunities, long_term_opportunities, target_realization
            )
        }

    def _generate_timing_recommendations(self, short_term: List[Dict],
                                       long_term: List[Dict],
                                       target: Decimal) -> List[str]:
        """Generate capital gains timing recommendations"""
        recommendations = []
        
        if not short_term and not long_term:
            return ["No unrealized gains available for realization"]
        
        # Prioritize long-term gains for immediate realization
        total_long_term_available = sum(op['unrealized_gain'] for op in long_term)
        
        if total_long_term_available >= target:
            recommendations.append(f"Realize ${target:,.2f} from long-term gains to minimize tax impact")
            
            # Identify specific holdings to sell
            running_total = Decimal('0')
            for opportunity in long_term:
                if running_total >= target:
                    break
                needed = min(opportunity['unrealized_gain'], target - running_total)
                recommendations.append(
                    f"Consider selling {opportunity['investment'].symbol} "
                    f"for ${needed:,.2f} in long-term gains"
                )
                running_total += needed
        else:
            if total_long_term_available > 0:
                recommendations.append(f"Realize all ${total_long_term_available:,.2f} in long-term gains first")
            
            remaining_needed = target - total_long_term_available
            recommendations.append(f"Need ${remaining_needed:,.2f} more in gains")
            
            # Check if waiting would be beneficial for short-term holdings
            for opportunity in short_term:
                if opportunity['days_to_long_term'] <= 60:  # Less than 2 months
                    savings = opportunity['tax_savings_by_waiting']
                    recommendations.append(
                        f"Consider waiting {opportunity['days_to_long_term']} days "
                        f"to save ${savings:,.2f} in taxes on {opportunity['investment'].symbol}"
                    )
        
        return recommendations

    def calculate_year_end_tax_estimate(self, financial_data: Dict[str, Any],
                                      filing_status: FilingStatus) -> Dict[str, Any]:
        """Calculate year-end tax liability estimate"""
        # Extract key financial data
        ordinary_income = financial_data.get('ordinary_income', Decimal('0'))
        short_term_gains = financial_data.get('short_term_capital_gains', Decimal('0'))
        long_term_gains = financial_data.get('long_term_capital_gains', Decimal('0'))
        qualified_dividends = financial_data.get('qualified_dividends', Decimal('0'))
        ordinary_dividends = financial_data.get('ordinary_dividends', Decimal('0'))
        interest_income = financial_data.get('interest_income', Decimal('0'))
        
        # Standard deduction for 2025 (estimated)
        standard_deductions = {
            FilingStatus.SINGLE: Decimal('14600'),
            FilingStatus.MARRIED_JOINT: Decimal('29200'),
            FilingStatus.MARRIED_SEPARATE: Decimal('14600'),
            FilingStatus.HEAD_OF_HOUSEHOLD: Decimal('21900')
        }
        
        standard_deduction = standard_deductions[filing_status]
        itemized_deductions = financial_data.get('itemized_deductions', Decimal('0'))
        deductions = max(standard_deduction, itemized_deductions)
        
        # Calculate adjusted gross income
        agi = (ordinary_income + short_term_gains + long_term_gains + 
               qualified_dividends + ordinary_dividends + interest_income)
        
        # Calculate taxable income
        taxable_income = max(Decimal('0'), agi - deductions)
        
        # Calculate ordinary income tax
        ordinary_taxable_income = (ordinary_income + short_term_gains + 
                                 ordinary_dividends + interest_income - deductions)
        ordinary_taxable_income = max(Decimal('0'), ordinary_taxable_income)
        
        ordinary_tax = self._calculate_tax_from_brackets(
            ordinary_taxable_income, self.TAX_BRACKETS_2025[filing_status]
        )
        
        # Calculate capital gains tax
        cap_gains_tax = long_term_gains * self.calculate_capital_gains_rate(
            agi, filing_status, 366  # Long-term
        )
        
        # Calculate qualified dividends tax (same rates as long-term capital gains)
        qualified_div_tax = qualified_dividends * self.calculate_capital_gains_rate(
            agi, filing_status, 366
        )
        
        total_tax = ordinary_tax + cap_gains_tax + qualified_div_tax
        
        # Estimate quarterly payments and withholding
        estimated_payments = financial_data.get('estimated_payments_ytd', Decimal('0'))
        withholding = financial_data.get('withholding_ytd', Decimal('0'))
        total_payments = estimated_payments + withholding
        
        # Calculate balance due or refund
        balance_due = total_tax - total_payments
        
        return {
            'agi': float(agi),
            'taxable_income': float(taxable_income),
            'deductions_used': float(deductions),
            'using_standard_deduction': deductions == standard_deduction,
            'ordinary_tax': float(ordinary_tax),
            'capital_gains_tax': float(cap_gains_tax),
            'qualified_dividends_tax': float(qualified_div_tax),
            'total_tax_liability': float(total_tax),
            'total_payments_made': float(total_payments),
            'balance_due_or_refund': float(balance_due),
            'effective_tax_rate': float(total_tax / agi * 100) if agi > 0 else 0,
            'marginal_tax_rate': float(self.calculate_marginal_tax_rate(agi, filing_status) * 100),
            'recommendations': self._generate_year_end_recommendations(
                balance_due, agi, filing_status, financial_data
            )
        }

    def _calculate_tax_from_brackets(self, income: Decimal, brackets: List[TaxBracket]) -> Decimal:
        """Calculate tax owed using bracket system"""
        total_tax = Decimal('0')
        remaining_income = income
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
                
            bracket_width = (bracket.max_income or income) - bracket.min_income
            taxable_in_bracket = min(remaining_income, bracket_width)
            
            if taxable_in_bracket > 0:
                total_tax += taxable_in_bracket * bracket.rate
                remaining_income -= taxable_in_bracket
        
        return total_tax

    def _generate_year_end_recommendations(self, balance_due: Decimal, agi: Decimal,
                                         filing_status: FilingStatus,
                                         financial_data: Dict[str, Any]) -> List[str]:
        """Generate year-end tax planning recommendations"""
        recommendations = []
        
        if balance_due > Decimal('1000'):
            recommendations.append(
                f"Consider making estimated tax payment of ${balance_due:,.2f} "
                "to avoid underpayment penalty"
            )
        
        # Roth conversion opportunity
        current_bracket = None
        brackets = self.TAX_BRACKETS_2025[filing_status]
        for bracket in brackets:
            if bracket.max_income is None or agi <= bracket.max_income:
                current_bracket = bracket
                break
        
        if current_bracket and current_bracket.max_income:
            room_in_bracket = current_bracket.max_income - agi
            if room_in_bracket > Decimal('5000'):
                recommendations.append(
                    f"Consider Roth conversion of up to ${room_in_bracket:,.2f} "
                    f"while staying in {float(current_bracket.rate * 100):.1f}% bracket"
                )
        
        # Charitable giving bunching strategy
        charitable_deductions = financial_data.get('charitable_deductions', Decimal('0'))
        standard_deduction = self._get_standard_deduction(filing_status)
        
        if charitable_deductions > Decimal('0') and charitable_deductions < standard_deduction * Decimal('0.5'):
            recommendations.append(
                "Consider bunching charitable donations in alternating years "
                "to exceed standard deduction threshold"
            )
        
        # Tax-loss harvesting reminder
        unrealized_losses = financial_data.get('unrealized_losses_available', Decimal('0'))
        if unrealized_losses > Decimal('3000'):
            recommendations.append(
                f"Consider harvesting up to ${unrealized_losses:,.2f} in tax losses "
                "before year-end"
            )
        
        return recommendations

    def _get_standard_deduction(self, filing_status: FilingStatus) -> Decimal:
        """Get standard deduction amount"""
        deductions = {
            FilingStatus.SINGLE: Decimal('14600'),
            FilingStatus.MARRIED_JOINT: Decimal('29200'),
            FilingStatus.MARRIED_SEPARATE: Decimal('14600'),
            FilingStatus.HEAD_OF_HOUSEHOLD: Decimal('21900')
        }
        return deductions[filing_status]

    def optimize_roth_conversions(self, current_income: Decimal, filing_status: FilingStatus,
                                traditional_ira_balance: Decimal,
                                years_to_retirement: int,
                                expected_retirement_income: Decimal) -> Dict[str, Any]:
        """Optimize Roth conversion strategy"""
        current_bracket_info = self._get_current_tax_bracket(current_income, filing_status)
        retirement_bracket_info = self._get_current_tax_bracket(expected_retirement_income, filing_status)
        
        current_rate = current_bracket_info['rate']
        retirement_rate = retirement_bracket_info['rate']
        
        # Calculate room in current bracket
        room_in_current_bracket = Decimal('0')
        if current_bracket_info['max_income']:
            room_in_current_bracket = current_bracket_info['max_income'] - current_income
        
        # Optimal conversion strategy
        if current_rate < retirement_rate:
            # Convert aggressively - will be in higher bracket later
            recommended_conversion = min(
                room_in_current_bracket,
                traditional_ira_balance / max(1, years_to_retirement)
            )
            strategy = "Aggressive conversion - currently in lower bracket"
        elif current_rate > retirement_rate:
            # Convert conservatively - will be in lower bracket later
            recommended_conversion = min(
                room_in_current_bracket * Decimal('0.5'),
                traditional_ira_balance / max(1, years_to_retirement * 2)
            )
            strategy = "Conservative conversion - will be in lower bracket in retirement"
        else:
            # Same bracket - moderate conversion
            recommended_conversion = min(
                room_in_current_bracket * Decimal('0.7'),
                traditional_ira_balance / max(1, years_to_retirement)
            )
            strategy = "Moderate conversion - same tax bracket expected"
        
        # Calculate tax cost and long-term savings
        conversion_tax_cost = recommended_conversion * current_rate
        
        # Estimate future tax savings (simplified model)
        future_withdrawals = traditional_ira_balance
        future_tax_if_not_converted = future_withdrawals * retirement_rate
        future_tax_after_conversion = (traditional_ira_balance - recommended_conversion) * retirement_rate
        estimated_long_term_savings = future_tax_if_not_converted - future_tax_after_conversion - conversion_tax_cost
        
        return {
            'recommended_conversion_amount': float(recommended_conversion),
            'conversion_tax_cost': float(conversion_tax_cost),
            'current_tax_rate': float(current_rate * 100),
            'expected_retirement_tax_rate': float(retirement_rate * 100),
            'room_in_current_bracket': float(room_in_current_bracket),
            'strategy': strategy,
            'estimated_long_term_savings': float(estimated_long_term_savings),
            'break_even_years': int(conversion_tax_cost / max(Decimal('100'), (retirement_rate - current_rate) * recommended_conversion)) if retirement_rate != current_rate else None,
            'recommendations': [
                f"Convert ${recommended_conversion:,.2f} to Roth IRA",
                f"Tax cost: ${conversion_tax_cost:,.2f}",
                f"Strategy: {strategy}"
            ]
        }

    def _get_current_tax_bracket(self, income: Decimal, filing_status: FilingStatus) -> Dict[str, Any]:
        """Get current tax bracket information"""
        brackets = self.TAX_BRACKETS_2025[filing_status]
        
        for bracket in brackets:
            if bracket.max_income is None or income <= bracket.max_income:
                return {
                    'min_income': float(bracket.min_income),
                    'max_income': float(bracket.max_income) if bracket.max_income else None,
                    'rate': bracket.rate
                }
        
        return {
            'min_income': float(brackets[-1].min_income),
            'max_income': None,
            'rate': brackets[-1].rate
        }

    def analyze_state_tax_benefits(self, current_state: str, 
                                 financial_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze state-specific tax benefits and planning opportunities"""
        current_state_rate = self.STATE_TAX_RATES.get(current_state, Decimal('0.05'))
        
        # 529 Plan state tax benefits (simplified)
        state_529_benefits = {
            'NY': {'deduction_limit': 10000, 'description': 'Up to $10,000 deduction for NY 529 contributions'},
            'VA': {'deduction_limit': 4000, 'description': 'Up to $4,000 deduction per account'},
            'IN': {'credit_rate': 0.20, 'description': '20% tax credit up to $1,000'},
            'CO': {'deduction_unlimited': True, 'description': 'Unlimited deduction for CO 529 contributions'},
        }
        
        # State retirement tax treatment
        retirement_tax_treatment = {
            'FL': 'No state tax on retirement income',
            'TX': 'No state tax on retirement income',
            'WA': 'No state tax on retirement income',
            'NV': 'No state tax on retirement income',
            'TN': 'No state tax on retirement income',
            'PA': 'No tax on retirement account distributions',
            'MS': 'Retirement income partially exempt',
            'IL': 'Retirement income exempt'
        }
        
        analysis = {
            'current_state': current_state,
            'current_state_tax_rate': float(current_state_rate),
            'annual_state_tax_estimate': float(
                financial_profile.get('agi', Decimal('0')) * current_state_rate
            ),
            'state_529_benefits': state_529_benefits.get(current_state, {}),
            'retirement_tax_treatment': retirement_tax_treatment.get(
                current_state, 'Standard state tax applies to retirement income'
            ),
            'tax_friendly_alternatives': [],
            'recommendations': []
        }
        
        # Identify tax-friendly states
        no_tax_states = ['FL', 'TX', 'WA', 'NV', 'TN', 'NH', 'WY', 'AK', 'SD']
        if current_state not in no_tax_states:
            analysis['tax_friendly_alternatives'] = [
                {
                    'state': state,
                    'annual_savings': float(financial_profile.get('agi', Decimal('0')) * current_state_rate),
                    'description': f'No state income tax - potential annual savings'
                }
                for state in no_tax_states[:3]  # Top 3 recommendations
            ]
        
        # Generate recommendations
        if current_state_rate > Decimal('0.05'):
            analysis['recommendations'].append(
                f"High state tax rate ({float(current_state_rate * 100):.1f}%) - "
                "consider tax-loss harvesting and municipal bonds"
            )
        
        if current_state in state_529_benefits:
            analysis['recommendations'].append(
                f"Take advantage of state 529 tax benefits: {state_529_benefits[current_state]['description']}"
            )
        
        return analysis

    def calculate_charitable_giving_strategies(self, income: Decimal, filing_status: FilingStatus,
                                             charitable_intent: Decimal,
                                             appreciated_assets: Optional[List[Investment]] = None) -> Dict[str, Any]:
        """Calculate optimal charitable giving strategies"""
        standard_deduction = self._get_standard_deduction(filing_status)
        marginal_rate = self.calculate_marginal_tax_rate(income, filing_status)
        
        strategies = {}
        
        # Strategy 1: Annual giving with standard deduction
        annual_tax_benefit = min(charitable_intent, 
                               max(Decimal('0'), charitable_intent - standard_deduction)) * marginal_rate
        
        strategies['annual_giving'] = {
            'charitable_amount': float(charitable_intent),
            'tax_benefit': float(annual_tax_benefit),
            'effective_cost': float(charitable_intent - annual_tax_benefit),
            'description': 'Give annually and itemize deductions'
        }
        
        # Strategy 2: Bunching donations
        two_year_intent = charitable_intent * 2
        bunching_benefit_year1 = max(Decimal('0'), two_year_intent - standard_deduction) * marginal_rate
        bunching_benefit_year2 = Decimal('0')  # Take standard deduction
        total_bunching_benefit = bunching_benefit_year1 + bunching_benefit_year2
        
        strategies['bunching'] = {
            'charitable_amount': float(two_year_intent),
            'tax_benefit_two_years': float(total_bunching_benefit),
            'effective_cost_two_years': float(two_year_intent - total_bunching_benefit),
            'annual_tax_benefit_equivalent': float(total_bunching_benefit / 2),
            'description': 'Bunch two years of donations in one year'
        }
        
        # Strategy 3: Donor Advised Fund
        daf_contribution = charitable_intent * Decimal('5')  # Fund 5 years at once
        daf_immediate_deduction = min(
            daf_contribution,
            income * Decimal('0.5')  # 50% of AGI limit for cash
        )
        daf_tax_benefit = daf_immediate_deduction * marginal_rate
        
        strategies['donor_advised_fund'] = {
            'initial_contribution': float(daf_contribution),
            'immediate_deduction': float(daf_immediate_deduction),
            'immediate_tax_benefit': float(daf_tax_benefit),
            'years_of_giving_funded': 5,
            'description': 'Fund multiple years of giving upfront with immediate deduction'
        }
        
        # Strategy 4: Appreciated asset donation (if assets provided)
        if appreciated_assets:
            best_asset = max(appreciated_assets, 
                           key=lambda x: (x.current_price - x.purchase_price) * x.quantity)
            
            asset_value = best_asset.current_price * min(
                best_asset.quantity, 
                charitable_intent / best_asset.current_price
            )
            cost_basis = best_asset.purchase_price * min(
                best_asset.quantity,
                charitable_intent / best_asset.current_price
            )
            
            # Benefits: deduction + avoided capital gains tax
            deduction_benefit = asset_value * marginal_rate
            avoided_cap_gains = (asset_value - cost_basis) * self.calculate_capital_gains_rate(
                income, filing_status, (datetime.now() - best_asset.purchase_date).days
            )
            
            total_benefit = deduction_benefit + avoided_cap_gains
            
            strategies['appreciated_assets'] = {
                'asset_symbol': best_asset.symbol,
                'asset_value': float(asset_value),
                'cost_basis': float(cost_basis),
                'deduction_benefit': float(deduction_benefit),
                'avoided_capital_gains_tax': float(avoided_cap_gains),
                'total_tax_benefit': float(total_benefit),
                'effective_cost': float(cost_basis),  # Only out original investment
                'description': 'Donate appreciated assets to avoid capital gains'
            }
        
        # Determine optimal strategy
        if appreciated_assets and 'appreciated_assets' in strategies:
            optimal_strategy = 'appreciated_assets'
        elif strategies['bunching']['annual_tax_benefit_equivalent'] > strategies['annual_giving']['tax_benefit']:
            optimal_strategy = 'bunching'
        elif daf_contribution <= income * Decimal('0.5'):
            optimal_strategy = 'donor_advised_fund'
        else:
            optimal_strategy = 'annual_giving'
        
        return {
            'strategies': strategies,
            'optimal_strategy': optimal_strategy,
            'optimal_description': strategies[optimal_strategy]['description'],
            'recommendations': [
                f"Optimal strategy: {strategies[optimal_strategy]['description']}",
                "Consider timing donations for maximum tax benefit",
                "Evaluate appreciated assets for donation before selling"
            ]
        }

    def calculate_business_expense_optimization(self, business_income: Decimal,
                                             business_expenses: Dict[str, Decimal],
                                             filing_status: FilingStatus) -> Dict[str, Any]:
        """Optimize business expense strategies for self-employed individuals"""
        
        # Self-employment tax rate (Social Security + Medicare)
        se_tax_rate = Decimal('0.1413')  # 2025 rate
        marginal_income_rate = self.calculate_marginal_tax_rate(business_income, filing_status)
        
        # Total marginal rate including self-employment tax
        total_marginal_rate = marginal_income_rate + se_tax_rate
        
        current_total_expenses = sum(business_expenses.values())
        
        optimization_opportunities = []
        
        # Home office deduction
        if 'home_office' not in business_expenses or business_expenses.get('home_office', 0) == 0:
            # Simplified method: $5 per square foot, up to 300 sq ft
            estimated_home_office_deduction = Decimal('1500')  # 300 sq ft * $5
            tax_savings = estimated_home_office_deduction * total_marginal_rate
            
            optimization_opportunities.append({
                'category': 'Home Office Deduction',
                'potential_deduction': float(estimated_home_office_deduction),
                'tax_savings': float(tax_savings),
                'description': 'Simplified home office deduction ($5/sq ft, max 300 sq ft)',
                'requirements': 'Regular and exclusive business use of home space'
            })
        
        # Vehicle expenses
        current_vehicle = business_expenses.get('vehicle', Decimal('0'))
        if current_vehicle < business_income * Decimal('0.1'):  # Less than 10% of income
            # Standard mileage rate for 2025 (estimated)
            standard_mileage_rate = Decimal('0.67')
            estimated_business_miles = Decimal('10000')  # Conservative estimate
            potential_vehicle_deduction = estimated_business_miles * standard_mileage_rate
            additional_deduction = potential_vehicle_deduction - current_vehicle
            
            if additional_deduction > 0:
                tax_savings = additional_deduction * total_marginal_rate
                optimization_opportunities.append({
                    'category': 'Vehicle Expenses',
                    'current_deduction': float(current_vehicle),
                    'potential_deduction': float(potential_vehicle_deduction),
                    'additional_deduction': float(additional_deduction),
                    'tax_savings': float(tax_savings),
                    'description': f'Track business mileage (${float(standard_mileage_rate)}/mile)',
                    'requirements': 'Detailed mileage log required'
                })
        
        # Equipment depreciation/Section 179
        equipment_expense = business_expenses.get('equipment', Decimal('0'))
        if equipment_expense > 0:
            # Section 179 allows immediate deduction up to $1,160,000 in 2025
            section_179_limit = Decimal('1160000')
            immediate_deduction_benefit = min(equipment_expense, section_179_limit)
            
            optimization_opportunities.append({
                'category': 'Equipment Deduction',
                'strategy': 'Section 179 Election',
                'immediate_deduction': float(immediate_deduction_benefit),
                'vs_depreciation': 'Immediate vs. spread over several years',
                'description': 'Elect Section 179 for immediate equipment deduction',
                'requirements': 'Equipment must be used >50% for business'
            })
        
        # Professional development
        training_expense = business_expenses.get('training', Decimal('0'))
        estimated_optimal_training = business_income * Decimal('0.02')  # 2% of income
        if training_expense < estimated_optimal_training:
            additional_training_opportunity = estimated_optimal_training - training_expense
            tax_savings = additional_training_opportunity * total_marginal_rate
            
            optimization_opportunities.append({
                'category': 'Professional Development',
                'current_expense': float(training_expense),
                'recommended_expense': float(estimated_optimal_training),
                'additional_opportunity': float(additional_training_opportunity),
                'tax_savings': float(tax_savings),
                'description': 'Invest in business-related training and education',
                'requirements': 'Training must be business-related'
            })
        
        # Retirement contributions
        # SEP-IRA contribution limit: 25% of compensation or $69,000 (2025 limit)
        sep_ira_limit = min(business_income * Decimal('0.25'), Decimal('69000'))
        current_retirement = business_expenses.get('retirement_contribution', Decimal('0'))
        
        if current_retirement < sep_ira_limit:
            additional_contribution = sep_ira_limit - current_retirement
            tax_savings = additional_contribution * total_marginal_rate
            
            optimization_opportunities.append({
                'category': 'Retirement Contributions',
                'current_contribution': float(current_retirement),
                'maximum_contribution': float(sep_ira_limit),
                'additional_opportunity': float(additional_contribution),
                'tax_savings': float(tax_savings),
                'description': 'Maximize SEP-IRA contributions',
                'requirements': 'Must have self-employment income'
            })
        
        # Calculate total optimization potential
        total_additional_deductions = sum(
            opp.get('additional_deduction', opp.get('additional_opportunity', 0))
            for opp in optimization_opportunities
        )
        total_tax_savings = sum(opp['tax_savings'] for opp in optimization_opportunities)
        
        return {
            'business_income': float(business_income),
            'current_total_expenses': float(current_total_expenses),
            'marginal_tax_rate': float(total_marginal_rate * 100),
            'self_employment_tax_rate': float(se_tax_rate * 100),
            'optimization_opportunities': optimization_opportunities,
            'total_additional_deductions_available': float(total_additional_deductions),
            'total_potential_tax_savings': float(total_tax_savings),
            'recommendations': [
                'Track all business expenses meticulously',
                'Consider timing of equipment purchases for optimal tax benefit',
                'Maximize retirement contributions to reduce current tax burden',
                'Maintain detailed records for all business deductions'
            ]
        }

    def generate_comprehensive_tax_report(self, user_financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive tax optimization report"""
        
        # Extract user data
        income = Decimal(str(user_financial_data.get('income', 100000)))
        filing_status = FilingStatus(user_financial_data.get('filing_status', 'SINGLE'))
        state = user_financial_data.get('state', 'CA')
        investments = user_financial_data.get('investments', [])
        
        # Convert investment data if needed
        if investments and isinstance(investments[0], dict):
            investments = [
                Investment(
                    symbol=inv['symbol'],
                    quantity=Decimal(str(inv['quantity'])),
                    purchase_price=Decimal(str(inv['purchase_price'])),
                    purchase_date=datetime.fromisoformat(inv['purchase_date'].replace('Z', '+00:00')),
                    current_price=Decimal(str(inv['current_price'])),
                    account_type=AccountType(inv.get('account_type', 'TAXABLE'))
                )
                for inv in investments
            ]
        
        report = {
            'tax_year': 2025,
            'user_profile': {
                'income': float(income),
                'filing_status': filing_status.value,
                'state': state,
                'marginal_tax_rate': float(self.calculate_marginal_tax_rate(income, filing_status, state) * 100)
            }
        }
        
        # Tax-loss harvesting analysis
        if investments:
            loss_opportunities = self.identify_tax_loss_opportunities(
                investments, income, filing_status
            )
            report['tax_loss_harvesting'] = {
                'opportunities_found': len(loss_opportunities),
                'total_potential_losses': float(sum(opp.unrealized_loss for opp in loss_opportunities)),
                'estimated_tax_savings': float(sum(opp.tax_savings_estimate for opp in loss_opportunities)),
                'top_opportunities': [
                    {
                        'symbol': opp.investment.symbol,
                        'unrealized_loss': float(opp.unrealized_loss),
                        'tax_savings': float(opp.tax_savings_estimate),
                        'recommendation': opp.recommended_action,
                        'wash_sale_warning': opp.wash_sale_warning
                    }
                    for opp in loss_opportunities[:5]
                ]
            }
        
        # Year-end tax estimate
        report['year_end_estimate'] = self.calculate_year_end_tax_estimate(
            user_financial_data, filing_status
        )
        
        # State tax analysis
        report['state_tax_analysis'] = self.analyze_state_tax_benefits(
            state, {'agi': income}
        )
        
        # Asset location recommendations
        if 'portfolio' in user_financial_data:
            asset_recommendations = self.recommend_asset_location(
                user_financial_data['portfolio'],
                {'marginal_rate': self.calculate_marginal_tax_rate(income, filing_status)}
            )
            report['asset_location'] = {
                'recommendations_count': len(asset_recommendations),
                'total_potential_savings': float(sum(rec.potential_annual_savings for rec in asset_recommendations)),
                'top_recommendations': [
                    {
                        'asset_class': rec.asset_class,
                        'current_account': rec.current_account.value,
                        'recommended_account': rec.recommended_account.value,
                        'reason': rec.reason,
                        'potential_savings': float(rec.potential_annual_savings)
                    }
                    for rec in asset_recommendations[:3]
                ]
            }
        
        # Roth conversion analysis
        traditional_ira_balance = Decimal(str(user_financial_data.get('traditional_ira_balance', 100000)))
        years_to_retirement = user_financial_data.get('years_to_retirement', 20)
        expected_retirement_income = Decimal(str(user_financial_data.get('expected_retirement_income', income * Decimal('0.8'))))
        
        roth_analysis = self.optimize_roth_conversions(
            income, filing_status, traditional_ira_balance, 
            years_to_retirement, expected_retirement_income
        )
        report['roth_conversion_analysis'] = roth_analysis
        
        # Business expense optimization (if applicable)
        if user_financial_data.get('is_self_employed', False):
            business_income = Decimal(str(user_financial_data.get('business_income', income)))
            business_expenses = {
                k: Decimal(str(v)) for k, v in user_financial_data.get('business_expenses', {}).items()
            }
            
            business_optimization = self.calculate_business_expense_optimization(
                business_income, business_expenses, filing_status
            )
            report['business_expense_optimization'] = business_optimization
        
        # Overall recommendations
        total_potential_savings = 0
        top_recommendations = []
        
        if 'tax_loss_harvesting' in report:
            total_potential_savings += report['tax_loss_harvesting']['estimated_tax_savings']
            top_recommendations.append("Implement tax-loss harvesting strategy")
        
        if 'asset_location' in report:
            total_potential_savings += report['asset_location']['total_potential_savings']
            top_recommendations.append("Optimize asset location across account types")
        
        if roth_analysis['estimated_long_term_savings'] > 0:
            total_potential_savings += roth_analysis['estimated_long_term_savings']
            top_recommendations.append("Consider Roth conversion strategy")
        
        report['summary'] = {
            'total_estimated_annual_tax_savings': total_potential_savings,
            'top_recommendations': top_recommendations,
            'next_steps': [
                "Review tax-loss harvesting opportunities before year-end",
                "Optimize asset location in tax-advantaged accounts",
                "Consider Roth conversion based on current vs future tax rates",
                "Maximize tax-deductible retirement contributions"
            ]
        }
        
        return report


# Example usage and testing functions
def create_sample_investments() -> List[Investment]:
    """Create sample investments for testing"""
    return [
        Investment(
            symbol="AAPL",
            quantity=Decimal('100'),
            purchase_price=Decimal('150.00'),
            purchase_date=datetime(2023, 1, 15),
            current_price=Decimal('140.00'),
            account_type=AccountType.TAXABLE
        ),
        Investment(
            symbol="TSLA",
            quantity=Decimal('50'),
            purchase_price=Decimal('200.00'),
            purchase_date=datetime(2024, 6, 1),
            current_price=Decimal('180.00'),
            account_type=AccountType.TAXABLE
        ),
        Investment(
            symbol="VTI",
            quantity=Decimal('200'),
            purchase_price=Decimal('200.00'),
            purchase_date=datetime(2022, 3, 10),
            current_price=Decimal('220.00'),
            account_type=AccountType.ROTH_IRA
        )
    ]


def run_tax_optimization_example():
    """Run example tax optimization analysis"""
    service = TaxOptimizationService()
    
    # Sample data
    income = Decimal('150000')
    filing_status = FilingStatus.SINGLE
    investments = create_sample_investments()
    
    print("Tax Optimization Analysis Example")
    print("=" * 50)
    
    # Tax-loss harvesting
    print("\n1. Tax-Loss Harvesting Opportunities:")
    opportunities = service.identify_tax_loss_opportunities(
        investments, income, filing_status
    )
    
    for opp in opportunities:
        print(f"  {opp.investment.symbol}: ${opp.unrealized_loss:.2f} loss, "
              f"${opp.tax_savings_estimate:.2f} tax savings")
        print(f"    Recommendation: {opp.recommended_action}")
    
    # Municipal bond analysis
    print("\n2. Municipal Bond Analysis:")
    muni_analysis = service.calculate_municipal_bond_advantage(
        yield_municipal=Decimal('0.035'),
        yield_taxable=Decimal('0.045'),
        marginal_tax_rate=service.calculate_marginal_tax_rate(income, filing_status),
        state_tax_rate=Decimal('0.10'),
        is_in_state=True
    )
    print(f"  Tax-equivalent yield: {muni_analysis['tax_equivalent_yield']:.2%}")
    print(f"  Recommendation: {muni_analysis['recommendation']}")
    
    # Year-end tax estimate
    print("\n3. Year-End Tax Estimate:")
    financial_data = {
        'ordinary_income': income,
        'short_term_capital_gains': Decimal('5000'),
        'long_term_capital_gains': Decimal('10000'),
        'qualified_dividends': Decimal('2000')
    }
    
    tax_estimate = service.calculate_year_end_tax_estimate(financial_data, filing_status)
    print(f"  Estimated total tax: ${tax_estimate['total_tax_liability']:,.2f}")
    print(f"  Effective tax rate: {tax_estimate['effective_tax_rate']:.1f}%")
    print(f"  Balance due/refund: ${tax_estimate['balance_due_or_refund']:,.2f}")


if __name__ == "__main__":
    run_tax_optimization_example()
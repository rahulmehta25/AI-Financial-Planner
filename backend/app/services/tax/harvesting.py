"""
Tax-Loss Harvesting Engine with Wash Sale Compliance

Implements sophisticated tax-loss harvesting strategies including:
- Wash sale rule compliance (30-day rule)
- Substitute security selection
- Gain/loss optimization
- Tax lot management
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, date, timedelta
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...models.tax_accounts import (
    TaxAccount, TaxAccountHolding, TaxAccountTransaction, 
    TaxLossHarvestingOpportunity, AccountTypeEnum, TaxTreatmentEnum
)
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


@dataclass
class SecurityProfile:
    """Profile of a security for harvesting analysis"""
    symbol: str
    name: str
    asset_class: str
    sector: str
    market_cap: str
    correlation_with_market: float
    expense_ratio: Optional[float] = None
    dividend_yield: float = 0.0
    beta: float = 1.0


@dataclass
class WashSaleRule:
    """Wash sale rule parameters and checks"""
    lookback_days: int = 30
    lookforward_days: int = 30
    substantially_identical_threshold: float = 0.95  # Correlation threshold
    
    def is_wash_sale_safe(
        self,
        symbol: str,
        sell_date: datetime,
        transactions: List[TaxAccountTransaction]
    ) -> bool:
        """Check if selling is safe from wash sale rules"""
        
        # Check lookback period
        lookback_start = sell_date - timedelta(days=self.lookback_days)
        
        recent_purchases = [
            txn for txn in transactions
            if (txn.symbol == symbol and 
                txn.transaction_type == 'buy' and
                lookback_start <= txn.transaction_date <= sell_date)
        ]
        
        return len(recent_purchases) == 0


@dataclass
class HarvestingOpportunity:
    """Detailed tax-loss harvesting opportunity"""
    holding: TaxAccountHolding
    unrealized_loss: Decimal
    tax_benefit: Decimal
    wash_sale_safe: bool
    replacement_securities: List[SecurityProfile]
    optimal_replacement: Optional[SecurityProfile]
    implementation_steps: List[Dict]
    confidence_score: float
    risk_factors: List[str] = field(default_factory=list)


@dataclass
class HarvestingStrategy:
    """Complete harvesting strategy for a user"""
    opportunities: List[HarvestingOpportunity]
    total_harvestable_losses: Decimal
    total_tax_benefit: Decimal
    annual_loss_capacity: Decimal  # $3,000 ordinary income offset limit
    carryforward_losses: Decimal
    implementation_timeline: List[Dict]
    monitoring_schedule: List[Dict]


class TaxLossHarvestingEngine:
    """
    Advanced tax-loss harvesting engine with wash sale compliance
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.wash_sale_rule = WashSaleRule()
        
        # Security replacement database (simplified - would be more extensive)
        self.replacement_mapping = {
            # Large Cap US Equity
            'SPY': ['VTI', 'ITOT', 'SPTM'],  # S&P 500 alternatives
            'VTI': ['SPY', 'ITOT', 'SPTM'],
            'VOO': ['SPY', 'VTI', 'ITOT'],
            
            # International Equity
            'VEA': ['IEFA', 'VTEB', 'SCHF'],  # Developed markets
            'VWO': ['IEMG', 'SCHE', 'SPEM'],  # Emerging markets
            
            # Fixed Income
            'BND': ['AGG', 'SCHZ', 'IUSB'],  # Total bond market
            'AGG': ['BND', 'SCHZ', 'IUSB'],
            'TLT': ['EDV', 'VGLT', 'SPTL'],  # Long-term treasuries
            
            # Sector ETFs
            'XLK': ['VGT', 'FTEC', 'IYW'],  # Technology
            'XLF': ['VFH', 'FREL', 'IYF'],  # Financials
            'XLE': ['VDE', 'FENY', 'IYE'],  # Energy
            
            # Small Cap
            'IWM': ['VB', 'VTWO', 'SCHA'],   # Russell 2000
            'VB': ['IWM', 'VTWO', 'SCHA'],
            
            # REITs
            'VNQ': ['SCHH', 'IYR', 'FREL'],
            'IYR': ['VNQ', 'SCHH', 'FREL']
        }
        
        # Minimum thresholds
        self.min_loss_threshold = Decimal('500')  # Minimum loss to consider
        self.min_position_size = Decimal('1000')  # Minimum position size
        
    async def analyze_harvesting_opportunities(
        self,
        user_id: str,
        current_market_prices: Dict[str, float],
        tax_situation: Optional[Dict] = None
    ) -> HarvestingStrategy:
        """
        Comprehensive analysis of tax-loss harvesting opportunities
        """
        logger.info(f"Analyzing harvesting opportunities for user {user_id}")
        
        # Get user's taxable holdings and transaction history
        taxable_holdings = self._get_taxable_holdings(user_id)
        transaction_history = self._get_transaction_history(user_id)
        user_profile = self._get_user_profile(user_id)
        
        if not taxable_holdings:
            logger.warning(f"No taxable holdings found for user {user_id}")
            return self._empty_strategy()
        
        # Get existing tax loss carryforwards
        carryforward_losses = self._get_tax_loss_carryforwards(user_id)
        
        # Analyze each holding for harvesting potential
        opportunities = []
        
        for holding in taxable_holdings:
            if holding.symbol not in current_market_prices:
                logger.warning(f"No market price available for {holding.symbol}")
                continue
            
            opportunity = await self._analyze_holding_for_harvesting(
                holding,
                current_market_prices[holding.symbol],
                transaction_history,
                user_profile
            )
            
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort opportunities by tax benefit
        opportunities.sort(key=lambda x: x.tax_benefit, reverse=True)
        
        # Calculate strategy metrics
        total_harvestable_losses = sum(
            opp.unrealized_loss for opp in opportunities 
            if opp.wash_sale_safe
        )
        
        total_tax_benefit = sum(
            opp.tax_benefit for opp in opportunities 
            if opp.wash_sale_safe
        )
        
        # Generate implementation timeline
        implementation_timeline = self._generate_implementation_timeline(
            opportunities
        )
        
        # Create monitoring schedule
        monitoring_schedule = self._create_monitoring_schedule(
            opportunities
        )
        
        strategy = HarvestingStrategy(
            opportunities=opportunities,
            total_harvestable_losses=total_harvestable_losses,
            total_tax_benefit=total_tax_benefit,
            annual_loss_capacity=Decimal('3000'),  # IRS limit
            carryforward_losses=carryforward_losses,
            implementation_timeline=implementation_timeline,
            monitoring_schedule=monitoring_schedule
        )
        
        # Store opportunities in database
        await self._store_harvesting_opportunities(user_id, opportunities)
        
        logger.info(
            f"Found {len(opportunities)} opportunities with total benefit ${total_tax_benefit}"
        )
        
        return strategy
    
    def _get_taxable_holdings(self, user_id: str) -> List[TaxAccountHolding]:
        """Get holdings in taxable accounts only"""
        return (
            self.db.query(TaxAccountHolding)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccount.tax_treatment == TaxTreatmentEnum.TAXABLE,
                TaxAccount.is_active == True
            )
            .all()
        )
    
    def _get_transaction_history(self, user_id: str) -> List[TaxAccountTransaction]:
        """Get transaction history for wash sale analysis"""
        # Look back 60 days to be safe
        lookback_date = datetime.utcnow() - timedelta(days=60)
        
        return (
            self.db.query(TaxAccountTransaction)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccountTransaction.transaction_date >= lookback_date
            )
            .all()
        )
    
    def _get_user_profile(self, user_id: str) -> FinancialProfile:
        """Get user's financial profile for tax calculations"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    def _get_tax_loss_carryforwards(self, user_id: str) -> Decimal:
        """Get existing tax loss carryforwards"""
        # This would typically come from tax returns or previous calculations
        # For now, return 0 - would be enhanced with tax document integration
        return Decimal('0')
    
    async def _analyze_holding_for_harvesting(
        self,
        holding: TaxAccountHolding,
        current_price: float,
        transaction_history: List[TaxAccountTransaction],
        user_profile: FinancialProfile
    ) -> Optional[HarvestingOpportunity]:
        """Analyze a single holding for harvesting potential"""
        
        # Calculate unrealized loss
        current_market_value = Decimal(str(current_price)) * holding.shares
        cost_basis = (holding.cost_basis_per_share or Decimal('0')) * holding.shares
        unrealized_loss = cost_basis - current_market_value
        
        # Skip if not a loss or below threshold
        if unrealized_loss <= self.min_loss_threshold:
            return None
        
        # Skip small positions
        if current_market_value < self.min_position_size:
            return None
        
        # Check wash sale rule compliance
        wash_sale_safe = self.wash_sale_rule.is_wash_sale_safe(
            holding.symbol,
            datetime.utcnow(),
            transaction_history
        )
        
        # Calculate tax benefit
        tax_benefit = self._calculate_tax_benefit(
            unrealized_loss,
            user_profile.marginal_tax_rate
        )
        
        # Find replacement securities
        replacement_securities = self._find_replacement_securities(
            holding.symbol,
            holding.asset_class
        )
        
        # Select optimal replacement
        optimal_replacement = self._select_optimal_replacement(
            holding,
            replacement_securities
        )
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_steps(
            holding,
            optimal_replacement,
            wash_sale_safe
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            holding,
            replacement_securities,
            wash_sale_safe
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            holding,
            optimal_replacement,
            wash_sale_safe
        )
        
        return HarvestingOpportunity(
            holding=holding,
            unrealized_loss=unrealized_loss,
            tax_benefit=tax_benefit,
            wash_sale_safe=wash_sale_safe,
            replacement_securities=replacement_securities,
            optimal_replacement=optimal_replacement,
            implementation_steps=implementation_steps,
            confidence_score=confidence_score,
            risk_factors=risk_factors
        )
    
    def _calculate_tax_benefit(
        self,
        loss_amount: Decimal,
        marginal_tax_rate: float
    ) -> Decimal:
        """Calculate tax benefit from harvesting loss"""
        
        # Losses offset capital gains first (0% to 20% tax rate)
        # Then up to $3,000 can offset ordinary income
        # Remainder carries forward
        
        # Assume losses offset capital gains at 15% rate
        # This is simplified - real calculation would consider:
        # - Short vs long-term treatment
        # - Existing capital gains for the year
        # - State tax implications
        
        capital_gains_rate = 0.15
        ordinary_income_rate = marginal_tax_rate
        
        # For simplification, assume benefit at capital gains rate
        return loss_amount * Decimal(str(capital_gains_rate))
    
    def _find_replacement_securities(
        self,
        symbol: str,
        asset_class: str
    ) -> List[SecurityProfile]:
        """Find suitable replacement securities"""
        
        replacements = []
        
        # Check our predefined mapping
        if symbol in self.replacement_mapping:
            for replacement_symbol in self.replacement_mapping[symbol]:
                # Create security profile (simplified)
                profile = SecurityProfile(
                    symbol=replacement_symbol,
                    name=f"{replacement_symbol} Fund",
                    asset_class=asset_class,
                    sector="Diversified",
                    market_cap="Large",
                    correlation_with_market=0.95,  # Simplified
                    expense_ratio=0.05  # Typical for ETFs
                )
                replacements.append(profile)
        
        # If no predefined replacements, suggest similar asset class funds
        if not replacements:
            replacements = self._find_similar_asset_class_funds(asset_class)
        
        return replacements
    
    def _find_similar_asset_class_funds(self, asset_class: str) -> List[SecurityProfile]:
        """Find similar funds in the same asset class"""
        # This would typically query a securities database
        # For now, return some generic alternatives
        
        alternatives = {
            'equity': [
                SecurityProfile('VTI', 'Total Stock Market', 'equity', 'Diversified', 'All', 0.98),
                SecurityProfile('ITOT', 'Core S&P Total US', 'equity', 'Diversified', 'All', 0.97)
            ],
            'fixed_income': [
                SecurityProfile('BND', 'Total Bond Market', 'fixed_income', 'Government/Corporate', 'N/A', 0.1),
                SecurityProfile('AGG', 'Core US Aggregate', 'fixed_income', 'Government/Corporate', 'N/A', 0.1)
            ],
            'international': [
                SecurityProfile('VXUS', 'Total International Stock', 'international', 'Diversified', 'All', 0.85),
                SecurityProfile('IXUS', 'Core MSCI Total International', 'international', 'Diversified', 'All', 0.83)
            ]
        }
        
        return alternatives.get(asset_class.lower(), [])
    
    def _select_optimal_replacement(
        self,
        holding: TaxAccountHolding,
        replacements: List[SecurityProfile]
    ) -> Optional[SecurityProfile]:
        """Select the best replacement security"""
        
        if not replacements:
            return None
        
        # Score each replacement based on:
        # - Low expense ratio
        # - High correlation (similar exposure)
        # - Different enough to avoid wash sale
        
        best_replacement = None
        best_score = 0
        
        for replacement in replacements:
            score = 0
            
            # Prefer lower expense ratios
            if replacement.expense_ratio:
                score += max(0, (0.1 - replacement.expense_ratio) * 10)
            
            # Prefer high correlation (similar exposure)
            score += replacement.correlation_with_market * 5
            
            # Prefer well-known, liquid funds
            if replacement.symbol in ['VTI', 'SPY', 'BND', 'AGG']:
                score += 2
            
            if score > best_score:
                best_score = score
                best_replacement = replacement
        
        return best_replacement
    
    def _generate_implementation_steps(
        self,
        holding: TaxAccountHolding,
        replacement: Optional[SecurityProfile],
        wash_sale_safe: bool
    ) -> List[Dict]:
        """Generate step-by-step implementation plan"""
        
        steps = []
        
        if not wash_sale_safe:
            steps.append({
                'step': 1,
                'action': 'wait',
                'description': f"Wait until {holding.last_sale_date + timedelta(days=31)} to avoid wash sale",
                'timing': 'before_sale',
                'required': True
            })
        
        steps.append({
            'step': len(steps) + 1,
            'action': 'sell',
            'description': f"Sell {holding.shares} shares of {holding.symbol}",
            'timing': 'immediate' if wash_sale_safe else 'after_wait_period',
            'required': True,
            'tax_impact': f"Realize ${holding.unrealized_gain_loss} loss"
        })
        
        if replacement:
            steps.append({
                'step': len(steps) + 1,
                'action': 'buy',
                'description': f"Buy {replacement.symbol} as replacement",
                'timing': 'immediate_after_sale',
                'required': False,
                'note': f"Similar exposure to {holding.symbol}"
            })
        
        steps.append({
            'step': len(steps) + 1,
            'action': 'wait_to_rebuy',
            'description': f"Wait 31 days before buying {holding.symbol} again",
            'timing': 'after_sale',
            'required': True,
            'note': "Avoid wash sale rule violation"
        })
        
        return steps
    
    def _calculate_confidence_score(
        self,
        holding: TaxAccountHolding,
        replacements: List[SecurityProfile],
        wash_sale_safe: bool
    ) -> float:
        """Calculate confidence score for the opportunity"""
        
        score = 1.0
        
        # Reduce confidence if wash sale risk
        if not wash_sale_safe:
            score -= 0.3
        
        # Reduce confidence if no good replacements
        if not replacements:
            score -= 0.4
        elif len(replacements) < 2:
            score -= 0.2
        
        # Reduce confidence for small positions
        market_value = holding.market_value or Decimal('0')
        if market_value < Decimal('5000'):
            score -= 0.1
        
        # Reduce confidence if cost basis is unknown
        if not holding.cost_basis_per_share:
            score -= 0.2
        
        return max(0.0, score)
    
    def _identify_risk_factors(
        self,
        holding: TaxAccountHolding,
        replacement: Optional[SecurityProfile],
        wash_sale_safe: bool
    ) -> List[str]:
        """Identify potential risks with this opportunity"""
        
        risks = []
        
        if not wash_sale_safe:
            risks.append("Wash sale rule violation risk if sold now")
        
        if not replacement:
            risks.append("No suitable replacement security identified")
        
        if holding.unrealized_gain_loss and holding.unrealized_gain_loss < Decimal('-10000'):
            risks.append("Large position - consider scaling into harvest")
        
        market_value = holding.market_value or Decimal('0')
        if market_value > Decimal('50000'):
            risks.append("Large position - may impact market timing")
        
        if holding.dividend_yield and holding.dividend_yield > 0.03:
            risks.append("High dividend yield - consider income impact")
        
        return risks
    
    def _generate_implementation_timeline(
        self,
        opportunities: List[HarvestingOpportunity]
    ) -> List[Dict]:
        """Generate timeline for implementing harvesting opportunities"""
        
        timeline = []
        current_date = datetime.utcnow().date()
        
        # Group opportunities by timing
        immediate_opportunities = [
            opp for opp in opportunities if opp.wash_sale_safe
        ]
        
        delayed_opportunities = [
            opp for opp in opportunities if not opp.wash_sale_safe
        ]
        
        # Immediate opportunities
        if immediate_opportunities:
            timeline.append({
                'date': current_date,
                'actions': [
                    f"Harvest loss from {opp.holding.symbol}: ${opp.unrealized_loss}"
                    for opp in immediate_opportunities[:5]  # Limit to top 5
                ],
                'total_benefit': sum(opp.tax_benefit for opp in immediate_opportunities[:5]),
                'priority': 'high'
            })
        
        # Delayed opportunities (after wash sale periods)
        for opp in delayed_opportunities:
            if opp.holding.last_sale_date:
                safe_date = opp.holding.last_sale_date.date() + timedelta(days=31)
                timeline.append({
                    'date': safe_date,
                    'actions': [f"Harvest loss from {opp.holding.symbol}: ${opp.unrealized_loss}"],
                    'total_benefit': opp.tax_benefit,
                    'priority': 'medium',
                    'note': 'After wash sale period expires'
                })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def _create_monitoring_schedule(
        self,
        opportunities: List[HarvestingOpportunity]
    ) -> List[Dict]:
        """Create ongoing monitoring schedule"""
        
        schedule = []
        
        # Weekly monitoring for high-value opportunities
        high_value_opportunities = [
            opp for opp in opportunities 
            if opp.tax_benefit > Decimal('1000')
        ]
        
        if high_value_opportunities:
            schedule.append({
                'frequency': 'weekly',
                'actions': ['Monitor prices for high-value harvesting opportunities'],
                'symbols': [opp.holding.symbol for opp in high_value_opportunities],
                'priority': 'high'
            })
        
        # Monthly review of all positions
        schedule.append({
            'frequency': 'monthly',
            'actions': ['Review all positions for new harvesting opportunities'],
            'symbols': [opp.holding.symbol for opp in opportunities],
            'priority': 'medium'
        })
        
        # Year-end tax planning
        schedule.append({
            'frequency': 'annual',
            'timing': 'november',
            'actions': [
                'Year-end tax loss harvesting review',
                'Coordinate with tax professional',
                'Plan for next year carryforwards'
            ],
            'priority': 'high'
        })
        
        return schedule
    
    async def _store_harvesting_opportunities(
        self,
        user_id: str,
        opportunities: List[HarvestingOpportunity]
    ) -> None:
        """Store opportunities in database for tracking"""
        
        for opp in opportunities:
            # Check if opportunity already exists
            existing = self.db.query(TaxLossHarvestingOpportunity).filter(
                TaxLossHarvestingOpportunity.user_id == user_id,
                TaxLossHarvestingOpportunity.holding_id == opp.holding.id,
                TaxLossHarvestingOpportunity.status == 'identified'
            ).first()
            
            if existing:
                # Update existing opportunity
                existing.unrealized_loss = opp.unrealized_loss
                existing.tax_benefit = opp.tax_benefit
                existing.wash_sale_safe = opp.wash_sale_safe
                existing.updated_at = datetime.utcnow()
                
                if opp.optimal_replacement:
                    existing.replacement_symbol = opp.optimal_replacement.symbol
                    existing.replacement_name = opp.optimal_replacement.name
                    existing.correlation_score = opp.optimal_replacement.correlation_with_market
            else:
                # Create new opportunity record
                new_opp = TaxLossHarvestingOpportunity(
                    user_id=user_id,
                    holding_id=opp.holding.id,
                    symbol=opp.holding.symbol,
                    current_price=Decimal(str(opp.holding.current_price or 0)),
                    cost_basis=opp.holding.cost_basis_per_share or Decimal('0'),
                    unrealized_loss=opp.unrealized_loss,
                    tax_benefit=opp.tax_benefit,
                    wash_sale_safe=opp.wash_sale_safe,
                    priority_score=float(opp.confidence_score) * 100,
                    status='identified'
                )
                
                if opp.optimal_replacement:
                    new_opp.replacement_symbol = opp.optimal_replacement.symbol
                    new_opp.replacement_name = opp.optimal_replacement.name
                    new_opp.correlation_score = opp.optimal_replacement.correlation_with_market
                
                self.db.add(new_opp)
        
        await self.db.commit()
    
    def _empty_strategy(self) -> HarvestingStrategy:
        """Return empty strategy when no opportunities found"""
        return HarvestingStrategy(
            opportunities=[],
            total_harvestable_losses=Decimal('0'),
            total_tax_benefit=Decimal('0'),
            annual_loss_capacity=Decimal('3000'),
            carryforward_losses=Decimal('0'),
            implementation_timeline=[],
            monitoring_schedule=[]
        )
    
    async def execute_harvesting_opportunity(
        self,
        opportunity_id: str,
        execution_date: date
    ) -> Dict:
        """Execute a specific harvesting opportunity"""
        
        opportunity = self.db.query(TaxLossHarvestingOpportunity).filter(
            TaxLossHarvestingOpportunity.id == opportunity_id
        ).first()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Update status to executed
        opportunity.status = 'executed'
        opportunity.updated_at = datetime.utcnow()
        
        # Create transaction records for the sale
        # (This would integrate with brokerage API in production)
        
        result = {
            'opportunity_id': opportunity_id,
            'symbol': opportunity.symbol,
            'loss_realized': opportunity.unrealized_loss,
            'tax_benefit': opportunity.tax_benefit,
            'execution_date': execution_date,
            'replacement_symbol': opportunity.replacement_symbol,
            'status': 'executed'
        }
        
        await self.db.commit()
        
        logger.info(f"Executed harvesting opportunity for {opportunity.symbol}")
        
        return result
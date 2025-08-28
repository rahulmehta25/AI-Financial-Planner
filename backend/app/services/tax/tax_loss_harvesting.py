"""
Advanced Tax-Loss Harvesting Service

This module provides sophisticated tax-loss harvesting strategies including:
- Advanced wash sale rule compliance checking
- Optimal substitute security selection using correlation analysis
- Multi-lot tax optimization
- Intelligent harvesting timing
- Integration with portfolio rebalancing
- Automated monitoring and execution
- Risk management and position sizing
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ...models.tax_accounts import (
    TaxAccount, TaxAccountHolding, TaxAccountTransaction,
    TaxLossHarvestingOpportunity, AccountTypeEnum, TaxTreatmentEnum
)
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


class HarvestingStrategy(Enum):
    """Tax-loss harvesting strategy types"""
    AGGRESSIVE = "aggressive"  # Harvest all available losses
    CONSERVATIVE = "conservative"  # Only harvest high-confidence opportunities
    BALANCED = "balanced"  # Mix of aggressive and conservative
    YEAR_END = "year_end"  # Focus on year-end tax planning
    REBALANCING = "rebalancing"  # Coordinate with portfolio rebalancing


class RiskTolerance(Enum):
    """Risk tolerance for replacement securities"""
    LOW = "low"  # Only very similar securities
    MEDIUM = "medium"  # Some tracking error acceptable
    HIGH = "high"  # Higher tracking error for tax benefits


@dataclass
class SecurityCorrelation:
    """Security correlation analysis for substitute selection"""
    symbol: str
    name: str
    correlation: float
    tracking_error: float
    expense_ratio: float
    liquidity_score: float
    asset_class_match: bool
    sector_weights_similarity: float


@dataclass
class WashSaleAnalysis:
    """Comprehensive wash sale rule analysis"""
    is_safe: bool
    risk_score: float  # 0.0 = safe, 1.0 = high risk
    days_since_last_purchase: Optional[int]
    days_until_safe: Optional[int]
    related_purchases: List[Dict]
    substantially_identical_holdings: List[str]
    safe_date: Optional[date]


@dataclass
class TaxLotOpportunity:
    """Individual tax lot harvesting opportunity"""
    lot_id: str
    symbol: str
    shares: Decimal
    purchase_date: date
    cost_basis_per_share: Decimal
    current_price: Decimal
    holding_period_days: int
    unrealized_loss: Decimal
    tax_benefit: Decimal
    lot_priority: int
    wash_sale_analysis: WashSaleAnalysis


@dataclass
class HarvestingPlan:
    """Comprehensive harvesting execution plan"""
    total_opportunities: int
    total_harvestable_losses: Decimal
    total_tax_benefit: Decimal
    immediate_actions: List[Dict]
    scheduled_actions: List[Dict]
    monitoring_schedule: List[Dict]
    risk_mitigation_steps: List[str]
    performance_tracking: Dict[str, Any]


class AdvancedTaxLossHarvestingEngine:
    """
    Advanced tax-loss harvesting engine with sophisticated strategies
    and comprehensive wash sale compliance
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
        # Advanced wash sale parameters
        self.wash_sale_lookback_days = 30
        self.wash_sale_lookforward_days = 30
        self.substantially_identical_threshold = 0.85  # Correlation threshold
        
        # Minimum thresholds for harvesting
        self.min_loss_threshold = Decimal('250')
        self.min_tax_benefit_threshold = Decimal('50')
        self.min_position_value = Decimal('1000')
        
        # Advanced substitute security mapping with correlation data
        self.substitute_universe = {
            # Large Cap US Equity
            'SPY': [
                {'symbol': 'VOO', 'correlation': 0.999, 'tracking_error': 0.02},
                {'symbol': 'VTI', 'correlation': 0.985, 'tracking_error': 0.15},
                {'symbol': 'ITOT', 'correlation': 0.998, 'tracking_error': 0.03},
                {'symbol': 'SPTM', 'correlation': 0.996, 'tracking_error': 0.05},
            ],
            'VTI': [
                {'symbol': 'ITOT', 'correlation': 0.997, 'tracking_error': 0.08},
                {'symbol': 'SPTM', 'correlation': 0.994, 'tracking_error': 0.12},
                {'symbol': 'SCHB', 'correlation': 0.992, 'tracking_error': 0.15},
            ],
            'VOO': [
                {'symbol': 'SPY', 'correlation': 0.999, 'tracking_error': 0.02},
                {'symbol': 'ITOT', 'correlation': 0.996, 'tracking_error': 0.06},
                {'symbol': 'SPTM', 'correlation': 0.995, 'tracking_error': 0.08},
            ],
            
            # International Developed Markets
            'VEA': [
                {'symbol': 'IEFA', 'correlation': 0.995, 'tracking_error': 0.05},
                {'symbol': 'SCHF', 'correlation': 0.992, 'tracking_error': 0.08},
                {'symbol': 'VTEB', 'correlation': 0.988, 'tracking_error': 0.12},
            ],
            'IEFA': [
                {'symbol': 'VEA', 'correlation': 0.995, 'tracking_error': 0.05},
                {'symbol': 'SCHF', 'correlation': 0.993, 'tracking_error': 0.07},
                {'symbol': 'EFA', 'correlation': 0.990, 'tracking_error': 0.10},
            ],
            
            # Emerging Markets
            'VWO': [
                {'symbol': 'IEMG', 'correlation': 0.993, 'tracking_error': 0.08},
                {'symbol': 'SCHE', 'correlation': 0.990, 'tracking_error': 0.12},
                {'symbol': 'SPEM', 'correlation': 0.988, 'tracking_error': 0.15},
            ],
            'IEMG': [
                {'symbol': 'VWO', 'correlation': 0.993, 'tracking_error': 0.08},
                {'symbol': 'SCHE', 'correlation': 0.991, 'tracking_error': 0.10},
                {'symbol': 'EEM', 'correlation': 0.985, 'tracking_error': 0.18},
            ],
            
            # Fixed Income
            'BND': [
                {'symbol': 'AGG', 'correlation': 0.998, 'tracking_error': 0.03},
                {'symbol': 'SCHZ', 'correlation': 0.995, 'tracking_error': 0.05},
                {'symbol': 'IUSB', 'correlation': 0.993, 'tracking_error': 0.08},
            ],
            'AGG': [
                {'symbol': 'BND', 'correlation': 0.998, 'tracking_error': 0.03},
                {'symbol': 'SCHZ', 'correlation': 0.996, 'tracking_error': 0.04},
                {'symbol': 'IUSB', 'correlation': 0.994, 'tracking_error': 0.06},
            ],
            
            # Long-term Treasuries
            'TLT': [
                {'symbol': 'EDV', 'correlation': 0.985, 'tracking_error': 0.15},
                {'symbol': 'VGLT', 'correlation': 0.992, 'tracking_error': 0.08},
                {'symbol': 'SPTL', 'correlation': 0.988, 'tracking_error': 0.12},
            ],
            
            # Small Cap
            'IWM': [
                {'symbol': 'VB', 'correlation': 0.985, 'tracking_error': 0.18},
                {'symbol': 'VTWO', 'correlation': 0.988, 'tracking_error': 0.15},
                {'symbol': 'SCHA', 'correlation': 0.982, 'tracking_error': 0.20},
            ],
            'VB': [
                {'symbol': 'IWM', 'correlation': 0.985, 'tracking_error': 0.18},
                {'symbol': 'VTWO', 'correlation': 0.990, 'tracking_error': 0.12},
                {'symbol': 'SMLV', 'correlation': 0.875, 'tracking_error': 0.35},
            ],
            
            # REITs
            'VNQ': [
                {'symbol': 'SCHH', 'correlation': 0.992, 'tracking_error': 0.10},
                {'symbol': 'IYR', 'correlation': 0.988, 'tracking_error': 0.15},
                {'symbol': 'FREL', 'correlation': 0.985, 'tracking_error': 0.18},
            ],
            
            # Sector ETFs - Technology
            'XLK': [
                {'symbol': 'VGT', 'correlation': 0.985, 'tracking_error': 0.20},
                {'symbol': 'FTEC', 'correlation': 0.982, 'tracking_error': 0.25},
                {'symbol': 'IYW', 'correlation': 0.978, 'tracking_error': 0.28},
            ],
        }
        
        # Risk management parameters
        self.max_position_harvest_pct = 0.5  # Don't harvest more than 50% of position
        self.max_daily_harvest_value = Decimal('100000')  # Daily harvest limit
        self.correlation_decay_factor = 0.95  # Reduce correlation over time
    
    async def analyze_comprehensive_harvesting_opportunities(
        self,
        user_id: str,
        strategy: HarvestingStrategy = HarvestingStrategy.BALANCED,
        risk_tolerance: RiskTolerance = RiskTolerance.MEDIUM,
        current_market_prices: Optional[Dict[str, float]] = None
    ) -> HarvestingPlan:
        """
        Perform comprehensive analysis of tax-loss harvesting opportunities
        """
        logger.info(f"Analyzing comprehensive harvesting opportunities for user {user_id}")
        
        try:
            # Get user data
            user_profile = await self._get_user_profile(user_id)
            if not user_profile:
                raise ValueError(f"User profile not found for user {user_id}")
            
            # Get taxable holdings and transaction history
            holdings = await self._get_taxable_holdings(user_id)
            transactions = await self._get_transaction_history(user_id)
            
            if not holdings:
                logger.warning(f"No taxable holdings found for user {user_id}")
                return self._empty_harvesting_plan()
            
            # Update market prices if provided
            if current_market_prices:
                await self._update_holding_prices(holdings, current_market_prices)
            
            # Analyze each holding for tax-loss opportunities
            all_opportunities = []
            
            for holding in holdings:
                opportunities = await self._analyze_holding_comprehensive(
                    holding, transactions, user_profile, strategy, risk_tolerance
                )
                all_opportunities.extend(opportunities)
            
            # Filter and prioritize opportunities
            filtered_opportunities = self._filter_opportunities(
                all_opportunities, strategy, user_profile
            )
            
            # Generate comprehensive execution plan
            execution_plan = await self._generate_execution_plan(
                filtered_opportunities, strategy, user_profile
            )
            
            # Create monitoring and tracking systems
            monitoring_schedule = self._create_monitoring_schedule(
                filtered_opportunities, strategy
            )
            
            # Performance tracking setup
            performance_tracking = self._setup_performance_tracking(
                filtered_opportunities
            )
            
            # Risk mitigation strategies
            risk_mitigation = self._generate_risk_mitigation_steps(
                filtered_opportunities, strategy
            )
            
            harvesting_plan = HarvestingPlan(
                total_opportunities=len(filtered_opportunities),
                total_harvestable_losses=sum(opp.unrealized_loss for opp in filtered_opportunities),
                total_tax_benefit=sum(opp.tax_benefit for opp in filtered_opportunities),
                immediate_actions=execution_plan.get('immediate_actions', []),
                scheduled_actions=execution_plan.get('scheduled_actions', []),
                monitoring_schedule=monitoring_schedule,
                risk_mitigation_steps=risk_mitigation,
                performance_tracking=performance_tracking
            )
            
            # Store analysis results
            await self._store_harvesting_analysis(user_id, harvesting_plan, filtered_opportunities)
            
            logger.info(f"Generated harvesting plan with {len(filtered_opportunities)} opportunities")
            
            return harvesting_plan
            
        except Exception as e:
            logger.error(f"Error analyzing harvesting opportunities for user {user_id}: {str(e)}")
            raise
    
    async def _get_user_profile(self, user_id: str) -> Optional[FinancialProfile]:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    async def _get_taxable_holdings(self, user_id: str) -> List[TaxAccountHolding]:
        """Get holdings in taxable accounts only"""
        return (
            self.db.query(TaxAccountHolding)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccount.tax_treatment == TaxTreatmentEnum.TAXABLE,
                TaxAccount.is_active == True,
                TaxAccountHolding.shares > 0
            )
            .order_by(desc(TaxAccountHolding.market_value))
            .all()
        )
    
    async def _get_transaction_history(self, user_id: str) -> List[TaxAccountTransaction]:
        """Get comprehensive transaction history for wash sale analysis"""
        # Extended lookback period for thorough analysis
        lookback_date = datetime.utcnow() - timedelta(days=90)
        
        return (
            self.db.query(TaxAccountTransaction)
            .join(TaxAccount)
            .filter(
                TaxAccount.user_id == user_id,
                TaxAccountTransaction.transaction_date >= lookback_date
            )
            .order_by(desc(TaxAccountTransaction.transaction_date))
            .all()
        )
    
    async def _update_holding_prices(
        self,
        holdings: List[TaxAccountHolding],
        market_prices: Dict[str, float]
    ) -> None:
        """Update holding prices with current market data"""
        for holding in holdings:
            if holding.symbol in market_prices:
                new_price = Decimal(str(market_prices[holding.symbol]))
                holding.current_price = new_price
                holding.market_value = holding.shares * new_price
                holding.unrealized_gain_loss = (
                    holding.market_value - (holding.shares * holding.cost_basis_per_share)
                )
    
    async def _analyze_holding_comprehensive(
        self,
        holding: TaxAccountHolding,
        transactions: List[TaxAccountTransaction],
        user_profile: FinancialProfile,
        strategy: HarvestingStrategy,
        risk_tolerance: RiskTolerance
    ) -> List[TaxLotOpportunity]:
        """Comprehensive analysis of individual holding for tax-loss harvesting"""
        
        opportunities = []
        
        # Get all tax lots for this holding
        tax_lots = await self._get_tax_lots(holding)
        
        # Analyze each tax lot separately
        for lot in tax_lots:
            opportunity = await self._analyze_tax_lot(
                lot, holding, transactions, user_profile, strategy, risk_tolerance
            )
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by tax benefit
        opportunities.sort(key=lambda x: x.tax_benefit, reverse=True)
        
        return opportunities
    
    async def _get_tax_lots(self, holding: TaxAccountHolding) -> List[Dict]:
        """Get individual tax lots for a holding (FIFO, LIFO, or specific identification)"""
        
        # For now, treat each holding as a single tax lot
        # In a production system, this would query actual tax lot data
        current_value = holding.shares * (holding.current_price or Decimal('0'))
        cost_basis = holding.shares * (holding.cost_basis_per_share or Decimal('0'))
        
        return [{
            'lot_id': f"{holding.id}_default",
            'shares': holding.shares,
            'purchase_date': holding.purchase_date or datetime.utcnow().date(),
            'cost_basis_per_share': holding.cost_basis_per_share or Decimal('0'),
            'current_value': current_value,
            'cost_basis': cost_basis,
            'unrealized_gain_loss': current_value - cost_basis
        }]
    
    async def _analyze_tax_lot(
        self,
        tax_lot: Dict,
        holding: TaxAccountHolding,
        transactions: List[TaxAccountTransaction],
        user_profile: FinancialProfile,
        strategy: HarvestingStrategy,
        risk_tolerance: RiskTolerance
    ) -> Optional[TaxLotOpportunity]:
        """Analyze individual tax lot for harvesting opportunity"""
        
        # Calculate unrealized loss
        unrealized_loss = tax_lot['cost_basis'] - tax_lot['current_value']
        
        # Skip if not a loss or below threshold
        if unrealized_loss <= self.min_loss_threshold:
            return None
        
        # Skip small positions
        if tax_lot['current_value'] < self.min_position_value:
            return None
        
        # Calculate holding period
        purchase_date = tax_lot['purchase_date']
        holding_period_days = (datetime.utcnow().date() - purchase_date).days
        
        # Perform wash sale analysis
        wash_sale_analysis = await self._perform_wash_sale_analysis(
            holding.symbol, transactions, purchase_date
        )
        
        # Calculate tax benefit
        tax_benefit = await self._calculate_tax_benefit(
            unrealized_loss, holding_period_days, user_profile
        )
        
        # Skip if tax benefit is too small
        if tax_benefit < self.min_tax_benefit_threshold:
            return None
        
        # Calculate lot priority based on strategy
        lot_priority = self._calculate_lot_priority(
            unrealized_loss, tax_benefit, holding_period_days, 
            wash_sale_analysis, strategy
        )
        
        return TaxLotOpportunity(
            lot_id=tax_lot['lot_id'],
            symbol=holding.symbol,
            shares=tax_lot['shares'],
            purchase_date=purchase_date,
            cost_basis_per_share=tax_lot['cost_basis_per_share'],
            current_price=holding.current_price or Decimal('0'),
            holding_period_days=holding_period_days,
            unrealized_loss=unrealized_loss,
            tax_benefit=tax_benefit,
            lot_priority=lot_priority,
            wash_sale_analysis=wash_sale_analysis
        )
    
    async def _perform_wash_sale_analysis(
        self,
        symbol: str,
        transactions: List[TaxAccountTransaction],
        purchase_date: date
    ) -> WashSaleAnalysis:
        """Perform comprehensive wash sale rule analysis"""
        
        current_date = datetime.utcnow().date()
        
        # Check for purchases in the wash sale window
        related_purchases = []
        
        # Look back 30 days from today
        lookback_start = current_date - timedelta(days=self.wash_sale_lookback_days)
        
        for transaction in transactions:
            if (transaction.symbol == symbol and 
                transaction.transaction_type == 'buy' and
                transaction.transaction_date.date() >= lookback_start):
                
                related_purchases.append({
                    'date': transaction.transaction_date.date(),
                    'shares': transaction.shares,
                    'price': transaction.price_per_share,
                    'days_ago': (current_date - transaction.transaction_date.date()).days
                })
        
        # Determine if sale is safe
        is_safe = len(related_purchases) == 0
        
        # Calculate risk score
        if related_purchases:
            most_recent_purchase = min(p['days_ago'] for p in related_purchases)
            risk_score = max(0.0, 1.0 - (most_recent_purchase / self.wash_sale_lookback_days))
            days_until_safe = max(0, self.wash_sale_lookback_days + 1 - most_recent_purchase)
            safe_date = current_date + timedelta(days=days_until_safe)
        else:
            risk_score = 0.0
            days_until_safe = None
            safe_date = None
        
        # Find substantially identical securities
        substantially_identical = await self._find_substantially_identical_securities(symbol)
        
        return WashSaleAnalysis(
            is_safe=is_safe,
            risk_score=risk_score,
            days_since_last_purchase=min(p['days_ago'] for p in related_purchases) if related_purchases else None,
            days_until_safe=days_until_safe,
            related_purchases=related_purchases,
            substantially_identical_holdings=substantially_identical,
            safe_date=safe_date
        )
    
    async def _find_substantially_identical_securities(self, symbol: str) -> List[str]:
        """Find substantially identical securities that could trigger wash sale"""
        
        # Get potential substitutes
        substitutes = self.substitute_universe.get(symbol, [])
        
        # Filter by correlation threshold for substantially identical determination
        substantially_identical = []
        for substitute in substitutes:
            if substitute['correlation'] >= self.substantially_identical_threshold:
                substantially_identical.append(substitute['symbol'])
        
        return substantially_identical
    
    async def _calculate_tax_benefit(
        self,
        loss_amount: Decimal,
        holding_period_days: int,
        user_profile: FinancialProfile
    ) -> Decimal:
        """Calculate tax benefit from harvesting loss"""
        
        # Determine if short-term or long-term
        is_long_term = holding_period_days > 365
        
        # Get user's tax rates
        filing_status = user_profile.filing_status.lower()
        income = user_profile.annual_income or Decimal('0')
        
        if is_long_term:
            # Long-term capital gains rates (0%, 15%, 20%)
            if filing_status == 'single':
                if income <= Decimal('47000'):
                    tax_rate = Decimal('0.00')
                elif income <= Decimal('518900'):
                    tax_rate = Decimal('0.15')
                else:
                    tax_rate = Decimal('0.20')
            elif filing_status in ['married_filing_jointly', 'qualifying_widow']:
                if income <= Decimal('94000'):
                    tax_rate = Decimal('0.00')
                elif income <= Decimal('583750'):
                    tax_rate = Decimal('0.15')
                else:
                    tax_rate = Decimal('0.20')
            else:  # married_filing_separately, head_of_household
                if income <= Decimal('47000'):
                    tax_rate = Decimal('0.00')
                elif income <= Decimal('291875'):
                    tax_rate = Decimal('0.15')
                else:
                    tax_rate = Decimal('0.20')
        else:
            # Short-term capital gains taxed as ordinary income
            # Simplified marginal rate calculation
            if income <= Decimal('47500'):
                tax_rate = Decimal('0.12')
            elif income <= Decimal('100500'):
                tax_rate = Decimal('0.22')
            elif income <= Decimal('191650'):
                tax_rate = Decimal('0.24')
            elif income <= Decimal('243725'):
                tax_rate = Decimal('0.32')
            elif income <= Decimal('609350'):
                tax_rate = Decimal('0.35')
            else:
                tax_rate = Decimal('0.37')
        
        # Add state tax if available
        state_tax_rate = getattr(user_profile, 'state_tax_rate', Decimal('0.05'))
        total_tax_rate = tax_rate + state_tax_rate
        
        # Calculate tax benefit (losses offset gains/income)
        return loss_amount * total_tax_rate
    
    def _calculate_lot_priority(
        self,
        unrealized_loss: Decimal,
        tax_benefit: Decimal,
        holding_period_days: int,
        wash_sale_analysis: WashSaleAnalysis,
        strategy: HarvestingStrategy
    ) -> int:
        """Calculate priority ranking for tax lot (1 = highest priority)"""
        
        base_score = float(tax_benefit / unrealized_loss) * 100  # Tax benefit as % of loss
        
        # Adjust for wash sale risk
        if not wash_sale_analysis.is_safe:
            base_score *= (1 - wash_sale_analysis.risk_score)
        
        # Adjust for holding period
        if holding_period_days > 365:
            base_score *= 0.8  # Slight preference for short-term losses
        
        # Strategy-specific adjustments
        if strategy == HarvestingStrategy.AGGRESSIVE:
            base_score *= 1.2
        elif strategy == HarvestingStrategy.CONSERVATIVE:
            if wash_sale_analysis.risk_score > 0.1:
                base_score *= 0.5
        
        # Convert to priority ranking (1-10)
        if base_score >= 20:
            return 1
        elif base_score >= 15:
            return 2
        elif base_score >= 10:
            return 3
        elif base_score >= 5:
            return 4
        else:
            return 5
    
    def _filter_opportunities(
        self,
        opportunities: List[TaxLotOpportunity],
        strategy: HarvestingStrategy,
        user_profile: FinancialProfile
    ) -> List[TaxLotOpportunity]:
        """Filter opportunities based on strategy and user preferences"""
        
        filtered = []
        
        for opp in opportunities:
            # Strategy-specific filtering
            if strategy == HarvestingStrategy.CONSERVATIVE:
                # Only include high-confidence opportunities
                if opp.wash_sale_analysis.risk_score > 0.1:
                    continue
                if opp.tax_benefit < Decimal('100'):
                    continue
            elif strategy == HarvestingStrategy.YEAR_END:
                # Focus on opportunities that can be executed before year-end
                days_until_year_end = (date(2025, 12, 31) - datetime.utcnow().date()).days
                if opp.wash_sale_analysis.days_until_safe and opp.wash_sale_analysis.days_until_safe > days_until_year_end:
                    continue
            
            # Check against user's risk tolerance and preferences
            if self._meets_user_criteria(opp, user_profile):
                filtered.append(opp)
        
        # Sort by priority
        filtered.sort(key=lambda x: (x.lot_priority, -float(x.tax_benefit)))
        
        return filtered
    
    def _meets_user_criteria(
        self,
        opportunity: TaxLotOpportunity,
        user_profile: FinancialProfile
    ) -> bool:
        """Check if opportunity meets user-specific criteria"""
        
        # Check minimum thresholds
        if opportunity.tax_benefit < self.min_tax_benefit_threshold:
            return False
        
        # Check position size limits
        current_value = opportunity.shares * opportunity.current_price
        if current_value < self.min_position_value:
            return False
        
        # Additional user-specific criteria would be implemented here
        # based on user preferences stored in the profile
        
        return True
    
    async def _generate_execution_plan(
        self,
        opportunities: List[TaxLotOpportunity],
        strategy: HarvestingStrategy,
        user_profile: FinancialProfile
    ) -> Dict[str, List[Dict]]:
        """Generate comprehensive execution plan"""
        
        immediate_actions = []
        scheduled_actions = []
        
        for opp in opportunities:
            if opp.wash_sale_analysis.is_safe:
                # Can execute immediately
                immediate_actions.append({
                    'action_type': 'harvest_loss',
                    'symbol': opp.symbol,
                    'shares': float(opp.shares),
                    'expected_loss': float(opp.unrealized_loss),
                    'expected_tax_benefit': float(opp.tax_benefit),
                    'priority': opp.lot_priority,
                    'execution_date': 'immediate',
                    'replacement_options': await self._get_replacement_options(
                        opp.symbol, RiskTolerance.MEDIUM
                    )
                })
            else:
                # Schedule for future execution
                if opp.wash_sale_analysis.safe_date:
                    scheduled_actions.append({
                        'action_type': 'scheduled_harvest',
                        'symbol': opp.symbol,
                        'shares': float(opp.shares),
                        'expected_loss': float(opp.unrealized_loss),
                        'expected_tax_benefit': float(opp.tax_benefit),
                        'priority': opp.lot_priority,
                        'scheduled_date': opp.wash_sale_analysis.safe_date.isoformat(),
                        'days_until_execution': opp.wash_sale_analysis.days_until_safe,
                        'wash_sale_risk': opp.wash_sale_analysis.risk_score
                    })
        
        return {
            'immediate_actions': immediate_actions,
            'scheduled_actions': scheduled_actions
        }
    
    async def _get_replacement_options(
        self,
        symbol: str,
        risk_tolerance: RiskTolerance
    ) -> List[Dict]:
        """Get suitable replacement security options"""
        
        substitutes = self.substitute_universe.get(symbol, [])
        
        options = []
        for substitute in substitutes:
            # Filter based on risk tolerance
            if risk_tolerance == RiskTolerance.LOW and substitute['tracking_error'] > 0.05:
                continue
            elif risk_tolerance == RiskTolerance.MEDIUM and substitute['tracking_error'] > 0.20:
                continue
            
            options.append({
                'symbol': substitute['symbol'],
                'correlation': substitute['correlation'],
                'tracking_error': substitute['tracking_error'],
                'suitability_score': substitute['correlation'] * (1 - substitute['tracking_error'])
            })
        
        # Sort by suitability score
        options.sort(key=lambda x: x['suitability_score'], reverse=True)
        
        return options[:3]  # Return top 3 options
    
    def _create_monitoring_schedule(
        self,
        opportunities: List[TaxLotOpportunity],
        strategy: HarvestingStrategy
    ) -> List[Dict]:
        """Create monitoring schedule for opportunities"""
        
        schedule = []
        
        # Daily monitoring for high-value immediate opportunities
        high_value_immediate = [
            opp for opp in opportunities 
            if opp.wash_sale_analysis.is_safe and opp.tax_benefit > Decimal('500')
        ]
        
        if high_value_immediate:
            schedule.append({
                'frequency': 'daily',
                'action': 'monitor_high_value_opportunities',
                'description': f'Monitor {len(high_value_immediate)} high-value immediate opportunities',
                'symbols': [opp.symbol for opp in high_value_immediate],
                'automation_level': 'high'
            })
        
        # Weekly monitoring for wash sale situations
        wash_sale_opportunities = [
            opp for opp in opportunities if not opp.wash_sale_analysis.is_safe
        ]
        
        if wash_sale_opportunities:
            schedule.append({
                'frequency': 'weekly',
                'action': 'monitor_wash_sale_clearance',
                'description': f'Monitor {len(wash_sale_opportunities)} opportunities waiting for wash sale clearance',
                'symbols': [opp.symbol for opp in wash_sale_opportunities],
                'automation_level': 'medium'
            })
        
        # Monthly comprehensive review
        schedule.append({
            'frequency': 'monthly',
            'action': 'comprehensive_review',
            'description': 'Full review of all positions for new harvesting opportunities',
            'automation_level': 'low'
        })
        
        return schedule
    
    def _setup_performance_tracking(
        self,
        opportunities: List[TaxLotOpportunity]
    ) -> Dict[str, Any]:
        """Setup performance tracking for harvesting activities"""
        
        return {
            'metrics_to_track': [
                'total_losses_harvested',
                'total_tax_benefits_realized',
                'number_of_harvests_executed',
                'average_time_to_execution',
                'wash_sale_violations_avoided',
                'replacement_security_performance'
            ],
            'reporting_frequency': 'monthly',
            'benchmark_comparisons': [
                'sp500_performance',
                'portfolio_performance_vs_benchmark',
                'tax_alpha_generated'
            ],
            'alert_thresholds': {
                'large_unrealized_loss': 1000.0,
                'high_tax_benefit_opportunity': 250.0,
                'wash_sale_risk_change': 0.2
            }
        }
    
    def _generate_risk_mitigation_steps(
        self,
        opportunities: List[TaxLotOpportunity],
        strategy: HarvestingStrategy
    ) -> List[str]:
        """Generate risk mitigation steps"""
        
        steps = [
            "Maintain diversified portfolio exposure through replacement securities",
            "Monitor correlation drift between original and replacement securities",
            "Set maximum position size limits for individual harvesting transactions",
            "Implement stop-loss mechanisms for replacement securities if needed"
        ]
        
        # Add strategy-specific risk mitigation
        if strategy == HarvestingStrategy.AGGRESSIVE:
            steps.extend([
                "Review all transactions for wash sale compliance before execution",
                "Consider tax impact of replacement security dividends and distributions",
                "Monitor portfolio drift from target allocation"
            ])
        
        # Add opportunity-specific risk mitigation
        high_risk_opportunities = [opp for opp in opportunities if opp.wash_sale_analysis.risk_score > 0.3]
        if high_risk_opportunities:
            steps.append(f"Extra scrutiny for {len(high_risk_opportunities)} high wash-sale-risk opportunities")
        
        return steps
    
    def _empty_harvesting_plan(self) -> HarvestingPlan:
        """Return empty harvesting plan when no opportunities found"""
        return HarvestingPlan(
            total_opportunities=0,
            total_harvestable_losses=Decimal('0'),
            total_tax_benefit=Decimal('0'),
            immediate_actions=[],
            scheduled_actions=[],
            monitoring_schedule=[],
            risk_mitigation_steps=[],
            performance_tracking={}
        )
    
    async def _store_harvesting_analysis(
        self,
        user_id: str,
        plan: HarvestingPlan,
        opportunities: List[TaxLotOpportunity]
    ) -> None:
        """Store harvesting analysis results in database"""
        
        # Store each opportunity in the database
        for opp in opportunities:
            existing = self.db.query(TaxLossHarvestingOpportunity).filter(
                TaxLossHarvestingOpportunity.user_id == user_id,
                TaxLossHarvestingOpportunity.symbol == opp.symbol,
                TaxLossHarvestingOpportunity.lot_id == opp.lot_id
            ).first()
            
            if existing:
                # Update existing record
                existing.unrealized_loss = opp.unrealized_loss
                existing.tax_benefit = opp.tax_benefit
                existing.wash_sale_safe = opp.wash_sale_analysis.is_safe
                existing.priority_score = float(opp.lot_priority) * 20  # Convert to 0-100 scale
                existing.updated_at = datetime.utcnow()
            else:
                # Create new record
                new_opportunity = TaxLossHarvestingOpportunity(
                    user_id=user_id,
                    symbol=opp.symbol,
                    lot_id=opp.lot_id,
                    shares=opp.shares,
                    cost_basis=opp.cost_basis_per_share,
                    current_price=opp.current_price,
                    unrealized_loss=opp.unrealized_loss,
                    tax_benefit=opp.tax_benefit,
                    wash_sale_safe=opp.wash_sale_analysis.is_safe,
                    priority_score=float(opp.lot_priority) * 20,
                    holding_period_days=opp.holding_period_days,
                    status='identified'
                )
                
                self.db.add(new_opportunity)
        
        await self.db.commit()
    
    async def execute_harvesting_opportunity(
        self,
        user_id: str,
        opportunity_id: str,
        replacement_symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a specific harvesting opportunity"""
        
        # Get the opportunity record
        opportunity = self.db.query(TaxLossHarvestingOpportunity).filter(
            TaxLossHarvestingOpportunity.id == opportunity_id,
            TaxLossHarvestingOpportunity.user_id == user_id
        ).first()
        
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        if not opportunity.wash_sale_safe:
            raise ValueError("Cannot execute opportunity with wash sale risk")
        
        # Execute the harvesting transaction
        execution_result = await self._execute_harvest_transaction(
            opportunity, replacement_symbol
        )
        
        # Update opportunity status
        opportunity.status = 'executed'
        opportunity.executed_at = datetime.utcnow()
        opportunity.replacement_symbol = replacement_symbol
        
        await self.db.commit()
        
        return execution_result
    
    async def _execute_harvest_transaction(
        self,
        opportunity: TaxLossHarvestingOpportunity,
        replacement_symbol: Optional[str]
    ) -> Dict[str, Any]:
        """Execute the actual harvesting transaction"""
        
        # In a production system, this would integrate with brokerage APIs
        # For now, we'll simulate the transaction
        
        execution_result = {
            'opportunity_id': opportunity.id,
            'symbol_sold': opportunity.symbol,
            'shares_sold': float(opportunity.shares),
            'sale_price': float(opportunity.current_price),
            'total_proceeds': float(opportunity.shares * opportunity.current_price),
            'realized_loss': float(opportunity.unrealized_loss),
            'tax_benefit_realized': float(opportunity.tax_benefit),
            'execution_timestamp': datetime.utcnow().isoformat(),
            'replacement_symbol': replacement_symbol,
            'status': 'executed'
        }
        
        if replacement_symbol:
            # Calculate replacement purchase
            replacement_shares = opportunity.shares  # Same dollar amount
            execution_result.update({
                'replacement_purchase': {
                    'symbol': replacement_symbol,
                    'shares': float(replacement_shares),
                    'estimated_price': float(opportunity.current_price),  # Simplified
                    'total_cost': float(replacement_shares * opportunity.current_price)
                }
            })
        
        logger.info(f"Executed harvesting for {opportunity.symbol}: ${opportunity.unrealized_loss:.2f} loss")
        
        return execution_result
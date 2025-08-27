"""
Tax-Aware Account Optimization Engine

Optimizes asset allocation across multiple account types:
- 401(k), Roth 401(k), Traditional IRA, Roth IRA
- HSA, 529 plans, Taxable accounts
- Asset location optimization for tax efficiency
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime, date
import logging
from sqlalchemy.orm import Session

from ...models.tax_accounts import (
    TaxAccount, TaxAccountHolding, AccountTypeEnum, TaxTreatmentEnum,
    AssetLocationPriorityEnum, IRSLimits2025, TaxCalculationUtils,
    AssetLocationAnalysis
)
from ...models.user import User
from ...models.financial_profile import FinancialProfile

logger = logging.getLogger(__name__)


@dataclass
class AssetCharacteristics:
    """Characteristics of an asset for tax optimization"""
    symbol: str
    asset_class: str
    expected_return: float
    dividend_yield: float
    turnover_ratio: float
    tax_efficiency_score: float
    volatility: float
    correlation_matrix: Dict[str, float]


@dataclass 
class AccountCapacity:
    """Available capacity in each account type"""
    account_id: str
    account_type: AccountTypeEnum
    available_space: Decimal
    tax_treatment: TaxTreatmentEnum
    current_allocation: Dict[str, Decimal]
    optimal_asset_types: List[str]


@dataclass
class OptimizationResult:
    """Result of asset location optimization"""
    optimal_allocation: Dict[str, Dict[str, Decimal]]  # account_id -> {symbol: amount}
    current_tax_drag: Decimal
    optimized_tax_drag: Decimal
    annual_tax_savings: Decimal
    implementation_steps: List[Dict]
    rebalancing_trades: List[Dict]
    confidence_score: float


class TaxAwareAccountOptimizer:
    """
    Comprehensive tax-aware account optimization engine
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.irs_limits = IRSLimits2025()
        self.tax_utils = TaxCalculationUtils()
        
        # Asset location priority rules
        self.location_rules = {
            # Tax-inefficient assets belong in tax-deferred accounts
            'bonds': {
                AccountTypeEnum.TRADITIONAL_401K: 1.0,
                AccountTypeEnum.TRADITIONAL_IRA: 1.0,
                AccountTypeEnum.ROTH_401K: 0.3,
                AccountTypeEnum.ROTH_IRA: 0.3,
                AccountTypeEnum.HSA: 0.2,
                AccountTypeEnum.TAXABLE: 0.1
            },
            'reits': {
                AccountTypeEnum.TRADITIONAL_401K: 1.0,
                AccountTypeEnum.TRADITIONAL_IRA: 1.0,
                AccountTypeEnum.HSA: 0.8,
                AccountTypeEnum.ROTH_401K: 0.5,
                AccountTypeEnum.ROTH_IRA: 0.5,
                AccountTypeEnum.TAXABLE: 0.1
            },
            # High-growth assets belong in Roth accounts
            'growth_stocks': {
                AccountTypeEnum.ROTH_IRA: 1.0,
                AccountTypeEnum.ROTH_401K: 1.0,
                AccountTypeEnum.HSA: 0.9,
                AccountTypeEnum.TRADITIONAL_401K: 0.6,
                AccountTypeEnum.TRADITIONAL_IRA: 0.6,
                AccountTypeEnum.TAXABLE: 0.7
            },
            # International stocks (foreign tax credit) in taxable
            'international_stocks': {
                AccountTypeEnum.TAXABLE: 1.0,
                AccountTypeEnum.ROTH_IRA: 0.8,
                AccountTypeEnum.ROTH_401K: 0.8,
                AccountTypeEnum.TRADITIONAL_401K: 0.5,
                AccountTypeEnum.TRADITIONAL_IRA: 0.5,
                AccountTypeEnum.HSA: 0.6
            },
            # Tax-efficient assets can go anywhere
            'index_funds': {
                AccountTypeEnum.ROTH_IRA: 0.9,
                AccountTypeEnum.ROTH_401K: 0.9,
                AccountTypeEnum.TAXABLE: 0.8,
                AccountTypeEnum.HSA: 0.7,
                AccountTypeEnum.TRADITIONAL_401K: 0.6,
                AccountTypeEnum.TRADITIONAL_IRA: 0.6
            }
        }
    
    async def optimize_account_allocation(
        self,
        user_id: str,
        target_allocation: Dict[str, float],
        asset_characteristics: List[AssetCharacteristics],
        time_horizon: int = 30
    ) -> OptimizationResult:
        """
        Optimize asset allocation across all account types for maximum tax efficiency
        """
        logger.info(f"Starting account optimization for user {user_id}")
        
        # Get user's accounts and current holdings
        accounts = self._get_user_accounts(user_id)
        current_holdings = self._get_current_holdings(user_id)
        user_profile = self._get_user_profile(user_id)
        
        # Calculate account capacities
        account_capacities = self._calculate_account_capacities(
            accounts, user_profile
        )
        
        # Calculate current tax drag
        current_tax_drag = self._calculate_current_tax_drag(
            current_holdings, user_profile.marginal_tax_rate
        )
        
        # Run optimization algorithm
        optimal_allocation = self._optimize_asset_locations(
            target_allocation,
            asset_characteristics,
            account_capacities,
            user_profile
        )
        
        # Calculate optimized tax drag
        optimized_tax_drag = self._calculate_optimized_tax_drag(
            optimal_allocation, asset_characteristics, user_profile.marginal_tax_rate
        )
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_plan(
            current_holdings, optimal_allocation, account_capacities
        )
        
        # Calculate rebalancing trades needed
        rebalancing_trades = self._calculate_rebalancing_trades(
            current_holdings, optimal_allocation
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            account_capacities, asset_characteristics, user_profile
        )
        
        result = OptimizationResult(
            optimal_allocation=optimal_allocation,
            current_tax_drag=current_tax_drag,
            optimized_tax_drag=optimized_tax_drag,
            annual_tax_savings=current_tax_drag - optimized_tax_drag,
            implementation_steps=implementation_steps,
            rebalancing_trades=rebalancing_trades,
            confidence_score=confidence_score
        )
        
        # Store analysis in database
        await self._store_analysis_results(user_id, result)
        
        logger.info(
            f"Optimization complete. Potential annual tax savings: ${result.annual_tax_savings}"
        )
        
        return result
    
    def _get_user_accounts(self, user_id: str) -> List[TaxAccount]:
        """Get all tax accounts for user"""
        return self.db.query(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.is_active == True
        ).all()
    
    def _get_current_holdings(self, user_id: str) -> List[TaxAccountHolding]:
        """Get all current holdings across accounts"""
        return self.db.query(TaxAccountHolding).join(TaxAccount).filter(
            TaxAccount.user_id == user_id,
            TaxAccount.is_active == True
        ).all()
    
    def _get_user_profile(self, user_id: str) -> FinancialProfile:
        """Get user's financial profile"""
        return self.db.query(FinancialProfile).filter(
            FinancialProfile.user_id == user_id
        ).first()
    
    def _calculate_account_capacities(
        self,
        accounts: List[TaxAccount],
        user_profile: FinancialProfile
    ) -> List[AccountCapacity]:
        """Calculate available capacity in each account"""
        capacities = []
        
        for account in accounts:
            # Calculate contribution limit based on account type and user age
            contribution_limit = self.tax_utils.get_contribution_limit(
                account.account_type,
                user_profile.age,
                user_profile.filing_status,
                user_profile.annual_income
            )
            
            # Available space is limit minus current contributions
            available_space = max(0, contribution_limit - (account.annual_contribution or 0))
            
            # Plus any existing balance for reallocation
            available_space += account.current_balance
            
            # Determine optimal asset types for this account
            optimal_assets = self._get_optimal_assets_for_account(account.account_type)
            
            capacities.append(AccountCapacity(
                account_id=str(account.id),
                account_type=account.account_type,
                available_space=Decimal(str(available_space)),
                tax_treatment=account.tax_treatment,
                current_allocation=self._get_account_allocation(account),
                optimal_asset_types=optimal_assets
            ))
        
        return capacities
    
    def _get_optimal_assets_for_account(self, account_type: AccountTypeEnum) -> List[str]:
        """Get list of asset types optimal for this account type"""
        optimal_assets = []
        
        for asset_class, preferences in self.location_rules.items():
            if preferences.get(account_type, 0) >= 0.8:
                optimal_assets.append(asset_class)
        
        return optimal_assets
    
    def _get_account_allocation(self, account: TaxAccount) -> Dict[str, Decimal]:
        """Get current allocation within an account"""
        allocation = {}
        
        for holding in account.holdings:
            allocation[holding.symbol] = holding.market_value or Decimal('0')
        
        return allocation
    
    def _calculate_current_tax_drag(
        self,
        holdings: List[TaxAccountHolding],
        marginal_tax_rate: float
    ) -> Decimal:
        """Calculate current annual tax drag from holdings"""
        annual_tax_drag = Decimal('0')
        
        for holding in holdings:
            # Only taxable accounts contribute to tax drag
            if holding.account.tax_treatment == TaxTreatmentEnum.TAXABLE:
                # Tax on dividends
                dividend_tax = (
                    holding.market_value *
                    Decimal(str(holding.dividend_yield or 0)) *
                    Decimal(str(marginal_tax_rate))
                )
                
                # Tax on turnover (realized gains)
                turnover_tax = (
                    holding.market_value *
                    Decimal(str(holding.turnover_ratio or 0)) *
                    Decimal('0.15')  # Assume 15% capital gains rate
                )
                
                annual_tax_drag += dividend_tax + turnover_tax
        
        return annual_tax_drag
    
    def _optimize_asset_locations(
        self,
        target_allocation: Dict[str, float],
        asset_characteristics: List[AssetCharacteristics],
        account_capacities: List[AccountCapacity],
        user_profile: FinancialProfile
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Core optimization algorithm using linear programming approach
        """
        # Convert to optimization problem
        total_portfolio_value = sum(cap.available_space for cap in account_capacities)
        
        # Initialize allocation matrix
        allocation = {}
        for capacity in account_capacities:
            allocation[capacity.account_id] = {}
        
        # Sort assets by tax efficiency (least efficient first)
        sorted_assets = sorted(
            asset_characteristics,
            key=lambda x: x.tax_efficiency_score
        )
        
        # Allocate each asset to best available account
        for asset in sorted_assets:
            target_amount = Decimal(str(target_allocation.get(asset.symbol, 0))) * total_portfolio_value
            remaining_amount = target_amount
            
            # Get account preferences for this asset
            asset_class = asset.asset_class
            preferences = self.location_rules.get(asset_class, {})
            
            # Sort accounts by preference for this asset
            sorted_accounts = sorted(
                account_capacities,
                key=lambda x: preferences.get(x.account_type, 0),
                reverse=True
            )
            
            # Allocate to accounts in preference order
            for capacity in sorted_accounts:
                if remaining_amount <= 0:
                    break
                
                # How much can we put in this account?
                available = capacity.available_space - sum(
                    allocation[capacity.account_id].values()
                )
                
                if available > 0:
                    amount_to_allocate = min(remaining_amount, available)
                    allocation[capacity.account_id][asset.symbol] = amount_to_allocate
                    remaining_amount -= amount_to_allocate
            
            # If we couldn't allocate everything, put remainder in taxable
            if remaining_amount > 0:
                # Find taxable account
                taxable_accounts = [
                    cap for cap in account_capacities
                    if cap.account_type == AccountTypeEnum.TAXABLE
                ]
                
                if taxable_accounts:
                    taxable_id = taxable_accounts[0].account_id
                    if taxable_id not in allocation:
                        allocation[taxable_id] = {}
                    
                    allocation[taxable_id][asset.symbol] = allocation[taxable_id].get(
                        asset.symbol, Decimal('0')
                    ) + remaining_amount
        
        return allocation
    
    def _calculate_optimized_tax_drag(
        self,
        optimal_allocation: Dict[str, Dict[str, Decimal]],
        asset_characteristics: List[AssetCharacteristics],
        marginal_tax_rate: float
    ) -> Decimal:
        """Calculate tax drag after optimization"""
        tax_drag = Decimal('0')
        
        # Create asset lookup
        asset_lookup = {asset.symbol: asset for asset in asset_characteristics}
        
        for account_id, holdings in optimal_allocation.items():
            # Get account info
            account = self.db.query(TaxAccount).filter(
                TaxAccount.id == account_id
            ).first()
            
            if not account or account.tax_treatment != TaxTreatmentEnum.TAXABLE:
                continue  # Only taxable accounts have tax drag
            
            for symbol, amount in holdings.items():
                asset = asset_lookup.get(symbol)
                if not asset:
                    continue
                
                # Tax on dividends
                dividend_tax = (
                    amount * 
                    Decimal(str(asset.dividend_yield)) *
                    Decimal(str(marginal_tax_rate))
                )
                
                # Tax on turnover
                turnover_tax = (
                    amount *
                    Decimal(str(asset.turnover_ratio)) *
                    Decimal('0.15')  # Capital gains rate
                )
                
                tax_drag += dividend_tax + turnover_tax
        
        return tax_drag
    
    def _generate_implementation_plan(
        self,
        current_holdings: List[TaxAccountHolding],
        optimal_allocation: Dict[str, Dict[str, Decimal]],
        account_capacities: List[AccountCapacity]
    ) -> List[Dict]:
        """Generate step-by-step implementation plan"""
        steps = []
        
        # Step 1: Contribute to high-priority accounts first
        steps.append({
            'step': 1,
            'action': 'maximize_employer_match',
            'description': 'Contribute enough to 401(k) to get full employer match',
            'priority': 'high',
            'tax_benefit': 'immediate'
        })
        
        # Step 2: Max out HSA if available
        hsa_accounts = [
            cap for cap in account_capacities
            if cap.account_type == AccountTypeEnum.HSA
        ]
        
        if hsa_accounts:
            steps.append({
                'step': 2,
                'action': 'maximize_hsa',
                'description': 'Maximize HSA contribution (triple tax advantage)',
                'priority': 'high',
                'tax_benefit': 'triple_advantage'
            })
        
        # Step 3: Asset location moves
        relocation_moves = self._identify_relocation_moves(
            current_holdings, optimal_allocation
        )
        
        for i, move in enumerate(relocation_moves):
            steps.append({
                'step': len(steps) + 1,
                'action': 'relocate_asset',
                'description': f"Move {move['asset']} from {move['from_account']} to {move['to_account']}",
                'priority': move['priority'],
                'tax_benefit': move['estimated_benefit']
            })
        
        # Step 4: Rebalancing within accounts
        steps.append({
            'step': len(steps) + 1,
            'action': 'rebalance_accounts',
            'description': 'Rebalance within each account to target allocation',
            'priority': 'medium',
            'tax_benefit': 'maintenance'
        })
        
        return steps
    
    def _identify_relocation_moves(
        self,
        current_holdings: List[TaxAccountHolding],
        optimal_allocation: Dict[str, Dict[str, Decimal]]
    ) -> List[Dict]:
        """Identify specific asset relocation moves"""
        moves = []
        
        for holding in current_holdings:
            current_account_id = str(holding.account_id)
            symbol = holding.symbol
            
            # Find where this asset should optimally be located
            optimal_account_id = None
            max_allocation = Decimal('0')
            
            for account_id, allocations in optimal_allocation.items():
                if symbol in allocations and allocations[symbol] > max_allocation:
                    max_allocation = allocations[symbol]
                    optimal_account_id = account_id
            
            # If asset should be in a different account
            if optimal_account_id and optimal_account_id != current_account_id:
                current_account = holding.account
                
                # Estimate tax benefit of move
                benefit = self._estimate_relocation_benefit(holding, optimal_account_id)
                
                moves.append({
                    'asset': symbol,
                    'from_account': current_account.account_name,
                    'to_account': optimal_account_id,
                    'amount': holding.market_value,
                    'estimated_benefit': benefit,
                    'priority': 'high' if benefit > 1000 else 'medium'
                })
        
        return sorted(moves, key=lambda x: x['estimated_benefit'], reverse=True)
    
    def _estimate_relocation_benefit(
        self,
        holding: TaxAccountHolding,
        target_account_id: str
    ) -> Decimal:
        """Estimate annual tax benefit of relocating an asset"""
        target_account = self.db.query(TaxAccount).filter(
            TaxAccount.id == target_account_id
        ).first()
        
        if not target_account:
            return Decimal('0')
        
        current_tax_drag = Decimal('0')
        future_tax_drag = Decimal('0')
        
        # Calculate current tax drag
        if holding.account.tax_treatment == TaxTreatmentEnum.TAXABLE:
            current_tax_drag = (
                holding.market_value * 
                Decimal(str(holding.dividend_yield or 0)) *
                Decimal(str(holding.account.marginal_tax_rate or 0.22))
            )
        
        # Calculate future tax drag
        if target_account.tax_treatment == TaxTreatmentEnum.TAXABLE:
            future_tax_drag = (
                holding.market_value *
                Decimal(str(holding.dividend_yield or 0)) *
                Decimal(str(target_account.marginal_tax_rate or 0.22))
            )
        
        return current_tax_drag - future_tax_drag
    
    def _calculate_rebalancing_trades(
        self,
        current_holdings: List[TaxAccountHolding],
        optimal_allocation: Dict[str, Dict[str, Decimal]]
    ) -> List[Dict]:
        """Calculate specific trades needed for rebalancing"""
        trades = []
        
        # Group current holdings by account
        current_by_account = {}
        for holding in current_holdings:
            account_id = str(holding.account_id)
            if account_id not in current_by_account:
                current_by_account[account_id] = {}
            current_by_account[account_id][holding.symbol] = holding.market_value
        
        # Compare with optimal allocation
        for account_id, optimal_holdings in optimal_allocation.items():
            current_holdings_dict = current_by_account.get(account_id, {})
            
            for symbol, target_amount in optimal_holdings.items():
                current_amount = current_holdings_dict.get(symbol, Decimal('0'))
                difference = target_amount - current_amount
                
                if abs(difference) > Decimal('100'):  # Minimum trade threshold
                    trades.append({
                        'account_id': account_id,
                        'symbol': symbol,
                        'action': 'buy' if difference > 0 else 'sell',
                        'amount': abs(difference),
                        'current_position': current_amount,
                        'target_position': target_amount
                    })
        
        return trades
    
    def _calculate_confidence_score(
        self,
        account_capacities: List[AccountCapacity],
        asset_characteristics: List[AssetCharacteristics],
        user_profile: FinancialProfile
    ) -> float:
        """Calculate confidence score for optimization"""
        score = 1.0
        
        # Penalize if we don't have enough account diversity
        account_types = {cap.account_type for cap in account_capacities}
        if len(account_types) < 3:
            score -= 0.2
        
        # Penalize if asset data is incomplete
        incomplete_assets = sum(
            1 for asset in asset_characteristics
            if asset.tax_efficiency_score == 0
        )
        if incomplete_assets > 0:
            score -= 0.1 * (incomplete_assets / len(asset_characteristics))
        
        # Penalize if user profile is incomplete
        if not user_profile.marginal_tax_rate:
            score -= 0.3
        
        return max(0.0, score)
    
    async def _store_analysis_results(
        self,
        user_id: str,
        result: OptimizationResult
    ) -> None:
        """Store analysis results in database"""
        analysis = AssetLocationAnalysis(
            user_id=user_id,
            analysis_date=datetime.utcnow(),
            total_portfolio_value=sum(
                sum(holdings.values())
                for holdings in result.optimal_allocation.values()
            ),
            current_tax_drag=result.current_tax_drag,
            optimal_tax_drag=result.optimized_tax_drag,
            potential_savings=result.annual_tax_savings,
            recommendations=[
                step for step in result.implementation_steps
            ],
            implementation_steps=result.rebalancing_trades,
            confidence_score=result.confidence_score,
            data_completeness=result.confidence_score  # Simplified
        )
        
        self.db.add(analysis)
        await self.db.commit()
    
    async def get_contribution_priority_waterfall(
        self,
        user_id: str,
        annual_savings_capacity: Decimal
    ) -> List[Dict]:
        """
        Generate priority waterfall for contributions across account types
        """
        user_profile = self._get_user_profile(user_id)
        accounts = self._get_user_accounts(user_id)
        
        waterfall = []
        remaining_capacity = annual_savings_capacity
        
        # Priority 1: 401(k) employer match
        for account in accounts:
            if account.account_type in [AccountTypeEnum.TRADITIONAL_401K, AccountTypeEnum.ROTH_401K]:
                if account.employer_match_rate and account.employer_match_rate > 0:
                    match_contribution = min(
                        remaining_capacity,
                        account.employer_match_limit or Decimal('0')
                    )
                    
                    if match_contribution > 0:
                        waterfall.append({
                            'priority': 1,
                            'account_id': str(account.id),
                            'account_type': account.account_type.value,
                            'contribution_amount': match_contribution,
                            'reason': 'Employer match (100% return)',
                            'tax_benefit': match_contribution * Decimal('1.0')  # 100% match
                        })
                        remaining_capacity -= match_contribution
        
        # Priority 2: HSA (triple tax advantage)
        hsa_accounts = [
            acc for acc in accounts
            if acc.account_type == AccountTypeEnum.HSA
        ]
        
        if hsa_accounts and remaining_capacity > 0:
            hsa_limit = Decimal(str(self.tax_utils.get_contribution_limit(
                AccountTypeEnum.HSA, user_profile.age
            )))
            
            hsa_contribution = min(remaining_capacity, hsa_limit)
            
            waterfall.append({
                'priority': 2,
                'account_id': str(hsa_accounts[0].id),
                'account_type': AccountTypeEnum.HSA.value,
                'contribution_amount': hsa_contribution,
                'reason': 'HSA triple tax advantage',
                'tax_benefit': hsa_contribution * Decimal(str(user_profile.marginal_tax_rate))
            })
            remaining_capacity -= hsa_contribution
        
        # Priority 3: Roth IRA (if eligible)
        if remaining_capacity > 0:
            roth_limit = Decimal(str(self.tax_utils.get_contribution_limit(
                AccountTypeEnum.ROTH_IRA,
                user_profile.age,
                user_profile.filing_status,
                float(user_profile.annual_income)
            )))
            
            if roth_limit > 0:
                roth_contribution = min(remaining_capacity, roth_limit)
                
                waterfall.append({
                    'priority': 3,
                    'account_id': 'new_roth_ira',
                    'account_type': AccountTypeEnum.ROTH_IRA.value,
                    'contribution_amount': roth_contribution,
                    'reason': 'Tax-free growth and withdrawals',
                    'tax_benefit': roth_contribution * Decimal('0.2')  # Estimated benefit
                })
                remaining_capacity -= roth_contribution
        
        # Priority 4: Remaining 401(k) space
        if remaining_capacity > 0:
            for account in accounts:
                if account.account_type in [AccountTypeEnum.TRADITIONAL_401K, AccountTypeEnum.ROTH_401K]:
                    contribution_limit = Decimal(str(self.tax_utils.get_contribution_limit(
                        account.account_type, user_profile.age
                    )))
                    
                    already_contributed = sum(
                        w['contribution_amount'] for w in waterfall
                        if w['account_id'] == str(account.id)
                    )
                    
                    remaining_401k_space = contribution_limit - already_contributed
                    
                    if remaining_401k_space > 0:
                        contribution_401k = min(remaining_capacity, remaining_401k_space)
                        
                        waterfall.append({
                            'priority': 4,
                            'account_id': str(account.id),
                            'account_type': account.account_type.value,
                            'contribution_amount': contribution_401k,
                            'reason': 'Additional tax-deferred savings',
                            'tax_benefit': contribution_401k * Decimal(str(user_profile.marginal_tax_rate))
                        })
                        remaining_capacity -= contribution_401k
        
        # Priority 5: Taxable account
        if remaining_capacity > 0:
            waterfall.append({
                'priority': 5,
                'account_id': 'taxable',
                'account_type': AccountTypeEnum.TAXABLE.value,
                'contribution_amount': remaining_capacity,
                'reason': 'Additional investment savings',
                'tax_benefit': Decimal('0')
            })
        
        return waterfall
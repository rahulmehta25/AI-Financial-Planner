"""
Portfolio Rebalancing with Transaction Cost and Tax Optimization
Implements intelligent rebalancing strategies considering costs and taxes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import cvxpy as cp
from enum import Enum


class RebalanceFrequency(Enum):
    """Rebalancing frequency options"""
    DAILY = 1
    WEEKLY = 7
    MONTHLY = 30
    QUARTERLY = 90
    SEMI_ANNUALLY = 180
    ANNUALLY = 365
    THRESHOLD_BASED = -1  # Rebalance when threshold exceeded


@dataclass
class TransactionCost:
    """Transaction cost structure"""
    fixed_cost: float = 0.0  # Fixed cost per trade
    variable_cost: float = 0.001  # Proportional cost (e.g., 0.1%)
    bid_ask_spread: float = 0.0005  # Half-spread
    market_impact: float = 0.0  # Price impact function coefficient
    
@dataclass
class TaxRates:
    """Tax rate structure"""
    short_term_capital_gains: float = 0.37  # Ordinary income rate
    long_term_capital_gains: float = 0.20  # LTCG rate
    state_tax_rate: float = 0.05  # State tax rate
    tax_loss_harvest_threshold: float = 1000  # Min loss to harvest
    
@dataclass
class Holding:
    """Asset holding information"""
    asset_id: str
    quantity: float
    cost_basis: float
    purchase_date: datetime
    current_price: float
    
    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_gain(self) -> float:
        return self.current_value - (self.quantity * self.cost_basis)
    
    @property
    def holding_period_days(self) -> int:
        return (datetime.now() - self.purchase_date).days
    
    @property
    def is_long_term(self) -> bool:
        return self.holding_period_days > 365
    
@dataclass
class RebalanceResult:
    """Result of rebalancing optimization"""
    trades: Dict[str, float]  # Asset -> quantity to trade (+ buy, - sell)
    transaction_costs: float
    tax_impact: float
    tracking_error: float
    turnover: float
    implementation_shortfall: float


class TaxAwareRebalancer:
    """
    Tax-aware portfolio rebalancing with transaction cost optimization
    """
    
    def __init__(
        self,
        transaction_cost: Optional[TransactionCost] = None,
        tax_rates: Optional[TaxRates] = None
    ):
        self.transaction_cost = transaction_cost or TransactionCost()
        self.tax_rates = tax_rates or TaxRates()
        self.wash_sale_window = 30  # Days for wash sale rule
        
    def optimize_rebalance(
        self,
        current_holdings: List[Holding],
        target_weights: Dict[str, float],
        portfolio_value: float,
        constraints: Optional[Dict] = None
    ) -> RebalanceResult:
        """
        Optimize rebalancing considering taxes and transaction costs
        
        Args:
            current_holdings: Current portfolio holdings
            target_weights: Target portfolio weights
            portfolio_value: Total portfolio value
            constraints: Optional constraints
            
        Returns:
            Optimal rebalancing trades
        """
        # Organize holdings by asset
        holdings_dict = {}
        for holding in current_holdings:
            if holding.asset_id not in holdings_dict:
                holdings_dict[holding.asset_id] = []
            holdings_dict[holding.asset_id].append(holding)
            
        # Get all assets
        all_assets = list(set(list(holdings_dict.keys()) + list(target_weights.keys())))
        n_assets = len(all_assets)
        
        # Current weights
        current_weights = np.zeros(n_assets)
        current_values = np.zeros(n_assets)
        
        for i, asset in enumerate(all_assets):
            if asset in holdings_dict:
                asset_value = sum(h.current_value for h in holdings_dict[asset])
                current_values[i] = asset_value
                current_weights[i] = asset_value / portfolio_value
                
        # Target weights vector
        target_weights_vec = np.array([
            target_weights.get(asset, 0) for asset in all_assets
        ])
        
        # Optimization variables
        trades = cp.Variable(n_assets)  # Trade amounts (in dollars)
        
        # New weights after trading
        new_values = current_values + trades
        new_weights = new_values / cp.sum(new_values)
        
        # Transaction costs
        transaction_costs = self._calculate_transaction_costs(trades, all_assets)
        
        # Tax impact
        tax_impact = self._estimate_tax_impact(
            trades, 
            holdings_dict,
            all_assets
        )
        
        # Tracking error
        tracking_error = cp.norm(new_weights - target_weights_vec, 2)
        
        # Objective: minimize costs + tracking error
        alpha = constraints.get('tracking_error_penalty', 100) if constraints else 100
        objective = cp.Minimize(
            transaction_costs + tax_impact + alpha * tracking_error
        )
        
        # Constraints
        constraints_list = [
            cp.sum(new_values) == portfolio_value,  # Preserve total value
            new_values >= 0  # No negative holdings
        ]
        
        # Add custom constraints
        if constraints:
            if 'max_turnover' in constraints:
                turnover = cp.sum(cp.abs(trades)) / (2 * portfolio_value)
                constraints_list.append(turnover <= constraints['max_turnover'])
                
            if 'min_trade_size' in constraints:
                # This is non-convex, so we approximate
                min_size = constraints['min_trade_size']
                # trades should be 0 or >= min_size (approximation)
                
            if 'max_positions' in constraints:
                # Limit number of positions (also non-convex)
                pass
                
        # Solve
        problem = cp.Problem(objective, constraints_list)
        problem.solve(solver=cp.OSQP, verbose=False)
        
        if problem.status not in ["optimal", "optimal_inaccurate"]:
            # Fallback to simple rebalancing
            return self._simple_rebalance(
                current_weights,
                target_weights_vec,
                portfolio_value,
                all_assets
            )
            
        # Extract results
        optimal_trades = trades.value
        
        # Convert to trade dictionary
        trade_dict = {}
        for i, asset in enumerate(all_assets):
            if abs(optimal_trades[i]) > 1:  # Minimum $1 trade
                trade_dict[asset] = optimal_trades[i]
                
        # Calculate actual costs
        actual_transaction_cost = self._calculate_actual_transaction_cost(
            trade_dict,
            all_assets
        )
        
        actual_tax_impact = self._calculate_actual_tax_impact(
            trade_dict,
            holdings_dict
        )
        
        # Calculate turnover
        turnover = sum(abs(t) for t in trade_dict.values()) / (2 * portfolio_value)
        
        # Implementation shortfall estimate
        implementation_shortfall = self._estimate_implementation_shortfall(
            trade_dict,
            all_assets
        )
        
        return RebalanceResult(
            trades=trade_dict,
            transaction_costs=actual_transaction_cost,
            tax_impact=actual_tax_impact,
            tracking_error=float(tracking_error.value) if tracking_error.value else 0,
            turnover=turnover,
            implementation_shortfall=implementation_shortfall
        )
    
    def tax_loss_harvest(
        self,
        holdings: List[Holding],
        replacement_map: Dict[str, str],
        min_loss: Optional[float] = None
    ) -> List[Tuple[str, str, float]]:
        """
        Identify tax loss harvesting opportunities
        
        Args:
            holdings: Current holdings
            replacement_map: Map of asset -> replacement asset
            min_loss: Minimum loss threshold
            
        Returns:
            List of (sell_asset, buy_asset, amount) tuples
        """
        if min_loss is None:
            min_loss = self.tax_rates.tax_loss_harvest_threshold
            
        harvest_opportunities = []
        
        for holding in holdings:
            # Check for unrealized loss
            if holding.unrealized_gain < -min_loss:
                # Check wash sale rule
                if self._check_wash_sale_safe(holding):
                    # Find replacement
                    if holding.asset_id in replacement_map:
                        replacement = replacement_map[holding.asset_id]
                        
                        # Calculate tax benefit
                        if holding.is_long_term:
                            tax_rate = self.tax_rates.long_term_capital_gains
                        else:
                            tax_rate = self.tax_rates.short_term_capital_gains
                            
                        tax_benefit = -holding.unrealized_gain * tax_rate
                        
                        harvest_opportunities.append((
                            holding.asset_id,
                            replacement,
                            holding.current_value,
                            tax_benefit
                        ))
                        
        # Sort by tax benefit
        harvest_opportunities.sort(key=lambda x: x[3], reverse=True)
        
        return harvest_opportunities
    
    def calculate_optimal_rebalance_frequency(
        self,
        historical_returns: pd.DataFrame,
        target_weights: Dict[str, float],
        transaction_cost: TransactionCost,
        initial_value: float = 100000
    ) -> RebalanceFrequency:
        """
        Determine optimal rebalancing frequency based on historical data
        
        Args:
            historical_returns: Historical return data
            target_weights: Target portfolio weights
            transaction_cost: Transaction cost structure
            initial_value: Initial portfolio value
            
        Returns:
            Optimal rebalancing frequency
        """
        frequencies = [
            RebalanceFrequency.MONTHLY,
            RebalanceFrequency.QUARTERLY,
            RebalanceFrequency.SEMI_ANNUALLY,
            RebalanceFrequency.ANNUALLY
        ]
        
        results = {}
        
        for frequency in frequencies:
            # Simulate rebalancing at this frequency
            performance = self._simulate_rebalancing(
                historical_returns,
                target_weights,
                frequency.value,
                transaction_cost,
                initial_value
            )
            
            # Calculate net performance (return - costs)
            results[frequency] = performance
            
        # Select frequency with best net performance
        optimal_freq = max(results, key=lambda k: results[k]['net_return'])
        
        return optimal_freq
    
    def threshold_based_rebalancing(
        self,
        current_weights: np.ndarray,
        target_weights: np.ndarray,
        threshold: float = 0.05
    ) -> bool:
        """
        Determine if rebalancing is needed based on threshold
        
        Args:
            current_weights: Current portfolio weights
            target_weights: Target portfolio weights
            threshold: Deviation threshold (e.g., 5%)
            
        Returns:
            True if rebalancing needed
        """
        # Check absolute deviation
        max_deviation = np.max(np.abs(current_weights - target_weights))
        
        # Check relative deviation for non-zero targets
        relative_deviations = []
        for i, target in enumerate(target_weights):
            if target > 0:
                rel_dev = abs((current_weights[i] - target) / target)
                relative_deviations.append(rel_dev)
                
        max_relative_deviation = max(relative_deviations) if relative_deviations else 0
        
        return max_deviation > threshold or max_relative_deviation > threshold
    
    def create_rebalancing_schedule(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: RebalanceFrequency,
        blackout_periods: Optional[List[Tuple[datetime, datetime]]] = None
    ) -> List[datetime]:
        """
        Create rebalancing schedule with blackout periods
        
        Args:
            start_date: Start date
            end_date: End date
            frequency: Rebalancing frequency
            blackout_periods: List of (start, end) blackout periods
            
        Returns:
            List of rebalancing dates
        """
        rebalance_dates = []
        current_date = start_date
        
        while current_date <= end_date:
            # Check if in blackout period
            in_blackout = False
            if blackout_periods:
                for blackout_start, blackout_end in blackout_periods:
                    if blackout_start <= current_date <= blackout_end:
                        in_blackout = True
                        break
                        
            if not in_blackout:
                rebalance_dates.append(current_date)
                
            # Move to next date based on frequency
            if frequency == RebalanceFrequency.DAILY:
                current_date += timedelta(days=1)
            elif frequency == RebalanceFrequency.WEEKLY:
                current_date += timedelta(days=7)
            elif frequency == RebalanceFrequency.MONTHLY:
                # Move to same day next month
                if current_date.month == 12:
                    current_date = current_date.replace(
                        year=current_date.year + 1,
                        month=1
                    )
                else:
                    current_date = current_date.replace(
                        month=current_date.month + 1
                    )
            elif frequency == RebalanceFrequency.QUARTERLY:
                # Move 3 months forward
                for _ in range(3):
                    if current_date.month == 12:
                        current_date = current_date.replace(
                            year=current_date.year + 1,
                            month=1
                        )
                    else:
                        current_date = current_date.replace(
                            month=current_date.month + 1
                        )
            elif frequency == RebalanceFrequency.ANNUALLY:
                current_date = current_date.replace(year=current_date.year + 1)
                
        return rebalance_dates
    
    def _calculate_transaction_costs(
        self,
        trades: cp.Variable,
        assets: List[str]
    ) -> cp.Expression:
        """Calculate transaction costs for trades"""
        # Variable costs (proportional to trade value)
        variable_costs = self.transaction_cost.variable_cost * cp.sum(cp.abs(trades))
        
        # Bid-ask spread costs
        spread_costs = self.transaction_cost.bid_ask_spread * cp.sum(cp.abs(trades))
        
        # Market impact (quadratic in trade size for large trades)
        if self.transaction_cost.market_impact > 0:
            market_impact = self.transaction_cost.market_impact * cp.sum(cp.square(trades))
        else:
            market_impact = 0
            
        return variable_costs + spread_costs + market_impact
    
    def _estimate_tax_impact(
        self,
        trades: cp.Variable,
        holdings_dict: Dict[str, List[Holding]],
        assets: List[str]
    ) -> cp.Expression:
        """Estimate tax impact of trades"""
        # Simplified tax impact estimate
        # In practice, this would be more complex
        tax_impact = 0
        
        for i, asset in enumerate(assets):
            if asset in holdings_dict:
                # Estimate tax on sales (negative trades)
                # Use average tax rate for simplification
                avg_tax_rate = (
                    self.tax_rates.short_term_capital_gains * 0.3 +
                    self.tax_rates.long_term_capital_gains * 0.7
                )
                
                # Only tax gains, not losses
                # This is a simplification
                tax_impact += cp.maximum(0, -trades[i] * avg_tax_rate * 0.1)
                
        return tax_impact
    
    def _calculate_actual_transaction_cost(
        self,
        trades: Dict[str, float],
        assets: List[str]
    ) -> float:
        """Calculate actual transaction costs"""
        total_cost = 0
        
        for asset, trade_value in trades.items():
            # Fixed cost per trade
            if trade_value != 0:
                total_cost += self.transaction_cost.fixed_cost
                
            # Variable costs
            total_cost += abs(trade_value) * self.transaction_cost.variable_cost
            
            # Bid-ask spread
            total_cost += abs(trade_value) * self.transaction_cost.bid_ask_spread
            
            # Market impact (simplified)
            if self.transaction_cost.market_impact > 0:
                total_cost += self.transaction_cost.market_impact * (trade_value ** 2)
                
        return total_cost
    
    def _calculate_actual_tax_impact(
        self,
        trades: Dict[str, float],
        holdings_dict: Dict[str, List[Holding]]
    ) -> float:
        """Calculate actual tax impact of trades"""
        total_tax = 0
        
        for asset, trade_value in trades.items():
            if trade_value < 0 and asset in holdings_dict:  # Selling
                # Determine which lots to sell (FIFO for simplicity)
                holdings = sorted(
                    holdings_dict[asset],
                    key=lambda h: h.purchase_date
                )
                
                remaining_to_sell = abs(trade_value)
                
                for holding in holdings:
                    if remaining_to_sell <= 0:
                        break
                        
                    sell_value = min(remaining_to_sell, holding.current_value)
                    sell_ratio = sell_value / holding.current_value
                    
                    # Calculate gain
                    cost_basis = holding.cost_basis * holding.quantity * sell_ratio
                    gain = sell_value - cost_basis
                    
                    # Apply appropriate tax rate
                    if gain > 0:
                        if holding.is_long_term:
                            tax_rate = self.tax_rates.long_term_capital_gains
                        else:
                            tax_rate = self.tax_rates.short_term_capital_gains
                            
                        total_tax += gain * tax_rate
                        
                    remaining_to_sell -= sell_value
                    
        return total_tax
    
    def _check_wash_sale_safe(self, holding: Holding) -> bool:
        """Check if selling would violate wash sale rule"""
        # Simplified check - in practice would check transaction history
        return holding.holding_period_days > self.wash_sale_window
    
    def _simple_rebalance(
        self,
        current_weights: np.ndarray,
        target_weights: np.ndarray,
        portfolio_value: float,
        assets: List[str]
    ) -> RebalanceResult:
        """Simple rebalancing fallback"""
        trades = {}
        
        for i, asset in enumerate(assets):
            current_value = current_weights[i] * portfolio_value
            target_value = target_weights[i] * portfolio_value
            trade_value = target_value - current_value
            
            if abs(trade_value) > 1:  # Minimum $1 trade
                trades[asset] = trade_value
                
        transaction_costs = self._calculate_actual_transaction_cost(trades, assets)
        
        return RebalanceResult(
            trades=trades,
            transaction_costs=transaction_costs,
            tax_impact=0,
            tracking_error=np.linalg.norm(current_weights - target_weights),
            turnover=sum(abs(t) for t in trades.values()) / (2 * portfolio_value),
            implementation_shortfall=0
        )
    
    def _estimate_implementation_shortfall(
        self,
        trades: Dict[str, float],
        assets: List[str]
    ) -> float:
        """Estimate implementation shortfall from market impact"""
        # Simplified model
        total_shortfall = 0
        
        for asset, trade_value in trades.items():
            # Assume linear market impact
            impact = abs(trade_value) * self.transaction_cost.market_impact * 0.5
            total_shortfall += impact
            
        return total_shortfall
    
    def _simulate_rebalancing(
        self,
        historical_returns: pd.DataFrame,
        target_weights: Dict[str, float],
        frequency_days: int,
        transaction_cost: TransactionCost,
        initial_value: float
    ) -> Dict[str, float]:
        """Simulate rebalancing strategy on historical data"""
        portfolio_value = initial_value
        total_costs = 0
        rebalance_dates = []
        
        # Identify rebalance dates
        for i in range(0, len(historical_returns), frequency_days):
            rebalance_dates.append(i)
            
        # Simulate portfolio evolution
        current_weights = np.array([
            target_weights.get(asset, 0) for asset in historical_returns.columns
        ])
        
        for i, returns in historical_returns.iterrows():
            # Apply returns
            portfolio_return = np.sum(current_weights * returns.values)
            portfolio_value *= (1 + portfolio_return)
            
            # Update weights based on returns
            asset_returns = 1 + returns.values
            current_weights = (current_weights * asset_returns) / np.sum(current_weights * asset_returns)
            
            # Rebalance if scheduled
            if i in rebalance_dates:
                # Calculate rebalancing trades
                target_weights_array = np.array([
                    target_weights.get(asset, 0) for asset in historical_returns.columns
                ])
                
                trades = (target_weights_array - current_weights) * portfolio_value
                
                # Calculate costs
                cost = sum(abs(trade) * transaction_cost.variable_cost for trade in trades)
                total_costs += cost
                portfolio_value -= cost
                
                # Reset to target weights
                current_weights = target_weights_array
                
        # Calculate performance metrics
        total_return = (portfolio_value - initial_value) / initial_value
        net_return = total_return - (total_costs / initial_value)
        
        return {
            'total_return': total_return,
            'total_costs': total_costs,
            'net_return': net_return,
            'final_value': portfolio_value
        }
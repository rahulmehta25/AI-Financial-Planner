"""
Position Limits and Risk Controls

This module implements comprehensive position limit controls including:
- Concentration limits and diversification requirements
- Risk budgeting and allocation
- Stop-loss and take-profit triggers
- Margin requirements and leverage controls
- Dynamic position sizing based on volatility
- Circuit breakers and trading halts
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class LimitType(Enum):
    """Types of position limits"""
    CONCENTRATION = "concentration"
    RISK_BUDGET = "risk_budget"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    MARGIN = "margin"
    LEVERAGE = "leverage"
    VOLATILITY = "volatility"
    CORRELATION = "correlation"
    SECTOR = "sector"
    ASSET_CLASS = "asset_class"


class TriggerStatus(Enum):
    """Status of limit triggers"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    PENDING = "pending"


@dataclass
class PositionLimit:
    """Position limit configuration"""
    limit_id: str
    limit_type: LimitType
    threshold: float
    current_value: float
    max_value: float
    min_value: Optional[float] = None
    is_hard_limit: bool = True  # Hard limit stops trading, soft limit warns
    enabled: bool = True
    metadata: Dict = field(default_factory=dict)


@dataclass
class RiskBudget:
    """Risk budget allocation"""
    budget_id: str
    total_budget: float
    allocated: float
    consumed: float
    remaining: float
    allocations: Dict[str, float] = field(default_factory=dict)
    limits: Dict[str, float] = field(default_factory=dict)
    rebalance_frequency: str = "monthly"


@dataclass
class StopLossTrigger:
    """Stop-loss trigger configuration"""
    trigger_id: str
    position_id: str
    trigger_price: float
    trigger_type: str  # fixed, trailing, guaranteed
    current_price: float
    distance: float  # Distance from entry or current price
    status: TriggerStatus
    created_at: datetime
    triggered_at: Optional[datetime] = None
    trail_amount: Optional[float] = None
    trail_percentage: Optional[float] = None


@dataclass
class TakeProfitTrigger:
    """Take-profit trigger configuration"""
    trigger_id: str
    position_id: str
    trigger_price: float
    partial_exit: bool = False
    exit_percentage: float = 1.0
    current_price: float
    status: TriggerStatus
    created_at: datetime
    triggered_at: Optional[datetime] = None


@dataclass
class MarginRequirement:
    """Margin requirement details"""
    initial_margin: float
    maintenance_margin: float
    current_margin: float
    excess_margin: float
    margin_call_price: float
    liquidation_price: float
    leverage_ratio: float
    max_leverage: float


@dataclass
class CircuitBreaker:
    """Circuit breaker configuration"""
    breaker_id: str
    trigger_condition: str  # loss_threshold, volatility_spike, correlation_break
    threshold: float
    current_value: float
    cooldown_period: timedelta
    status: TriggerStatus
    last_triggered: Optional[datetime] = None
    auto_reset: bool = True


@dataclass
class PositionLimitReport:
    """Comprehensive position limit report"""
    timestamp: datetime
    limits: List[PositionLimit]
    risk_budget: RiskBudget
    stop_losses: List[StopLossTrigger]
    take_profits: List[TakeProfitTrigger]
    margin_requirements: MarginRequirement
    circuit_breakers: List[CircuitBreaker]
    violations: List[Dict]
    warnings: List[str]
    recommendations: List[str]


class PositionLimitsEngine:
    """
    Engine for managing position limits and risk controls
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize position limits engine
        
        Args:
            config: Configuration dictionary for limits
        """
        self.config = config or self._default_config()
        self.limits = self._initialize_limits()
        self.risk_budget = self._initialize_risk_budget()
        self.circuit_breakers = self._initialize_circuit_breakers()
        self.active_triggers = {
            'stop_loss': {},
            'take_profit': {}
        }
        
    def _default_config(self) -> Dict:
        """Default configuration for position limits"""
        return {
            # Concentration limits
            'max_position_size': 0.20,  # 20% of portfolio
            'max_sector_exposure': 0.30,  # 30% per sector
            'max_asset_class_exposure': 0.60,  # 60% per asset class
            'max_correlation': 0.80,  # Maximum correlation between positions
            
            # Risk budget
            'total_risk_budget': 0.10,  # 10% total portfolio risk
            'per_position_risk': 0.02,  # 2% risk per position
            'daily_loss_limit': 0.05,  # 5% daily loss limit
            'monthly_loss_limit': 0.15,  # 15% monthly loss limit
            
            # Stop-loss defaults
            'default_stop_loss': 0.05,  # 5% stop-loss
            'trailing_stop_distance': 0.03,  # 3% trailing stop
            'guaranteed_stop_premium': 0.002,  # 0.2% premium for guaranteed stops
            
            # Take-profit defaults
            'default_take_profit': 0.10,  # 10% take-profit
            'partial_profit_levels': [0.05, 0.08, 0.12],  # Partial exit levels
            'partial_profit_percentages': [0.33, 0.33, 0.34],  # Exit percentages
            
            # Margin and leverage
            'initial_margin': 0.50,  # 50% initial margin
            'maintenance_margin': 0.25,  # 25% maintenance margin
            'max_leverage': 2.0,  # 2:1 maximum leverage
            'margin_call_threshold': 0.30,  # 30% equity threshold
            
            # Volatility adjustments
            'volatility_scalar': True,  # Adjust position size by volatility
            'target_volatility': 0.15,  # 15% annualized volatility target
            'min_position_size': 0.01,  # 1% minimum position
            'max_position_volatility': 0.25,  # 25% max position volatility
            
            # Circuit breakers
            'daily_circuit_breaker': 0.07,  # 7% daily loss circuit breaker
            'volatility_circuit_breaker': 3.0,  # 3x normal volatility
            'correlation_circuit_breaker': 0.95,  # 95% correlation threshold
            'circuit_breaker_cooldown': 3600,  # 1 hour cooldown in seconds
        }
    
    def _initialize_limits(self) -> Dict[LimitType, PositionLimit]:
        """Initialize position limits from configuration"""
        limits = {}
        
        # Concentration limit
        limits[LimitType.CONCENTRATION] = PositionLimit(
            limit_id="LIM-CONC-001",
            limit_type=LimitType.CONCENTRATION,
            threshold=self.config['max_position_size'],
            current_value=0.0,
            max_value=self.config['max_position_size'],
            is_hard_limit=True
        )
        
        # Risk budget limit
        limits[LimitType.RISK_BUDGET] = PositionLimit(
            limit_id="LIM-RISK-001",
            limit_type=LimitType.RISK_BUDGET,
            threshold=self.config['total_risk_budget'],
            current_value=0.0,
            max_value=self.config['total_risk_budget'],
            is_hard_limit=True
        )
        
        # Leverage limit
        limits[LimitType.LEVERAGE] = PositionLimit(
            limit_id="LIM-LEV-001",
            limit_type=LimitType.LEVERAGE,
            threshold=self.config['max_leverage'],
            current_value=1.0,
            max_value=self.config['max_leverage'],
            min_value=0.5,
            is_hard_limit=True
        )
        
        # Sector exposure limit
        limits[LimitType.SECTOR] = PositionLimit(
            limit_id="LIM-SECT-001",
            limit_type=LimitType.SECTOR,
            threshold=self.config['max_sector_exposure'],
            current_value=0.0,
            max_value=self.config['max_sector_exposure'],
            is_hard_limit=False
        )
        
        # Asset class limit
        limits[LimitType.ASSET_CLASS] = PositionLimit(
            limit_id="LIM-ASSET-001",
            limit_type=LimitType.ASSET_CLASS,
            threshold=self.config['max_asset_class_exposure'],
            current_value=0.0,
            max_value=self.config['max_asset_class_exposure'],
            is_hard_limit=False
        )
        
        # Volatility limit
        limits[LimitType.VOLATILITY] = PositionLimit(
            limit_id="LIM-VOL-001",
            limit_type=LimitType.VOLATILITY,
            threshold=self.config['max_position_volatility'],
            current_value=0.0,
            max_value=self.config['max_position_volatility'],
            is_hard_limit=False
        )
        
        # Correlation limit
        limits[LimitType.CORRELATION] = PositionLimit(
            limit_id="LIM-CORR-001",
            limit_type=LimitType.CORRELATION,
            threshold=self.config['max_correlation'],
            current_value=0.0,
            max_value=self.config['max_correlation'],
            is_hard_limit=False
        )
        
        return limits
    
    def _initialize_risk_budget(self) -> RiskBudget:
        """Initialize risk budget allocation"""
        total_budget = self.config['total_risk_budget']
        
        return RiskBudget(
            budget_id="BUDGET-001",
            total_budget=total_budget,
            allocated=0.0,
            consumed=0.0,
            remaining=total_budget,
            allocations={},
            limits={
                'per_position': self.config['per_position_risk'],
                'daily': self.config['daily_loss_limit'],
                'monthly': self.config['monthly_loss_limit']
            },
            rebalance_frequency="monthly"
        )
    
    def _initialize_circuit_breakers(self) -> List[CircuitBreaker]:
        """Initialize circuit breakers"""
        breakers = []
        
        # Daily loss circuit breaker
        breakers.append(CircuitBreaker(
            breaker_id="CB-DAILY-001",
            trigger_condition="daily_loss",
            threshold=self.config['daily_circuit_breaker'],
            current_value=0.0,
            cooldown_period=timedelta(seconds=self.config['circuit_breaker_cooldown']),
            status=TriggerStatus.ACTIVE,
            auto_reset=True
        ))
        
        # Volatility spike circuit breaker
        breakers.append(CircuitBreaker(
            breaker_id="CB-VOL-001",
            trigger_condition="volatility_spike",
            threshold=self.config['volatility_circuit_breaker'],
            current_value=1.0,
            cooldown_period=timedelta(seconds=self.config['circuit_breaker_cooldown']),
            status=TriggerStatus.ACTIVE,
            auto_reset=True
        ))
        
        # Correlation breakdown circuit breaker
        breakers.append(CircuitBreaker(
            breaker_id="CB-CORR-001",
            trigger_condition="correlation_break",
            threshold=self.config['correlation_circuit_breaker'],
            current_value=0.0,
            cooldown_period=timedelta(seconds=self.config['circuit_breaker_cooldown'] * 2),
            status=TriggerStatus.ACTIVE,
            auto_reset=False
        ))
        
        return breakers
    
    def check_position_limits(
        self,
        position: Dict,
        portfolio: Dict,
        market_data: Dict
    ) -> Tuple[bool, List[str]]:
        """
        Check if position violates any limits
        
        Args:
            position: Proposed position details
            portfolio: Current portfolio state
            market_data: Current market data
            
        Returns:
            Tuple of (is_allowed, list_of_violations)
        """
        violations = []
        warnings = []
        
        # Check concentration limit
        position_size = position['value'] / portfolio['total_value']
        if position_size > self.limits[LimitType.CONCENTRATION].threshold:
            violations.append(f"Position size {position_size:.1%} exceeds limit {self.limits[LimitType.CONCENTRATION].threshold:.1%}")
        
        # Check risk budget
        position_risk = self._calculate_position_risk(position, market_data)
        if position_risk > self.risk_budget.remaining:
            violations.append(f"Position risk {position_risk:.1%} exceeds remaining budget {self.risk_budget.remaining:.1%}")
        
        # Check sector exposure
        sector_exposure = self._calculate_sector_exposure(position, portfolio)
        if sector_exposure > self.limits[LimitType.SECTOR].threshold:
            msg = f"Sector exposure {sector_exposure:.1%} exceeds limit {self.limits[LimitType.SECTOR].threshold:.1%}"
            if self.limits[LimitType.SECTOR].is_hard_limit:
                violations.append(msg)
            else:
                warnings.append(msg)
        
        # Check leverage
        leverage = self._calculate_leverage(portfolio)
        if leverage > self.limits[LimitType.LEVERAGE].threshold:
            violations.append(f"Leverage {leverage:.1f}x exceeds limit {self.limits[LimitType.LEVERAGE].threshold:.1f}x")
        
        # Check volatility
        position_volatility = market_data.get('volatility', 0.20)
        if position_volatility > self.limits[LimitType.VOLATILITY].threshold:
            msg = f"Position volatility {position_volatility:.1%} exceeds limit {self.limits[LimitType.VOLATILITY].threshold:.1%}"
            if self.limits[LimitType.VOLATILITY].is_hard_limit:
                violations.append(msg)
            else:
                warnings.append(msg)
        
        # Check circuit breakers
        for breaker in self.circuit_breakers:
            if breaker.status == TriggerStatus.TRIGGERED:
                violations.append(f"Circuit breaker {breaker.breaker_id} is triggered")
        
        is_allowed = len(violations) == 0
        
        # Log warnings even if trade is allowed
        for warning in warnings:
            logger.warning(warning)
        
        return is_allowed, violations
    
    def calculate_position_size(
        self,
        account_value: float,
        risk_per_trade: float,
        entry_price: float,
        stop_loss_price: float,
        volatility: Optional[float] = None,
        use_kelly: bool = False,
        win_rate: Optional[float] = None,
        risk_reward_ratio: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate optimal position size
        
        Args:
            account_value: Total account value
            risk_per_trade: Risk amount per trade (in currency)
            entry_price: Entry price for position
            stop_loss_price: Stop-loss price
            volatility: Asset volatility (for volatility-adjusted sizing)
            use_kelly: Use Kelly Criterion for sizing
            win_rate: Historical win rate (for Kelly)
            risk_reward_ratio: Risk/reward ratio (for Kelly)
            
        Returns:
            Dictionary with position sizing details
        """
        # Basic position sizing (fixed fractional)
        risk_amount = min(risk_per_trade, account_value * self.config['per_position_risk'])
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return {'shares': 0, 'position_value': 0, 'risk': 0}
        
        base_shares = risk_amount / price_risk
        
        # Apply volatility adjustment if enabled
        if self.config['volatility_scalar'] and volatility:
            target_vol = self.config['target_volatility']
            vol_scalar = min(target_vol / volatility, 2.0)  # Cap at 2x
            adjusted_shares = base_shares * vol_scalar
        else:
            adjusted_shares = base_shares
        
        # Apply Kelly Criterion if requested
        if use_kelly and win_rate and risk_reward_ratio:
            kelly_fraction = self._calculate_kelly_fraction(
                win_rate, risk_reward_ratio
            )
            # Use fractional Kelly (25% of full Kelly) for safety
            safe_kelly = kelly_fraction * 0.25
            kelly_position = account_value * safe_kelly / entry_price
            adjusted_shares = min(adjusted_shares, kelly_position)
        
        # Apply position limits
        max_position_value = account_value * self.config['max_position_size']
        max_shares = max_position_value / entry_price
        
        final_shares = min(adjusted_shares, max_shares)
        
        # Ensure minimum position size
        min_position_value = account_value * self.config['min_position_size']
        min_shares = min_position_value / entry_price
        
        if final_shares < min_shares:
            final_shares = 0  # Don't take position if below minimum
        
        position_value = final_shares * entry_price
        actual_risk = final_shares * price_risk
        
        return {
            'shares': int(final_shares),
            'position_value': position_value,
            'risk': actual_risk,
            'risk_percentage': actual_risk / account_value,
            'position_percentage': position_value / account_value,
            'volatility_adjustment': volatility if volatility else 1.0,
            'kelly_fraction': safe_kelly if use_kelly else None
        }
    
    def _calculate_kelly_fraction(
        self,
        win_rate: float,
        risk_reward_ratio: float
    ) -> float:
        """Calculate Kelly fraction for position sizing"""
        if risk_reward_ratio <= 0:
            return 0.0
        
        # Kelly formula: f = (p * b - q) / b
        # p = win probability, q = loss probability, b = win/loss ratio
        q = 1 - win_rate
        kelly = (win_rate * risk_reward_ratio - q) / risk_reward_ratio
        
        # Cap Kelly fraction at 25% for safety
        return min(max(kelly, 0), 0.25)
    
    def set_stop_loss(
        self,
        position_id: str,
        entry_price: float,
        current_price: float,
        stop_type: str = "fixed",
        stop_distance: Optional[float] = None,
        trail_amount: Optional[float] = None,
        trail_percentage: Optional[float] = None
    ) -> StopLossTrigger:
        """
        Set stop-loss for a position
        
        Args:
            position_id: Position identifier
            entry_price: Entry price of position
            current_price: Current market price
            stop_type: Type of stop (fixed, trailing, guaranteed)
            stop_distance: Distance from entry price (for fixed stops)
            trail_amount: Trailing amount in currency
            trail_percentage: Trailing percentage
            
        Returns:
            StopLossTrigger object
        """
        # Calculate trigger price based on stop type
        if stop_type == "fixed":
            if not stop_distance:
                stop_distance = self.config['default_stop_loss']
            trigger_price = entry_price * (1 - stop_distance)
            
        elif stop_type == "trailing":
            if not trail_percentage:
                trail_percentage = self.config['trailing_stop_distance']
            trigger_price = current_price * (1 - trail_percentage)
            
        elif stop_type == "guaranteed":
            if not stop_distance:
                stop_distance = self.config['default_stop_loss']
            # Guaranteed stops have a premium cost
            trigger_price = entry_price * (1 - stop_distance)
            trigger_price *= (1 - self.config['guaranteed_stop_premium'])
            
        else:
            raise ValueError(f"Unknown stop type: {stop_type}")
        
        # Create stop-loss trigger
        trigger = StopLossTrigger(
            trigger_id=f"SL-{position_id}-{datetime.now().timestamp()}",
            position_id=position_id,
            trigger_price=trigger_price,
            trigger_type=stop_type,
            current_price=current_price,
            distance=abs(current_price - trigger_price) / current_price,
            status=TriggerStatus.ACTIVE,
            created_at=datetime.now(),
            trail_amount=trail_amount,
            trail_percentage=trail_percentage
        )
        
        # Store in active triggers
        self.active_triggers['stop_loss'][position_id] = trigger
        
        logger.info(f"Stop-loss set for {position_id}: {trigger_price:.2f} ({stop_type})")
        
        return trigger
    
    def set_take_profit(
        self,
        position_id: str,
        entry_price: float,
        current_price: float,
        profit_target: Optional[float] = None,
        partial_exits: bool = False
    ) -> List[TakeProfitTrigger]:
        """
        Set take-profit targets for a position
        
        Args:
            position_id: Position identifier
            entry_price: Entry price of position
            current_price: Current market price
            profit_target: Profit target percentage
            partial_exits: Enable partial profit taking
            
        Returns:
            List of TakeProfitTrigger objects
        """
        triggers = []
        
        if partial_exits and self.config['partial_profit_levels']:
            # Create multiple partial exit triggers
            for i, level in enumerate(self.config['partial_profit_levels']):
                trigger_price = entry_price * (1 + level)
                exit_pct = self.config['partial_profit_percentages'][i]
                
                trigger = TakeProfitTrigger(
                    trigger_id=f"TP-{position_id}-{i}-{datetime.now().timestamp()}",
                    position_id=position_id,
                    trigger_price=trigger_price,
                    partial_exit=True,
                    exit_percentage=exit_pct,
                    current_price=current_price,
                    status=TriggerStatus.ACTIVE,
                    created_at=datetime.now()
                )
                triggers.append(trigger)
        else:
            # Single take-profit target
            if not profit_target:
                profit_target = self.config['default_take_profit']
            
            trigger_price = entry_price * (1 + profit_target)
            
            trigger = TakeProfitTrigger(
                trigger_id=f"TP-{position_id}-{datetime.now().timestamp()}",
                position_id=position_id,
                trigger_price=trigger_price,
                partial_exit=False,
                exit_percentage=1.0,
                current_price=current_price,
                status=TriggerStatus.ACTIVE,
                created_at=datetime.now()
            )
            triggers.append(trigger)
        
        # Store in active triggers
        self.active_triggers['take_profit'][position_id] = triggers
        
        logger.info(f"Take-profit set for {position_id}: {len(triggers)} targets")
        
        return triggers
    
    def update_trailing_stops(
        self,
        positions: Dict[str, Dict],
        market_prices: Dict[str, float]
    ) -> List[StopLossTrigger]:
        """
        Update trailing stop-losses based on current prices
        
        Args:
            positions: Current positions
            market_prices: Current market prices
            
        Returns:
            List of updated stop-loss triggers
        """
        updated_triggers = []
        
        for position_id, trigger in self.active_triggers['stop_loss'].items():
            if trigger.trigger_type != 'trailing' or trigger.status != TriggerStatus.ACTIVE:
                continue
            
            if position_id not in market_prices:
                continue
            
            current_price = market_prices[position_id]
            
            # Calculate new trigger price
            if trigger.trail_percentage:
                new_trigger_price = current_price * (1 - trigger.trail_percentage)
            elif trigger.trail_amount:
                new_trigger_price = current_price - trigger.trail_amount
            else:
                continue
            
            # Only move stop up (for long positions)
            if new_trigger_price > trigger.trigger_price:
                trigger.trigger_price = new_trigger_price
                trigger.current_price = current_price
                trigger.distance = abs(current_price - new_trigger_price) / current_price
                updated_triggers.append(trigger)
                
                logger.info(f"Trailing stop updated for {position_id}: {new_trigger_price:.2f}")
        
        return updated_triggers
    
    def check_triggers(
        self,
        positions: Dict[str, Dict],
        market_prices: Dict[str, float]
    ) -> Dict[str, List]:
        """
        Check if any triggers have been hit
        
        Args:
            positions: Current positions
            market_prices: Current market prices
            
        Returns:
            Dictionary of triggered stops and take-profits
        """
        triggered = {
            'stop_losses': [],
            'take_profits': []
        }
        
        # Check stop-losses
        for position_id, trigger in self.active_triggers['stop_loss'].items():
            if trigger.status != TriggerStatus.ACTIVE:
                continue
            
            if position_id not in market_prices:
                continue
            
            current_price = market_prices[position_id]
            
            # Check if stop is triggered (for long positions)
            if current_price <= trigger.trigger_price:
                trigger.status = TriggerStatus.TRIGGERED
                trigger.triggered_at = datetime.now()
                triggered['stop_losses'].append(trigger)
                
                logger.warning(f"Stop-loss triggered for {position_id} at {current_price:.2f}")
        
        # Check take-profits
        for position_id, triggers in self.active_triggers['take_profit'].items():
            if position_id not in market_prices:
                continue
            
            current_price = market_prices[position_id]
            
            for trigger in triggers:
                if trigger.status != TriggerStatus.ACTIVE:
                    continue
                
                # Check if take-profit is triggered (for long positions)
                if current_price >= trigger.trigger_price:
                    trigger.status = TriggerStatus.TRIGGERED
                    trigger.triggered_at = datetime.now()
                    triggered['take_profits'].append(trigger)
                    
                    logger.info(f"Take-profit triggered for {position_id} at {current_price:.2f}")
        
        return triggered
    
    def calculate_margin_requirements(
        self,
        portfolio_value: float,
        positions_value: float,
        cash_balance: float,
        borrowed_amount: float = 0
    ) -> MarginRequirement:
        """
        Calculate margin requirements for portfolio
        
        Args:
            portfolio_value: Total portfolio value
            positions_value: Value of all positions
            cash_balance: Available cash
            borrowed_amount: Amount borrowed on margin
            
        Returns:
            MarginRequirement object
        """
        # Calculate equity
        equity = portfolio_value - borrowed_amount
        
        # Calculate leverage ratio
        leverage_ratio = positions_value / equity if equity > 0 else 0
        
        # Calculate margin requirements
        initial_margin = positions_value * self.config['initial_margin']
        maintenance_margin = positions_value * self.config['maintenance_margin']
        
        # Calculate current margin (equity as % of positions)
        current_margin = equity / positions_value if positions_value > 0 else 1.0
        
        # Calculate excess margin
        excess_margin = equity - maintenance_margin
        
        # Calculate margin call price (price at which margin call occurs)
        # Simplified calculation
        if positions_value > 0:
            margin_call_price = (borrowed_amount + maintenance_margin) / positions_value
        else:
            margin_call_price = 0
        
        # Calculate liquidation price
        liquidation_margin = positions_value * 0.15  # 15% liquidation level
        if positions_value > 0:
            liquidation_price = (borrowed_amount + liquidation_margin) / positions_value
        else:
            liquidation_price = 0
        
        return MarginRequirement(
            initial_margin=initial_margin,
            maintenance_margin=maintenance_margin,
            current_margin=current_margin,
            excess_margin=excess_margin,
            margin_call_price=margin_call_price,
            liquidation_price=liquidation_price,
            leverage_ratio=leverage_ratio,
            max_leverage=self.config['max_leverage']
        )
    
    def check_circuit_breakers(
        self,
        portfolio_metrics: Dict[str, float]
    ) -> List[CircuitBreaker]:
        """
        Check and update circuit breaker status
        
        Args:
            portfolio_metrics: Current portfolio metrics
            
        Returns:
            List of triggered circuit breakers
        """
        triggered_breakers = []
        current_time = datetime.now()
        
        for breaker in self.circuit_breakers:
            # Check if in cooldown period
            if breaker.status == TriggerStatus.TRIGGERED and breaker.last_triggered:
                if current_time - breaker.last_triggered < breaker.cooldown_period:
                    continue
                elif breaker.auto_reset:
                    breaker.status = TriggerStatus.ACTIVE
                    logger.info(f"Circuit breaker {breaker.breaker_id} reset after cooldown")
            
            # Check trigger conditions
            if breaker.trigger_condition == "daily_loss":
                daily_loss = portfolio_metrics.get('daily_loss', 0)
                breaker.current_value = abs(daily_loss)
                
                if abs(daily_loss) >= breaker.threshold:
                    breaker.status = TriggerStatus.TRIGGERED
                    breaker.last_triggered = current_time
                    triggered_breakers.append(breaker)
                    logger.critical(f"Daily loss circuit breaker triggered: {daily_loss:.1%}")
            
            elif breaker.trigger_condition == "volatility_spike":
                volatility_ratio = portfolio_metrics.get('volatility_ratio', 1.0)
                breaker.current_value = volatility_ratio
                
                if volatility_ratio >= breaker.threshold:
                    breaker.status = TriggerStatus.TRIGGERED
                    breaker.last_triggered = current_time
                    triggered_breakers.append(breaker)
                    logger.critical(f"Volatility circuit breaker triggered: {volatility_ratio:.1f}x")
            
            elif breaker.trigger_condition == "correlation_break":
                max_correlation = portfolio_metrics.get('max_correlation', 0)
                breaker.current_value = max_correlation
                
                if max_correlation >= breaker.threshold:
                    breaker.status = TriggerStatus.TRIGGERED
                    breaker.last_triggered = current_time
                    triggered_breakers.append(breaker)
                    logger.critical(f"Correlation circuit breaker triggered: {max_correlation:.2f}")
        
        return triggered_breakers
    
    def allocate_risk_budget(
        self,
        positions: Dict[str, Dict],
        expected_returns: Dict[str, float],
        volatilities: Dict[str, float],
        correlations: np.ndarray
    ) -> RiskBudget:
        """
        Allocate risk budget across positions
        
        Args:
            positions: Current positions
            expected_returns: Expected returns by position
            volatilities: Volatilities by position
            correlations: Correlation matrix
            
        Returns:
            Updated RiskBudget object
        """
        # Risk parity allocation (simplified)
        n_positions = len(positions)
        
        if n_positions == 0:
            return self.risk_budget
        
        # Calculate equal risk contribution initially
        equal_risk = self.risk_budget.total_budget / n_positions
        
        # Adjust for expected returns (higher return gets more risk budget)
        allocations = {}
        total_score = 0
        
        for position_id, position in positions.items():
            # Score based on return/volatility ratio
            expected_return = expected_returns.get(position_id, 0.05)
            volatility = volatilities.get(position_id, 0.20)
            
            score = expected_return / volatility if volatility > 0 else 0
            score = max(score, 0.1)  # Minimum score
            
            allocations[position_id] = score
            total_score += score
        
        # Normalize allocations
        for position_id in allocations:
            allocations[position_id] = (allocations[position_id] / total_score) * self.risk_budget.total_budget
            
            # Apply per-position limit
            allocations[position_id] = min(
                allocations[position_id],
                self.risk_budget.limits['per_position']
            )
        
        # Update risk budget
        self.risk_budget.allocations = allocations
        self.risk_budget.allocated = sum(allocations.values())
        self.risk_budget.remaining = self.risk_budget.total_budget - self.risk_budget.allocated
        
        logger.info(f"Risk budget allocated: {self.risk_budget.allocated:.1%} of {self.risk_budget.total_budget:.1%}")
        
        return self.risk_budget
    
    def _calculate_position_risk(
        self,
        position: Dict,
        market_data: Dict
    ) -> float:
        """Calculate risk for a position"""
        volatility = market_data.get('volatility', 0.20)
        position_size = position['value'] / position.get('portfolio_value', 1000000)
        
        # Simple risk calculation: position size * volatility
        return position_size * volatility
    
    def _calculate_sector_exposure(
        self,
        position: Dict,
        portfolio: Dict
    ) -> float:
        """Calculate sector exposure including new position"""
        sector = position.get('sector', 'unknown')
        
        # Sum existing sector exposure
        sector_value = sum(
            p['value'] for p in portfolio.get('positions', {}).values()
            if p.get('sector') == sector
        )
        
        # Add new position
        sector_value += position['value']
        
        # Calculate percentage
        return sector_value / portfolio['total_value'] if portfolio['total_value'] > 0 else 0
    
    def _calculate_leverage(self, portfolio: Dict) -> float:
        """Calculate portfolio leverage"""
        total_positions = sum(p['value'] for p in portfolio.get('positions', {}).values())
        equity = portfolio.get('equity', portfolio['total_value'])
        
        return total_positions / equity if equity > 0 else 0
    
    def generate_limit_report(
        self,
        portfolio: Dict,
        market_data: Dict
    ) -> PositionLimitReport:
        """
        Generate comprehensive position limit report
        
        Args:
            portfolio: Current portfolio state
            market_data: Current market data
            
        Returns:
            PositionLimitReport object
        """
        # Update current values for all limits
        for limit_type, limit in self.limits.items():
            if limit_type == LimitType.CONCENTRATION:
                max_position = max(
                    (p['value'] / portfolio['total_value'] 
                     for p in portfolio.get('positions', {}).values()),
                    default=0
                )
                limit.current_value = max_position
            
            elif limit_type == LimitType.LEVERAGE:
                limit.current_value = self._calculate_leverage(portfolio)
        
        # Collect violations and warnings
        violations = []
        warnings = []
        
        for limit in self.limits.values():
            if limit.current_value > limit.threshold:
                violation = {
                    'limit_type': limit.limit_type.value,
                    'current': limit.current_value,
                    'threshold': limit.threshold,
                    'severity': 'high' if limit.is_hard_limit else 'medium'
                }
                
                if limit.is_hard_limit:
                    violations.append(violation)
                else:
                    warnings.append(f"{limit.limit_type.value}: {limit.current_value:.1%} > {limit.threshold:.1%}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            violations, warnings, portfolio
        )
        
        # Calculate margin requirements
        margin_req = self.calculate_margin_requirements(
            portfolio['total_value'],
            sum(p['value'] for p in portfolio.get('positions', {}).values()),
            portfolio.get('cash_balance', 0),
            portfolio.get('borrowed_amount', 0)
        )
        
        return PositionLimitReport(
            timestamp=datetime.now(),
            limits=list(self.limits.values()),
            risk_budget=self.risk_budget,
            stop_losses=list(self.active_triggers['stop_loss'].values()),
            take_profits=[
                tp for tps in self.active_triggers['take_profit'].values() 
                for tp in tps
            ],
            margin_requirements=margin_req,
            circuit_breakers=self.circuit_breakers,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _generate_recommendations(
        self,
        violations: List[Dict],
        warnings: List[str],
        portfolio: Dict
    ) -> List[str]:
        """Generate recommendations based on limit status"""
        recommendations = []
        
        # Violation-based recommendations
        for violation in violations:
            if violation['limit_type'] == 'concentration':
                recommendations.append("Reduce largest positions to improve diversification")
            elif violation['limit_type'] == 'leverage':
                recommendations.append("Reduce leverage by closing margined positions")
            elif violation['limit_type'] == 'risk_budget':
                recommendations.append("Risk budget exceeded - reduce position sizes or add hedges")
        
        # Warning-based recommendations
        if len(warnings) > 3:
            recommendations.append("Multiple risk warnings - consider de-risking portfolio")
        
        # Risk budget recommendations
        if self.risk_budget.remaining < 0.01:
            recommendations.append("Risk budget nearly exhausted - avoid new positions")
        
        # Circuit breaker recommendations
        triggered_breakers = [cb for cb in self.circuit_breakers if cb.status == TriggerStatus.TRIGGERED]
        if triggered_breakers:
            recommendations.append("Circuit breakers triggered - trading restricted until reset")
        
        # General risk management
        recommendations.extend([
            "Review and update stop-loss levels for all positions",
            "Consider partial profit taking on winning positions",
            "Monitor correlation changes during market stress",
            "Maintain adequate cash reserves for margin calls"
        ])
        
        return recommendations


if __name__ == "__main__":
    # Example usage
    engine = PositionLimitsEngine()
    
    # Test position sizing
    position_size = engine.calculate_position_size(
        account_value=100000,
        risk_per_trade=2000,
        entry_price=150,
        stop_loss_price=145,
        volatility=0.25,
        use_kelly=True,
        win_rate=0.6,
        risk_reward_ratio=2.0
    )
    
    print("Position Sizing:")
    print(f"  Shares: {position_size['shares']}")
    print(f"  Position Value: ${position_size['position_value']:.2f}")
    print(f"  Risk: ${position_size['risk']:.2f} ({position_size['risk_percentage']:.1%})")
    
    # Test stop-loss setting
    stop_loss = engine.set_stop_loss(
        position_id="AAPL-001",
        entry_price=150,
        current_price=155,
        stop_type="trailing",
        trail_percentage=0.05
    )
    
    print(f"\nStop-Loss Set:")
    print(f"  Trigger Price: ${stop_loss.trigger_price:.2f}")
    print(f"  Type: {stop_loss.trigger_type}")
    print(f"  Distance: {stop_loss.distance:.1%}")
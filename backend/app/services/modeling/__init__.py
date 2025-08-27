"""
Advanced Financial Modeling Engine

This package provides sophisticated financial modeling capabilities including:
- Monte Carlo simulation with regime-switching models
- Cash flow modeling with life events
- Goal-based planning optimization  
- Backtesting framework with historical scenarios

Key Components:
- monte_carlo: Advanced Monte Carlo simulation engine
- cash_flow: Comprehensive cash flow modeling
- goals: Goal-based planning and optimization
- backtesting: Historical scenario backtesting

Usage:
    from app.services.modeling import (
        AdvancedMonteCarloEngine,
        CashFlowModelingEngine, 
        MultiGoalOptimizer,
        PortfolioBacktester
    )
"""

from .monte_carlo import (
    AdvancedMonteCarloEngine,
    RegimeSwitchingModel,
    FatTailedDistribution,
    DynamicCorrelationModel,
    SimulationParams,
    SimulationResults,
    AssetParams,
    MarketRegime
)

from .cash_flow import (
    CashFlowModelingEngine,
    LifeEventModeler,
    TaxCalculator,
    IncomeStream,
    ExpenseItem,
    LifeEventDefinition,
    CashFlowProjection,
    CashFlowScenario,
    LifeEvent,
    IncomeType,
    ExpenseCategory,
    InflationAssumptions
)

from .goals import (
    MultiGoalOptimizer,
    GoalSuccessProbabilityCalculator,
    FinancialGoal,
    GoalAllocation,
    OptimizationConstraints,
    TradeOffAnalysis,
    GoalOptimizationResult,
    GoalPriority,
    GoalType,
    OptimizationObjective
)

from .backtesting import (
    PortfolioBacktester,
    StrategyComparison,
    MarketDataProvider,
    StrategyDefinition,
    BacktestResult,
    ComparisonResult,
    PerformanceMetrics,
    AssetData,
    BacktestPeriod,
    StrategyType,
    RebalanceFrequency
)

__all__ = [
    # Monte Carlo
    'AdvancedMonteCarloEngine',
    'RegimeSwitchingModel', 
    'FatTailedDistribution',
    'DynamicCorrelationModel',
    'SimulationParams',
    'SimulationResults',
    'AssetParams',
    'MarketRegime',
    
    # Cash Flow
    'CashFlowModelingEngine',
    'LifeEventModeler',
    'TaxCalculator',
    'IncomeStream',
    'ExpenseItem', 
    'LifeEventDefinition',
    'CashFlowProjection',
    'CashFlowScenario',
    'LifeEvent',
    'IncomeType',
    'ExpenseCategory',
    'InflationAssumptions',
    
    # Goals
    'MultiGoalOptimizer',
    'GoalSuccessProbabilityCalculator',
    'FinancialGoal',
    'GoalAllocation',
    'OptimizationConstraints', 
    'TradeOffAnalysis',
    'GoalOptimizationResult',
    'GoalPriority',
    'GoalType',
    'OptimizationObjective',
    
    # Backtesting
    'PortfolioBacktester',
    'StrategyComparison',
    'MarketDataProvider',
    'StrategyDefinition',
    'BacktestResult',
    'ComparisonResult',
    'PerformanceMetrics',
    'AssetData',
    'BacktestPeriod',
    'StrategyType',
    'RebalanceFrequency'
]

# Version info
__version__ = "1.0.0"
__author__ = "Financial Planning AI System"
__description__ = "Advanced Financial Modeling Engine with Monte Carlo, Cash Flow, Goals, and Backtesting"
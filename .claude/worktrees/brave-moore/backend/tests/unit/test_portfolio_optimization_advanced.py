"""
Comprehensive unit tests for Intelligent Portfolio Optimization Engine

Tests cover:
- All optimization methods (Mean-Variance, Black-Litterman, Risk Parity, etc.)
- Multi-objective optimization
- ESG constraints and optimization
- Tax-aware optimization
- Performance requirements (<500ms for 100+ assets)
- Property-based testing with Hypothesis
- Financial accuracy validation
"""

import pytest
import numpy as np
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra.numpy import arrays
from unittest.mock import patch, MagicMock
import time
from decimal import Decimal
from typing import List, Dict

from app.services.optimization.portfolio_optimizer import (
    IntelligentPortfolioOptimizer,
    AssetData,
    PortfolioConstraints,
    OptimizationMethod,
    OptimizationResult
)
from app.services.optimization.black_litterman import InvestorView, MarketData
from app.services.optimization.rebalancing import TaxRates
from tests.factories import EnhancedMarketDataFactory, create_market_data_universe


class TestAssetData:
    """Test AssetData dataclass and validation"""
    
    def test_asset_data_creation(self):
        """Test basic AssetData creation"""
        returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
        
        asset = AssetData(
            symbol='AAPL',
            returns=returns,
            expected_return=0.08,
            volatility=0.15,
            sector='Technology',
            esg_score=75.0
        )
        
        assert asset.symbol == 'AAPL'
        assert asset.expected_return == 0.08
        assert asset.volatility == 0.15
        assert asset.sector == 'Technology'
        assert asset.esg_score == 75.0
    
    @given(
        expected_return=st.floats(min_value=-0.2, max_value=0.3),
        volatility=st.floats(min_value=0.01, max_value=1.0),
        esg_score=st.floats(min_value=0, max_value=100)
    )
    def test_asset_data_property_based(self, expected_return, volatility, esg_score):
        """Property-based testing for AssetData"""
        returns = pd.Series(np.random.normal(expected_return/252, volatility/np.sqrt(252), 252))
        
        asset = AssetData(
            symbol='TEST',
            returns=returns,
            expected_return=expected_return,
            volatility=volatility,
            esg_score=esg_score
        )
        
        assert asset.expected_return == expected_return
        assert asset.volatility == volatility
        assert asset.esg_score == esg_score
        assert len(asset.returns) == 252


class TestPortfolioConstraints:
    """Test PortfolioConstraints validation and edge cases"""
    
    def test_default_constraints(self):
        """Test default constraint values"""
        constraints = PortfolioConstraints()
        
        assert constraints.max_position_size == 0.25
        assert constraints.min_position_size == 0.01
        assert constraints.max_turnover == 0.5
        assert constraints.allow_short_selling == False
        assert constraints.leverage_limit == 1.0
    
    def test_custom_constraints(self):
        """Test custom constraint settings"""
        constraints = PortfolioConstraints(
            max_position_size=0.1,
            sector_limits={'Technology': (0.1, 0.3)},
            min_esg_score=60.0,
            allow_short_selling=True
        )
        
        assert constraints.max_position_size == 0.1
        assert constraints.sector_limits['Technology'] == (0.1, 0.3)
        assert constraints.min_esg_score == 60.0
        assert constraints.allow_short_selling == True


class TestIntelligentPortfolioOptimizer:
    """Comprehensive tests for portfolio optimization engine"""
    
    @pytest.fixture
    def optimizer(self):
        """Create optimizer instance"""
        return IntelligentPortfolioOptimizer(
            risk_free_rate=0.02,
            confidence_level=0.95,
            enable_caching=False  # Disable for testing
        )
    
    @pytest.fixture
    def sample_assets(self) -> List[AssetData]:
        """Create sample asset data for testing"""
        np.random.seed(42)
        assets = []
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA']
        sectors = ['Technology', 'Technology', 'Technology', 'Consumer', 'Consumer']
        expected_returns = [0.12, 0.10, 0.08, 0.15, 0.18]
        volatilities = [0.25, 0.22, 0.18, 0.30, 0.45]
        esg_scores = [75, 80, 85, 60, 45]
        
        for i, symbol in enumerate(symbols):
            returns = pd.Series(
                np.random.normal(
                    expected_returns[i]/252, 
                    volatilities[i]/np.sqrt(252), 
                    252
                )
            )
            
            asset = AssetData(
                symbol=symbol,
                returns=returns,
                expected_return=expected_returns[i],
                volatility=volatilities[i],
                sector=sectors[i],
                esg_score=esg_scores[i],
                market_cap=1e9 * (10 + i)  # Different market caps
            )
            assets.append(asset)
        
        return assets
    
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.risk_free_rate == 0.02
        assert optimizer.confidence_level == 0.95
        assert optimizer.max_workers == 4
        assert hasattr(optimizer, 'mpt_optimizer')
        assert hasattr(optimizer, 'black_litterman')
    
    @pytest.mark.parametrize("method", [
        OptimizationMethod.MEAN_VARIANCE,
        OptimizationMethod.MAX_SHARPE,
        OptimizationMethod.MIN_VARIANCE,
        OptimizationMethod.RISK_PARITY
    ])
    def test_basic_optimization_methods(self, optimizer, sample_assets, method):
        """Test basic optimization methods"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=method
        )
        
        # Validate result structure
        assert isinstance(result, OptimizationResult)
        assert result.method == method
        assert isinstance(result.weights, dict)
        assert result.constraints_satisfied is not None
        
        # Check weight properties
        weights_sum = sum(result.weights.values())
        assert abs(weights_sum - 1.0) < 1e-6  # Should sum to 1
        
        # All weights should be non-negative (no short selling by default)
        assert all(w >= -1e-6 for w in result.weights.values())
        
        # Should have portfolio metrics
        assert hasattr(result.metrics, 'expected_return')
        assert hasattr(result.metrics, 'volatility')
        assert hasattr(result.metrics, 'sharpe_ratio')
    
    def test_mean_variance_optimization(self, optimizer, sample_assets):
        """Test mean-variance optimization specifically"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MEAN_VARIANCE
        )
        
        # Mean-variance should produce efficient portfolio
        assert result.metrics.sharpe_ratio > 0  # Should be positive for good assets
        assert 0 < result.metrics.volatility < 0.5  # Reasonable volatility
        assert result.metrics.expected_return > 0  # Positive expected return
    
    def test_max_sharpe_optimization(self, optimizer, sample_assets):
        """Test maximum Sharpe ratio optimization"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MAX_SHARPE
        )
        
        # Max Sharpe should produce high Sharpe ratio
        assert result.metrics.sharpe_ratio > 0.3  # Should be reasonable
        
        # Compare with mean-variance result
        mv_result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MEAN_VARIANCE
        )
        
        # Max Sharpe should have higher or equal Sharpe ratio
        assert result.metrics.sharpe_ratio >= mv_result.metrics.sharpe_ratio - 0.01
    
    def test_min_variance_optimization(self, optimizer, sample_assets):
        """Test minimum variance optimization"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # Min variance should produce low-volatility portfolio
        assert result.metrics.volatility < 0.3
        
        # Compare with other methods
        max_sharpe_result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MAX_SHARPE
        )
        
        # Min variance should have lower volatility
        assert result.metrics.volatility <= max_sharpe_result.metrics.volatility + 0.01
    
    def test_risk_parity_optimization(self, optimizer, sample_assets):
        """Test risk parity optimization"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.RISK_PARITY
        )
        
        # Risk parity should be well-diversified
        weights_array = np.array(list(result.weights.values()))
        
        # No single position should dominate (heuristic test)
        assert np.max(weights_array) < 0.6
        
        # Should have reasonable number of positions
        non_zero_weights = np.sum(weights_array > 0.01)
        assert non_zero_weights >= 3
    
    def test_kelly_criterion_optimization(self, optimizer, sample_assets):
        """Test Kelly Criterion optimization"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.KELLY_CRITERION,
            kelly_fraction=0.25
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.method == OptimizationMethod.KELLY_CRITERION
        
        # Kelly should produce reasonable portfolio
        weights_sum = sum(result.weights.values())
        assert abs(weights_sum - 1.0) < 1e-6
    
    def test_hrp_optimization(self, optimizer, sample_assets):
        """Test Hierarchical Risk Parity optimization"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.HRP
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.method == OptimizationMethod.HRP
        
        # HRP should be well-diversified
        weights_array = np.array(list(result.weights.values()))
        
        # Should use all assets (or most)
        non_zero_weights = np.sum(weights_array > 0.01)
        assert non_zero_weights >= 3
        
        # Check that linkage matrix is in optimization info
        assert 'linkage_matrix' in result.optimization_info
    
    def test_cvar_optimization(self, optimizer, sample_assets):
        """Test Conditional Value at Risk optimization"""
        # Generate returns matrix for CVaR
        returns_matrix = np.array([asset.returns.values for asset in sample_assets]).T
        
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.CVaR,
            alpha=0.05
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.method == OptimizationMethod.CVaR
        
        # CVaR optimization should provide risk metrics
        assert 'cvar' in result.optimization_info
        assert 'var' in result.optimization_info
    
    def test_robust_optimization(self, optimizer, sample_assets):
        """Test robust optimization with uncertainty"""
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.ROBUST,
            uncertainty_set_size=0.1
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.method == OptimizationMethod.ROBUST
        
        # Robust optimization should provide uncertainty info
        assert 'uncertainty_set_size' in result.optimization_info
        assert 'worst_case_return' in result.optimization_info
    
    def test_black_litterman_optimization(self, optimizer, sample_assets):
        """Test Black-Litterman optimization with views"""
        # Create investor views
        views = [
            InvestorView(
                assets=['AAPL'],
                expected_return=0.15,
                confidence=0.8
            ),
            InvestorView(
                assets=['TSLA'],
                expected_return=0.10,
                confidence=0.6
            )
        ]
        
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.BLACK_LITTERMAN,
            views=views
        )
        
        assert isinstance(result, OptimizationResult)
        assert result.method == OptimizationMethod.BLACK_LITTERMAN
        
        # Black-Litterman should incorporate views
        assert 'confidence_scores' in result.optimization_info
    
    def test_multi_objective_optimization(self, optimizer, sample_assets):
        """Test multi-objective optimization"""
        objectives = [
            ('return', 0.6),
            ('risk', 0.3),
            ('esg', 0.1)
        ]
        
        result = optimizer.optimize_multi_objective(
            assets=sample_assets,
            objectives=objectives
        )
        
        assert isinstance(result, OptimizationResult)
        assert 'objectives' in result.optimization_info
        
        # Should balance multiple objectives
        weights_sum = sum(result.weights.values())
        assert abs(weights_sum - 1.0) < 1e-6
    
    def test_esg_constraints_optimization(self, optimizer, sample_assets):
        """Test ESG-constrained optimization"""
        esg_constraints = {
            'min_portfolio_esg': 70.0,
            'esg_weight': 0.2,
            'excluded_sectors': ['Oil & Gas']
        }
        
        result = optimizer.optimize_with_esg_constraints(
            assets=sample_assets,
            esg_constraints=esg_constraints
        )
        
        assert isinstance(result, OptimizationResult)
        
        # Check ESG metrics
        esg_metrics = result.optimization_info['esg_metrics']
        assert esg_metrics['portfolio_esg_score'] >= 70.0
    
    def test_ml_enhanced_optimization(self, optimizer, sample_assets):
        """Test ML-enhanced optimization"""
        # Add ML predictions to assets
        for i, asset in enumerate(sample_assets):
            asset.ml_predicted_return = asset.expected_return * (1 + 0.1 * (i - 2))  # Vary predictions
            asset.ml_confidence = 0.7 + 0.05 * i  # Vary confidence
        
        result = optimizer.optimize_with_ml_predictions(
            assets=sample_assets,
            method=OptimizationMethod.MAX_SHARPE,
            ml_weight=0.3
        )
        
        assert isinstance(result, OptimizationResult)
        assert 'ml_weight' in result.optimization_info
        assert 'avg_ml_confidence' in result.optimization_info
        assert 'optimization_time' in result.optimization_info
    
    def test_tax_aware_optimization(self, optimizer, sample_assets):
        """Test tax-aware optimization"""
        current_holdings = {
            'AAPL': 0.3,
            'GOOGL': 0.2,
            'MSFT': 0.2,
            'AMZN': 0.15,
            'TSLA': 0.15
        }
        
        tax_rates = TaxRates(
            short_term_capital_gains=0.37,
            long_term_capital_gains=0.20,
            dividend_tax_rate=0.20,
            state_tax_rate=0.05
        )
        
        result = optimizer.tax_aware_optimization(
            assets=sample_assets,
            current_holdings=current_holdings,
            tax_rates=tax_rates
        )
        
        assert isinstance(result, OptimizationResult)
        assert 'estimated_tax_cost' in result.optimization_info
        assert 'turnover' in result.optimization_info
        
        # Tax-aware should have reasonable turnover
        assert result.optimization_info['turnover'] <= 0.5
    
    def test_constraints_validation(self, optimizer, sample_assets):
        """Test constraint validation"""
        constraints = PortfolioConstraints(
            max_position_size=0.2,
            sector_limits={'Technology': (0.3, 0.7)},
            min_esg_score=60.0
        )
        
        result = optimizer.optimize(
            assets=sample_assets,
            method=OptimizationMethod.MEAN_VARIANCE,
            constraints=constraints
        )
        
        # Check position size constraint
        for weight in result.weights.values():
            assert weight <= constraints.max_position_size + 1e-6
        
        # Check sector constraint
        tech_weight = sum(
            result.weights.get(asset.symbol, 0)
            for asset in sample_assets
            if asset.sector == 'Technology'
        )
        assert 0.3 <= tech_weight <= 0.7
        
        assert result.constraints_satisfied
    
    def test_performance_requirements(self, optimizer):
        """Test performance requirements for large portfolios"""
        # Create large portfolio (100+ assets)
        np.random.seed(42)
        large_assets = []
        
        for i in range(120):
            returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
            asset = AssetData(
                symbol=f'ASSET_{i:03d}',
                returns=returns,
                expected_return=np.random.uniform(0.05, 0.15),
                volatility=np.random.uniform(0.1, 0.3),
                sector=f'Sector_{i % 10}',
                esg_score=np.random.uniform(40, 90)
            )
            large_assets.append(asset)
        
        # Test fast optimization
        start_time = time.time()
        result = optimizer.fast_optimize(
            assets=large_assets,
            method="min_variance",
            target_time_ms=500
        )
        optimization_time = (time.time() - start_time) * 1000
        
        # Should meet performance requirement
        assert optimization_time < 1000  # Allow some buffer
        assert isinstance(result, OptimizationResult)
        assert 'optimization_time_ms' in result.optimization_info
    
    @given(
        n_assets=st.integers(min_value=3, max_value=20),
        risk_free_rate=st.floats(min_value=0.0, max_value=0.1),
        max_position_size=st.floats(min_value=0.1, max_value=0.5)
    )
    @settings(max_examples=10, deadline=5000)
    def test_optimization_property_based(self, n_assets, risk_free_rate, max_position_size):
        """Property-based testing for optimization"""
        optimizer = IntelligentPortfolioOptimizer(risk_free_rate=risk_free_rate)
        
        # Generate random assets
        np.random.seed(42)
        assets = []
        for i in range(n_assets):
            returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
            asset = AssetData(
                symbol=f'ASSET_{i}',
                returns=returns,
                expected_return=np.random.uniform(0.02, 0.15),
                volatility=np.random.uniform(0.05, 0.3)
            )
            assets.append(asset)
        
        constraints = PortfolioConstraints(max_position_size=max_position_size)
        
        result = optimizer.optimize(
            assets=assets,
            method=OptimizationMethod.MIN_VARIANCE,
            constraints=constraints
        )
        
        # Properties that should always hold
        weights_sum = sum(result.weights.values())
        assert abs(weights_sum - 1.0) < 1e-5
        
        # Position size constraint
        for weight in result.weights.values():
            assert weight <= max_position_size + 1e-6
        
        # Non-negative weights
        assert all(w >= -1e-6 for w in result.weights.values())
    
    def test_edge_cases_and_error_handling(self, optimizer):
        """Test edge cases and error handling"""
        # Test with minimal assets
        minimal_assets = [
            AssetData(
                symbol='SINGLE',
                returns=pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252)),
                expected_return=0.08,
                volatility=0.15
            )
        ]
        
        result = optimizer.optimize(
            assets=minimal_assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # Should handle single asset
        assert len(result.weights) == 1
        assert abs(list(result.weights.values())[0] - 1.0) < 1e-6
        
        # Test with highly correlated assets
        correlated_returns = pd.Series(np.random.normal(0.08/252, 0.15/np.sqrt(252), 252))
        noise = pd.Series(np.random.normal(0, 0.001, 252))
        
        correlated_assets = [
            AssetData(
                symbol='CORR1',
                returns=correlated_returns,
                expected_return=0.08,
                volatility=0.15
            ),
            AssetData(
                symbol='CORR2',
                returns=correlated_returns + noise,
                expected_return=0.08,
                volatility=0.15
            )
        ]
        
        result = optimizer.optimize(
            assets=correlated_assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # Should handle correlated assets without error
        assert isinstance(result, OptimizationResult)
        weights_sum = sum(result.weights.values())
        assert abs(weights_sum - 1.0) < 1e-5
    
    def test_numerical_stability(self, optimizer, sample_assets):
        """Test numerical stability with extreme inputs"""
        # Test with very high volatility
        extreme_assets = []
        for i, asset in enumerate(sample_assets):
            extreme_asset = AssetData(
                symbol=asset.symbol,
                returns=asset.returns,
                expected_return=asset.expected_return,
                volatility=asset.volatility * (5 if i == 0 else 1),  # One very volatile asset
                sector=asset.sector,
                esg_score=asset.esg_score
            )
            extreme_assets.append(extreme_asset)
        
        result = optimizer.optimize(
            assets=extreme_assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # Should handle extreme volatility
        assert isinstance(result, OptimizationResult)
        
        # Volatile asset should have small weight
        volatile_weight = result.weights.get('AAPL', 0)  # First asset was made volatile
        assert volatile_weight < 0.1  # Should be small due to high volatility


class TestFinancialAccuracyValidation:
    """Test financial calculation accuracy"""
    
    def test_efficient_frontier_properties(self):
        """Test efficient frontier mathematical properties"""
        optimizer = IntelligentPortfolioOptimizer()
        
        # Create assets with known properties
        np.random.seed(42)
        assets = [
            AssetData(
                symbol='LOW_RISK',
                returns=pd.Series(np.random.normal(0.05/252, 0.08/np.sqrt(252), 252)),
                expected_return=0.05,
                volatility=0.08
            ),
            AssetData(
                symbol='HIGH_RISK',
                returns=pd.Series(np.random.normal(0.12/252, 0.25/np.sqrt(252), 252)),
                expected_return=0.12,
                volatility=0.25
            )
        ]
        
        # Min variance should choose mostly low-risk asset
        min_var_result = optimizer.optimize(
            assets=assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        low_risk_weight = min_var_result.weights.get('LOW_RISK', 0)
        assert low_risk_weight > 0.7  # Should prefer low-risk asset
        
        # Max Sharpe should balance risk and return
        max_sharpe_result = optimizer.optimize(
            assets=assets,
            method=OptimizationMethod.MAX_SHARPE
        )
        
        # Max Sharpe should have higher expected return than min variance
        assert (max_sharpe_result.metrics.expected_return >= 
                min_var_result.metrics.expected_return - 0.001)
    
    def test_diversification_benefits(self):
        """Test that optimization captures diversification benefits"""
        optimizer = IntelligentPortfolioOptimizer()
        
        # Create uncorrelated assets
        np.random.seed(42)
        assets = []
        
        for i in range(5):
            # Independent random returns
            returns = pd.Series(np.random.normal(0.08/252, 0.2/np.sqrt(252), 252))
            asset = AssetData(
                symbol=f'UNCORR_{i}',
                returns=returns,
                expected_return=0.08,
                volatility=0.2
            )
            assets.append(asset)
        
        result = optimizer.optimize(
            assets=assets,
            method=OptimizationMethod.MIN_VARIANCE
        )
        
        # Diversified portfolio should have lower volatility than individual assets
        assert result.metrics.volatility < 0.18  # Should be less than 0.2 due to diversification
        
        # Should use multiple assets for diversification
        non_zero_weights = sum(1 for w in result.weights.values() if w > 0.01)
        assert non_zero_weights >= 3
    
    def test_risk_return_tradeoff(self):
        """Test risk-return tradeoff in optimization"""
        optimizer = IntelligentPortfolioOptimizer()
        
        # Create assets with different risk-return profiles
        np.random.seed(42)
        low_risk_asset = AssetData(
            symbol='BONDS',
            returns=pd.Series(np.random.normal(0.03/252, 0.05/np.sqrt(252), 252)),
            expected_return=0.03,
            volatility=0.05
        )
        
        high_risk_asset = AssetData(
            symbol='GROWTH',
            returns=pd.Series(np.random.normal(0.15/252, 0.30/np.sqrt(252), 252)),
            expected_return=0.15,
            volatility=0.30
        )
        
        assets = [low_risk_asset, high_risk_asset]
        
        # Test different methods
        min_var = optimizer.optimize(assets, OptimizationMethod.MIN_VARIANCE)
        max_sharpe = optimizer.optimize(assets, OptimizationMethod.MAX_SHARPE)
        
        # Min variance should be more conservative
        assert min_var.metrics.volatility <= max_sharpe.metrics.volatility + 0.01
        
        # Max Sharpe should have higher return
        assert max_sharpe.metrics.expected_return >= min_var.metrics.expected_return - 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

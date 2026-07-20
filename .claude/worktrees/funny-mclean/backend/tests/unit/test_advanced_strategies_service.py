"""
Comprehensive unit tests for advanced strategies service.

Tests cover:
- Advanced portfolio optimization algorithms
- Factor-based investing strategies
- Alternative investment allocation
- Risk parity and volatility targeting
- Black-Litterman optimization
- Dynamic asset allocation
- ESG integration strategies
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple

from app.services.advanced_strategies import (
    AdvancedStrategiesService, BlackLittermanOptimizer, RiskParityOptimizer,
    FactorInvestingEngine, ESGIntegrationService, VolatilityTargetingEngine
)
from app.services.optimization.mpt import ModernPortfolioTheory
from app.services.optimization.factor_models import (
    FamaFrenchModel, CAPMModel, MultiFactorModel
)
from app.schemas.advanced_strategies import (
    OptimizationRequest, FactorExposure, ESGCriteria, VolatilityTarget
)


class TestAdvancedStrategiesService:
    """Test advanced strategies service functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_market_data_service(self):
        """Mock market data service."""
        mock = AsyncMock()
        # Mock historical returns data
        mock.get_historical_returns.return_value = {
            "SPY": np.array([0.08, 0.12, -0.05, 0.15, 0.09]),
            "QQQ": np.array([0.10, 0.18, -0.10, 0.22, 0.14]),
            "IWM": np.array([0.06, 0.14, -0.08, 0.18, 0.11]),
            "EFA": np.array([0.05, 0.10, -0.12, 0.13, 0.08]),
            "BND": np.array([0.02, 0.03, 0.04, 0.01, 0.03])
        }
        return mock
    
    @pytest.fixture
    def advanced_strategies_service(self, mock_db_session, mock_market_data_service):
        """Create advanced strategies service instance."""
        return AdvancedStrategiesService(
            db=mock_db_session,
            market_data_service=mock_market_data_service
        )
    
    @pytest.fixture
    def sample_universe(self):
        """Sample investment universe for testing."""
        return [
            {"symbol": "SPY", "name": "S&P 500 ETF", "asset_class": "US_EQUITY", "weight": 0.0},
            {"symbol": "QQQ", "name": "NASDAQ ETF", "asset_class": "US_GROWTH", "weight": 0.0},
            {"symbol": "IWM", "name": "Small Cap ETF", "asset_class": "US_SMALL_CAP", "weight": 0.0},
            {"symbol": "EFA", "name": "International ETF", "asset_class": "INTERNATIONAL", "weight": 0.0},
            {"symbol": "BND", "name": "Bond ETF", "asset_class": "BONDS", "weight": 0.0}
        ]
    
    async def test_mean_variance_optimization(self, advanced_strategies_service, sample_universe):
        """Test mean-variance optimization implementation."""
        
        optimization_request = OptimizationRequest(
            universe=sample_universe,
            objective="maximize_sharpe",
            constraints={
                "max_weight": 0.4,
                "min_weight": 0.05,
                "max_sector_concentration": 0.6
            },
            risk_tolerance=0.15
        )
        
        result = await advanced_strategies_service.optimize_portfolio_mean_variance(
            optimization_request
        )
        
        # Verify optimization results
        assert "weights" in result
        assert "expected_return" in result
        assert "expected_volatility" in result
        assert "sharpe_ratio" in result
        
        # Weights should sum to 1
        total_weight = sum(result["weights"].values())
        assert abs(total_weight - 1.0) < 1e-6
        
        # Constraints should be satisfied
        for weight in result["weights"].values():
            assert weight >= 0.05 - 1e-6  # Min weight constraint
            assert weight <= 0.4 + 1e-6   # Max weight constraint
    
    async def test_risk_parity_optimization(self, advanced_strategies_service, sample_universe):
        """Test risk parity optimization."""
        
        result = await advanced_strategies_service.optimize_risk_parity(sample_universe)
        
        # Risk contributions should be approximately equal
        risk_contributions = result["risk_contributions"]
        mean_contribution = np.mean(list(risk_contributions.values()))
        
        for contribution in risk_contributions.values():
            # Allow some tolerance for numerical optimization
            assert abs(contribution - mean_contribution) < 0.05
        
        # Portfolio should be diversified
        weights = result["weights"]
        max_weight = max(weights.values())
        assert max_weight < 0.6  # No single asset dominates
    
    async def test_black_litterman_integration(self, advanced_strategies_service, sample_universe):
        """Test Black-Litterman model integration."""
        
        # Market views/opinions
        views = [
            {"asset": "SPY", "expected_excess_return": 0.02, "confidence": 0.8},
            {"asset": "QQQ", "expected_excess_return": 0.03, "confidence": 0.6}
        ]
        
        result = await advanced_strategies_service.optimize_black_litterman(
            universe=sample_universe,
            market_views=views,
            risk_aversion=3.0
        )
        
        # Should incorporate views into optimization
        weights = result["weights"]
        
        # Assets with positive views should have reasonable weights
        assert weights["SPY"] > 0.1  # Positive view should increase allocation
        assert weights["QQQ"] > 0.1  # Positive view should increase allocation
        
        # Should have expected returns adjusted by views
        assert "adjusted_returns" in result
        assert "posterior_covariance" in result
    
    async def test_factor_based_optimization(self, advanced_strategies_service, sample_universe):
        """Test factor-based portfolio optimization."""
        
        target_factors = {
            "market_beta": 1.0,
            "size_factor": 0.2,   # Slight small-cap tilt
            "value_factor": 0.1,  # Slight value tilt
            "momentum_factor": 0.0,
            "quality_factor": 0.15
        }
        
        result = await advanced_strategies_service.optimize_factor_exposure(
            universe=sample_universe,
            target_factors=target_factors,
            tracking_error_limit=0.05
        )
        
        # Should achieve target factor exposures within tolerance
        actual_factors = result["factor_exposures"]
        
        for factor, target in target_factors.items():
            actual = actual_factors[factor]
            assert abs(actual - target) < 0.1, f"Factor {factor}: target {target}, actual {actual}"
        
        # Should respect tracking error limit
        assert result["tracking_error"] <= 0.05 + 1e-6
    
    async def test_volatility_targeting(self, advanced_strategies_service, sample_universe):
        """Test volatility targeting implementation."""
        
        target_volatility = 0.12  # 12% annualized volatility
        
        result = await advanced_strategies_service.optimize_volatility_targeting(
            universe=sample_universe,
            target_volatility=target_volatility
        )
        
        # Portfolio volatility should match target
        portfolio_vol = result["portfolio_volatility"]
        assert abs(portfolio_vol - target_volatility) < 0.01
        
        # Should provide volatility scaling factor
        assert "volatility_scalar" in result
        assert result["volatility_scalar"] > 0
    
    async def test_esg_integration(self, advanced_strategies_service, sample_universe):
        """Test ESG factor integration in optimization."""
        
        esg_criteria = ESGCriteria(
            min_esg_score=6.0,  # Out of 10
            exclude_sectors=["tobacco", "weapons", "fossil_fuels"],
            esg_weight=0.3  # 30% weight on ESG in optimization
        )
        
        # Mock ESG scores for universe
        with patch.object(advanced_strategies_service, '_get_esg_scores') as mock_esg:
            mock_esg.return_value = {
                "SPY": 7.5,
                "QQQ": 8.0,
                "IWM": 6.5,
                "EFA": 7.0,
                "BND": 8.5
            }
            
            result = await advanced_strategies_service.optimize_with_esg(
                universe=sample_universe,
                esg_criteria=esg_criteria
            )
            
            # All assets should meet minimum ESG score
            for symbol, score in result["esg_scores"].items():
                assert score >= esg_criteria.min_esg_score
            
            # Should show ESG-adjusted expected returns
            assert "esg_adjusted_returns" in result
    
    async def test_dynamic_asset_allocation(self, advanced_strategies_service, sample_universe):
        """Test dynamic asset allocation based on market conditions."""
        
        # Mock market regime indicators
        market_indicators = {
            "vix_level": 20.5,  # Moderate volatility
            "yield_curve_slope": 0.015,  # Positive slope
            "credit_spreads": 0.008,  # Normal spreads
            "momentum_signal": 0.05   # Slight positive momentum
        }
        
        result = await advanced_strategies_service.dynamic_asset_allocation(
            universe=sample_universe,
            market_indicators=market_indicators
        )
        
        # Should adjust allocations based on market conditions
        weights = result["weights"]
        
        # With moderate volatility, should have balanced allocation
        equity_weight = weights.get("SPY", 0) + weights.get("QQQ", 0) + weights.get("IWM", 0)
        bond_weight = weights.get("BND", 0)
        
        assert 0.4 <= equity_weight <= 0.8  # Reasonable equity allocation
        assert 0.2 <= bond_weight <= 0.6    # Reasonable bond allocation
        
        # Should provide regime analysis
        assert "market_regime" in result
        assert "allocation_rationale" in result
    
    @pytest.mark.benchmark
    async def test_optimization_performance(self, advanced_strategies_service, sample_universe, benchmark):
        """Benchmark optimization performance."""
        
        optimization_request = OptimizationRequest(
            universe=sample_universe,
            objective="maximize_sharpe",
            constraints={"max_weight": 0.5, "min_weight": 0.0}
        )
        
        # Optimization should complete within reasonable time
        result = benchmark(
            asyncio.run,
            advanced_strategies_service.optimize_portfolio_mean_variance(optimization_request)
        )
        
        assert result is not None
        assert "weights" in result


class TestBlackLittermanOptimizer:
    """Test Black-Litterman optimization implementation."""
    
    @pytest.fixture
    def bl_optimizer(self):
        """Create Black-Litterman optimizer."""
        return BlackLittermanOptimizer()
    
    @pytest.fixture
    def market_data(self):
        """Sample market data for Black-Litterman."""
        return {
            "returns": np.array([
                [0.10, 0.08, 0.06, 0.04],  # Asset 1
                [0.12, 0.10, 0.08, 0.06],  # Asset 2  
                [0.06, 0.04, 0.02, 0.08],  # Asset 3
                [0.02, 0.03, 0.01, 0.04]   # Asset 4
            ]).T,
            "market_caps": np.array([1000, 800, 600, 400]),  # Market capitalizations
            "risk_aversion": 3.0
        }
    
    def test_implied_returns_calculation(self, bl_optimizer, market_data):
        """Test calculation of implied equilibrium returns."""
        
        # Calculate covariance matrix
        cov_matrix = np.cov(market_data["returns"].T)
        
        # Calculate market weights
        total_market_cap = np.sum(market_data["market_caps"])
        market_weights = market_data["market_caps"] / total_market_cap
        
        implied_returns = bl_optimizer.calculate_implied_returns(
            covariance_matrix=cov_matrix,
            market_weights=market_weights,
            risk_aversion=market_data["risk_aversion"]
        )
        
        # Implied returns should be positive and reasonable
        assert len(implied_returns) == len(market_weights)
        assert all(ret > 0 for ret in implied_returns)
        assert all(ret < 0.5 for ret in implied_returns)  # Reasonable upper bound
    
    def test_view_incorporation(self, bl_optimizer, market_data):
        """Test incorporation of investor views."""
        
        # Define views
        views = [
            {"assets": [0], "expected_return": 0.15, "confidence": 0.8},  # Asset 0 will return 15%
            {"assets": [1, 2], "relative_return": 0.05, "confidence": 0.6}   # Asset 1 will outperform Asset 2 by 5%
        ]
        
        cov_matrix = np.cov(market_data["returns"].T)
        market_weights = market_data["market_caps"] / np.sum(market_data["market_caps"])
        
        posterior_returns, posterior_cov = bl_optimizer.incorporate_views(
            covariance_matrix=cov_matrix,
            market_weights=market_weights,
            views=views,
            risk_aversion=market_data["risk_aversion"]
        )
        
        # Posterior returns should be influenced by views
        assert len(posterior_returns) == len(market_weights)
        
        # Asset 0 expected return should be closer to view (15%)
        assert posterior_returns[0] > 0.10  # Should be elevated by positive view
        
        # Posterior covariance should account for view uncertainty
        assert posterior_cov.shape == cov_matrix.shape
        assert np.all(np.linalg.eigvals(posterior_cov) > 0)  # Should be positive definite
    
    def test_optimal_portfolio_calculation(self, bl_optimizer, market_data):
        """Test calculation of optimal Black-Litterman portfolio."""
        
        views = [
            {"assets": [0], "expected_return": 0.12, "confidence": 0.7}
        ]
        
        optimal_weights = bl_optimizer.calculate_optimal_portfolio(
            returns_data=market_data["returns"],
            market_caps=market_data["market_caps"],
            views=views,
            risk_aversion=market_data["risk_aversion"]
        )
        
        # Weights should sum to 1
        assert abs(np.sum(optimal_weights) - 1.0) < 1e-6
        
        # All weights should be non-negative (assuming no short selling)
        assert all(w >= -1e-6 for w in optimal_weights)
        
        # Asset with positive view should have higher weight than market cap would suggest
        market_weights = market_data["market_caps"] / np.sum(market_data["market_caps"])
        assert optimal_weights[0] > market_weights[0]


class TestRiskParityOptimizer:
    """Test risk parity optimization implementation."""
    
    @pytest.fixture
    def rp_optimizer(self):
        """Create risk parity optimizer."""
        return RiskParityOptimizer()
    
    @pytest.fixture
    def sample_covariance_matrix(self):
        """Sample covariance matrix for testing."""
        # 4x4 covariance matrix
        cov = np.array([
            [0.04, 0.02, 0.01, 0.005],
            [0.02, 0.06, 0.015, 0.008],
            [0.01, 0.015, 0.03, 0.006],
            [0.005, 0.008, 0.006, 0.01]
        ])
        return cov
    
    def test_equal_risk_contribution(self, rp_optimizer, sample_covariance_matrix):
        """Test equal risk contribution optimization."""
        
        weights = rp_optimizer.optimize_equal_risk_contribution(
            covariance_matrix=sample_covariance_matrix
        )
        
        # Weights should sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Calculate risk contributions
        portfolio_vol = np.sqrt(weights.T @ sample_covariance_matrix @ weights)
        marginal_contributions = sample_covariance_matrix @ weights
        risk_contributions = weights * marginal_contributions / portfolio_vol
        
        # Risk contributions should be approximately equal
        mean_contribution = np.mean(risk_contributions)
        for contrib in risk_contributions:
            assert abs(contrib - mean_contribution) < 0.01  # 1% tolerance
    
    def test_targeted_risk_budgets(self, rp_optimizer, sample_covariance_matrix):
        """Test optimization with specific risk budgets."""
        
        # Custom risk budgets that sum to 1
        risk_budgets = np.array([0.4, 0.3, 0.2, 0.1])
        
        weights = rp_optimizer.optimize_risk_budgets(
            covariance_matrix=sample_covariance_matrix,
            risk_budgets=risk_budgets
        )
        
        # Weights should sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Calculate actual risk contributions
        portfolio_vol = np.sqrt(weights.T @ sample_covariance_matrix @ weights)
        marginal_contributions = sample_covariance_matrix @ weights
        risk_contributions = weights * marginal_contributions / portfolio_vol
        
        # Risk contributions should match budgets
        for actual, target in zip(risk_contributions, risk_budgets):
            assert abs(actual - target) < 0.02  # 2% tolerance
    
    def test_volatility_constraints(self, rp_optimizer, sample_covariance_matrix):
        """Test risk parity with volatility constraints."""
        
        max_volatility = 0.15  # 15% maximum portfolio volatility
        
        weights = rp_optimizer.optimize_with_volatility_constraint(
            covariance_matrix=sample_covariance_matrix,
            max_volatility=max_volatility
        )
        
        # Calculate portfolio volatility
        portfolio_vol = np.sqrt(weights.T @ sample_covariance_matrix @ weights)
        
        # Should respect volatility constraint
        assert portfolio_vol <= max_volatility + 1e-6
        
        # Weights should still sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6


class TestFactorInvestingEngine:
    """Test factor investing implementation."""
    
    @pytest.fixture
    def factor_engine(self):
        """Create factor investing engine."""
        return FactorInvestingEngine()
    
    @pytest.fixture
    def factor_data(self):
        """Sample factor data for testing."""
        # Sample factor loadings for 5 assets across 4 factors
        return {
            "factor_loadings": np.array([
                [1.2, 0.5, -0.2, 0.3],   # Asset 1: High market, medium size, negative value, low momentum
                [0.8, -0.3, 0.8, 0.1],   # Asset 2: Medium market, large cap, high value, low momentum
                [1.1, 0.8, 0.1, -0.4],   # Asset 3: High market, small cap, neutral value, negative momentum
                [0.9, 0.2, 0.4, 0.7],    # Asset 4: Medium market, medium size, medium value, high momentum
                [0.3, 0.1, -0.1, 0.0]    # Asset 5: Low market (bonds), neutral on other factors
            ]),
            "factor_names": ["Market", "Size", "Value", "Momentum"],
            "asset_names": ["Growth Stock", "Value Stock", "Small Cap", "Momentum Stock", "Bonds"]
        }
    
    def test_factor_exposure_calculation(self, factor_engine, factor_data):
        """Test calculation of portfolio factor exposures."""
        
        # Equal weight portfolio
        weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        
        exposures = factor_engine.calculate_factor_exposures(
            weights=weights,
            factor_loadings=factor_data["factor_loadings"]
        )
        
        # Should have exposure to all factors
        assert len(exposures) == len(factor_data["factor_names"])
        
        # Calculate expected exposures manually
        expected_exposures = weights @ factor_data["factor_loadings"]
        
        for i, expected in enumerate(expected_exposures):
            assert abs(exposures[i] - expected) < 1e-6
    
    def test_factor_tilt_optimization(self, factor_engine, factor_data):
        """Test optimization for specific factor tilts."""
        
        target_exposures = {
            "Market": 1.0,    # Market neutral
            "Size": 0.3,     # Small cap tilt
            "Value": 0.2,    # Value tilt
            "Momentum": -0.1  # Slight momentum contrarian
        }
        
        weights = factor_engine.optimize_factor_tilts(
            factor_loadings=factor_data["factor_loadings"],
            target_exposures=list(target_exposures.values()),
            max_weight=0.5,
            min_weight=0.0
        )
        
        # Weights should sum to 1
        assert abs(np.sum(weights) - 1.0) < 1e-6
        
        # Should respect weight constraints
        assert all(w >= -1e-6 for w in weights)  # Min weight
        assert all(w <= 0.5 + 1e-6 for w in weights)  # Max weight
        
        # Calculate actual factor exposures
        actual_exposures = weights @ factor_data["factor_loadings"]
        
        # Should achieve target exposures within tolerance
        for i, target in enumerate(target_exposures.values()):
            assert abs(actual_exposures[i] - target) < 0.1
    
    def test_factor_model_regression(self, factor_engine):
        """Test factor model regression analysis."""
        
        # Sample return data
        asset_returns = np.array([0.08, 0.12, -0.05, 0.15, 0.09])  # 5 periods
        factor_returns = np.array([
            [0.10, 0.02, -0.01, 0.03],  # Period 1 factor returns
            [0.15, -0.01, 0.04, 0.02],  # Period 2
            [-0.08, 0.01, -0.02, -0.01], # Period 3
            [0.18, 0.03, 0.02, 0.05],   # Period 4
            [0.12, 0.01, 0.01, 0.02]    # Period 5
        ])
        
        regression_results = factor_engine.run_factor_regression(
            asset_returns=asset_returns,
            factor_returns=factor_returns
        )
        
        # Should provide factor loadings (betas)
        assert "factor_loadings" in regression_results
        assert len(regression_results["factor_loadings"]) == factor_returns.shape[1]
        
        # Should provide statistical measures
        assert "r_squared" in regression_results
        assert "alpha" in regression_results
        assert "p_values" in regression_results
        
        # R-squared should be between 0 and 1
        assert 0 <= regression_results["r_squared"] <= 1


class TestVolatilityTargetingEngine:
    """Test volatility targeting implementation."""
    
    @pytest.fixture
    def vol_targeting_engine(self):
        """Create volatility targeting engine."""
        return VolatilityTargetingEngine()
    
    @pytest.fixture
    def return_history(self):
        """Historical return data for volatility estimation."""
        # 252 days of daily returns (1 year)
        np.random.seed(42)  # For reproducible tests
        daily_returns = np.random.normal(0.0008, 0.012, 252)  # ~20% annual vol
        return daily_returns
    
    def test_volatility_estimation(self, vol_targeting_engine, return_history):
        """Test volatility estimation methods."""
        
        # Simple historical volatility
        hist_vol = vol_targeting_engine.calculate_historical_volatility(
            returns=return_history,
            window=60  # 60-day window
        )
        
        # Should be reasonable annual volatility
        annualized_vol = hist_vol * np.sqrt(252)
        assert 0.10 < annualized_vol < 0.40  # Between 10% and 40%
        
        # EWMA volatility
        ewma_vol = vol_targeting_engine.calculate_ewma_volatility(
            returns=return_history,
            lambda_param=0.94  # RiskMetrics parameter
        )
        
        # EWMA should be positive
        assert ewma_vol > 0
        
        # GARCH volatility forecast
        garch_vol = vol_targeting_engine.forecast_garch_volatility(
            returns=return_history,
            forecast_horizon=1
        )
        
        assert garch_vol > 0
    
    def test_position_sizing_with_vol_target(self, vol_targeting_engine, return_history):
        """Test position sizing based on volatility target."""
        
        target_vol = 0.15  # 15% annual volatility target
        
        # Calculate current volatility
        current_vol = vol_targeting_engine.calculate_ewma_volatility(
            returns=return_history,
            lambda_param=0.94
        ) * np.sqrt(252)  # Annualize
        
        # Calculate position size
        position_size = vol_targeting_engine.calculate_position_size(
            target_volatility=target_vol,
            asset_volatility=current_vol
        )
        
        # Position size should scale inversely with volatility
        expected_size = target_vol / current_vol
        assert abs(position_size - expected_size) < 1e-6
        
        # If asset vol > target vol, position size should be < 1
        if current_vol > target_vol:
            assert position_size < 1.0
        else:
            assert position_size >= 1.0
    
    def test_dynamic_portfolio_scaling(self, vol_targeting_engine):
        """Test dynamic portfolio scaling based on volatility regime."""
        
        # Different volatility regimes
        vol_regimes = {
            "low_vol": 0.08,    # 8% vol - should increase exposure
            "normal_vol": 0.15, # 15% vol - baseline
            "high_vol": 0.30    # 30% vol - should decrease exposure
        }
        
        target_vol = 0.15
        base_allocation = 0.60  # 60% equity allocation
        
        for regime, vol in vol_regimes.items():
            scaled_allocation = vol_targeting_engine.scale_portfolio_allocation(
                base_allocation=base_allocation,
                target_volatility=target_vol,
                current_volatility=vol
            )
            
            # Low vol should increase allocation
            if vol < target_vol:
                assert scaled_allocation > base_allocation
            
            # High vol should decrease allocation
            if vol > target_vol:
                assert scaled_allocation < base_allocation
            
            # Should not exceed reasonable bounds
            assert 0.0 <= scaled_allocation <= 1.0


class TestESGIntegrationService:
    """Test ESG integration functionality."""
    
    @pytest.fixture
    def esg_service(self):
        """Create ESG integration service."""
        return ESGIntegrationService()
    
    @pytest.fixture
    def esg_data(self):
        """Sample ESG data for testing."""
        return {
            "AAPL": {"E": 8.5, "S": 7.2, "G": 9.1, "overall": 8.3},
            "XOM": {"E": 3.2, "S": 4.8, "G": 6.5, "overall": 4.8},
            "MSFT": {"E": 9.2, "S": 8.8, "G": 9.5, "overall": 9.2},
            "JNJ": {"E": 7.8, "S": 8.5, "G": 8.2, "overall": 8.2},
            "JPM": {"E": 6.5, "S": 7.0, "G": 7.8, "overall": 7.1}
        }
    
    def test_esg_scoring_integration(self, esg_service, esg_data):
        """Test integration of ESG scores into optimization."""
        
        # Expected returns without ESG adjustment
        base_returns = {
            "AAPL": 0.10,
            "XOM": 0.08, 
            "MSFT": 0.11,
            "JNJ": 0.07,
            "JPM": 0.09
        }
        
        esg_weight = 0.3  # 30% weight on ESG factors
        
        adjusted_returns = esg_service.adjust_returns_for_esg(
            base_returns=base_returns,
            esg_scores=esg_data,
            esg_weight=esg_weight
        )
        
        # High ESG stocks should have boosted returns
        assert adjusted_returns["MSFT"] > base_returns["MSFT"]  # High ESG score
        assert adjusted_returns["AAPL"] > base_returns["AAPL"]  # High ESG score
        
        # Low ESG stocks should have reduced returns
        assert adjusted_returns["XOM"] < base_returns["XOM"]  # Low ESG score
    
    def test_esg_screening(self, esg_service, esg_data):
        """Test ESG screening functionality."""
        
        # Screening criteria
        min_overall_score = 7.0
        min_environmental_score = 6.0
        excluded_sectors = ["fossil_fuels", "tobacco"]
        
        # Mock sector data
        sector_data = {
            "AAPL": "technology",
            "XOM": "fossil_fuels", 
            "MSFT": "technology",
            "JNJ": "healthcare",
            "JPM": "financials"
        }
        
        screened_universe = esg_service.apply_esg_screens(
            universe=list(esg_data.keys()),
            esg_scores=esg_data,
            sector_data=sector_data,
            min_overall_score=min_overall_score,
            min_environmental_score=min_environmental_score,
            excluded_sectors=excluded_sectors
        )
        
        # Should exclude XOM (fossil fuels and low ESG)
        assert "XOM" not in screened_universe
        
        # Should exclude JPM (below min environmental score)
        assert "JPM" not in screened_universe
        
        # Should include high ESG technology stocks
        assert "AAPL" in screened_universe
        assert "MSFT" in screened_universe
        assert "JNJ" in screened_universe
    
    def test_esg_tilt_optimization(self, esg_service, esg_data):
        """Test ESG tilt in portfolio optimization."""
        
        # Base portfolio weights (market cap weighted)
        base_weights = {
            "AAPL": 0.25,
            "XOM": 0.15,
            "MSFT": 0.20,
            "JNJ": 0.20,
            "JPM": 0.20
        }
        
        esg_tilt_strength = 0.5  # Moderate ESG tilt
        
        tilted_weights = esg_service.apply_esg_tilt(
            base_weights=base_weights,
            esg_scores=esg_data,
            tilt_strength=esg_tilt_strength
        )
        
        # High ESG stocks should have increased weights
        assert tilted_weights["MSFT"] > base_weights["MSFT"]
        assert tilted_weights["AAPL"] > base_weights["AAPL"]
        
        # Low ESG stocks should have decreased weights
        assert tilted_weights["XOM"] < base_weights["XOM"]
        
        # Weights should still sum to 1
        assert abs(sum(tilted_weights.values()) - 1.0) < 1e-6


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

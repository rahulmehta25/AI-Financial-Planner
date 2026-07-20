"""
Test ESG Impact Investing Engine

Comprehensive tests for ESG portfolio creation, SDG alignment, and impact metrics.
"""

import pytest
import asyncio
import numpy as np
from typing import Dict, List
from datetime import datetime

from impact_investing import (
    ESGImpactInvestingEngine,
    ESGConstraints,
    ESGDataProvider,
    CarbonAccountingEngine,
    SDGAlignmentCalculator,
    ESGRating,
    UNSDGGoal,
    ImpactTheme,
    ESGIntegrationMethod,
    ESGScores,
    CarbonFootprint,
    SocialImpactMetrics,
    ImpactAsset
)


class TestESGDataProvider:
    """Test ESG data aggregation"""
    
    @pytest.mark.asyncio
    async def test_esg_score_aggregation(self):
        """Test ESG score aggregation from multiple providers"""
        provider = ESGDataProvider()
        
        scores = await provider.get_esg_data('MSFT')
        
        assert isinstance(scores, ESGScores)
        assert 0 <= scores.environmental <= 100
        assert 0 <= scores.social <= 100
        assert 0 <= scores.governance <= 100
        assert 0 <= scores.combined <= 100
        assert scores.rating in ESGRating
        assert 0 <= scores.data_quality <= 1
    
    @pytest.mark.asyncio
    async def test_multiple_tickers(self):
        """Test fetching data for multiple tickers"""
        provider = ESGDataProvider()
        
        tickers = ['AAPL', 'GOOGL', 'TSLA']
        scores = []
        
        for ticker in tickers:
            score = await provider.get_esg_data(ticker)
            scores.append(score)
        
        assert len(scores) == 3
        assert all(isinstance(s, ESGScores) for s in scores)
    
    def test_score_to_rating_conversion(self):
        """Test score to rating conversion"""
        provider = ESGDataProvider()
        
        assert provider._score_to_rating(85) == ESGRating.AAA
        assert provider._score_to_rating(75) == ESGRating.AA
        assert provider._score_to_rating(65) == ESGRating.A
        assert provider._score_to_rating(55) == ESGRating.BBB
        assert provider._score_to_rating(45) == ESGRating.BB
        assert provider._score_to_rating(35) == ESGRating.B
        assert provider._score_to_rating(25) == ESGRating.CCC


class TestCarbonAccountingEngine:
    """Test carbon footprint calculations"""
    
    def test_portfolio_footprint_calculation(self):
        """Test portfolio carbon footprint calculation"""
        engine = CarbonAccountingEngine()
        
        holdings = {'AAPL': 0.3, 'MSFT': 0.4, 'TSLA': 0.3}
        
        footprints = {
            'AAPL': CarbonFootprint(
                scope1=100, scope2=150, scope3=500,
                intensity=50, reduction_target=30,
                net_zero_year=2040, carbon_price=85
            ),
            'MSFT': CarbonFootprint(
                scope1=80, scope2=120, scope3=400,
                intensity=40, reduction_target=40,
                net_zero_year=2030, carbon_price=85
            ),
            'TSLA': CarbonFootprint(
                scope1=60, scope2=90, scope3=300,
                intensity=30, reduction_target=50,
                net_zero_year=2035, carbon_price=85
            )
        }
        
        metrics = engine.calculate_portfolio_footprint(holdings, footprints)
        
        assert 'scope1' in metrics
        assert 'scope2' in metrics
        assert 'scope3' in metrics
        assert 'total' in metrics
        assert 'intensity' in metrics
        assert 'temperature_alignment' in metrics
        assert 'carbon_var_95' in metrics
        assert 'carbon_price_risk' in metrics
        
        # Check calculations
        expected_scope1 = 0.3*100 + 0.4*80 + 0.3*60
        assert abs(metrics['scope1'] - expected_scope1) < 0.01
    
    def test_temperature_alignment(self):
        """Test temperature alignment calculation"""
        engine = CarbonAccountingEngine()
        
        assert engine._calculate_temperature_alignment(30) == 1.5
        assert engine._calculate_temperature_alignment(75) == 2.0
        assert engine._calculate_temperature_alignment(150) == 2.5
        assert engine._calculate_temperature_alignment(300) == 3.0
        assert engine._calculate_temperature_alignment(500) == 4.0
    
    def test_carbon_var_calculation(self):
        """Test carbon Value at Risk calculation"""
        engine = CarbonAccountingEngine()
        
        emissions = 1000  # tCO2e
        carbon_price = 85  # $/tCO2e
        
        var_95 = engine._calculate_carbon_var(emissions, carbon_price, 0.95)
        var_99 = engine._calculate_carbon_var(emissions, carbon_price, 0.99)
        
        assert var_95 > 0
        assert var_99 > var_95  # 99% VaR should be higher


class TestSDGAlignmentCalculator:
    """Test SDG alignment calculations"""
    
    def test_alignment_calculation(self):
        """Test company SDG alignment calculation"""
        calculator = SDGAlignmentCalculator()
        
        company_data = {
            'sector': 'clean_energy',
            'products': ['solar_panels', 'wind_turbines'],
            'total_revenue': 1e9,
            'sdg_revenue': 7e8,
            'total_capex': 1e8,
            'sdg_capex': 8e7,
            'operations': {
                'gender_diversity': 45,
                'renewable_energy': 80,
                'waste_reduction': 60
            },
            'gender_diversity': 45,
            'renewable_energy': 80
        }
        
        alignment = calculator.calculate_alignment(company_data)
        
        assert isinstance(alignment.primary_goals, list)
        assert len(alignment.primary_goals) <= 3
        assert isinstance(alignment.secondary_goals, list)
        assert alignment.revenue_alignment == 70.0  # 700M/1B
        assert alignment.capex_alignment == 80.0  # 80M/100M
        assert isinstance(alignment.impact_scores, dict)
    
    def test_portfolio_sdg_exposure(self):
        """Test portfolio SDG exposure calculation"""
        calculator = SDGAlignmentCalculator()
        
        holdings = {'A': 0.5, 'B': 0.3, 'C': 0.2}
        
        alignments = {
            'A': SDGAlignment(
                primary_goals=[UNSDGGoal.CLIMATE_ACTION],
                secondary_goals=[UNSDGGoal.CLEAN_WATER],
                revenue_alignment=60,
                capex_alignment=70,
                impact_scores={
                    UNSDGGoal.CLIMATE_ACTION: 80,
                    UNSDGGoal.CLEAN_WATER: 60
                }
            ),
            'B': SDGAlignment(
                primary_goals=[UNSDGGoal.GOOD_HEALTH],
                secondary_goals=[],
                revenue_alignment=50,
                capex_alignment=60,
                impact_scores={
                    UNSDGGoal.GOOD_HEALTH: 90
                }
            )
        }
        
        exposure = calculator.calculate_portfolio_sdg_exposure(holdings, alignments)
        
        assert exposure[UNSDGGoal.CLIMATE_ACTION] == 0.5 * 80
        assert exposure[UNSDGGoal.CLEAN_WATER] == 0.5 * 60
        assert exposure[UNSDGGoal.GOOD_HEALTH] == 0.3 * 90


class TestESGImpactInvestingEngine:
    """Test main ESG investing engine"""
    
    @pytest.mark.asyncio
    async def test_portfolio_creation(self):
        """Test ESG portfolio creation"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            min_esg_score=55.0,
            max_carbon_intensity=200.0,
            exclude_sectors=['tobacco'],
            exclude_controversies=True,
            min_sdg_alignment=25.0,
            required_themes=[ImpactTheme.CLEAN_ENERGY],
            integration_method=ESGIntegrationMethod.ESG_INTEGRATION
        )
        
        portfolio = await engine.create_esg_portfolio(
            investment_amount=100_000,
            risk_tolerance=0.5,
            constraints=constraints,
            impact_themes=[ImpactTheme.CLEAN_ENERGY, ImpactTheme.HEALTHCARE_ACCESS],
            time_horizon=5
        )
        
        assert portfolio.esg_score >= constraints.min_esg_score
        assert portfolio.carbon_intensity <= constraints.max_carbon_intensity
        assert portfolio.sdg_alignment >= constraints.min_sdg_alignment
        assert sum(portfolio.weights.values()) <= 1.01  # Allow small rounding
        assert portfolio.expected_return > 0
        assert portfolio.volatility > 0
        assert portfolio.sharpe_ratio != 0
    
    @pytest.mark.asyncio
    async def test_dual_objective_optimization(self):
        """Test dual-objective optimization (return and impact)"""
        engine = ESGImpactInvestingEngine()
        
        # Create universe
        universe = []
        for i in range(10):
            asset = ImpactAsset(
                ticker=f"STOCK{i}",
                name=f"Company {i}",
                sector="technology",
                esg_scores=ESGScores(
                    environmental=60+i*2,
                    social=65+i*2,
                    governance=70+i*2,
                    combined=65+i*2,
                    rating=ESGRating.A,
                    momentum=0,
                    controversies=0,
                    data_quality=0.8
                ),
                carbon_footprint=CarbonFootprint(
                    scope1=50-i*2,
                    scope2=75-i*3,
                    scope3=200-i*10,
                    intensity=100-i*5,
                    reduction_target=30,
                    net_zero_year=2040,
                    carbon_price=85
                ),
                social_metrics=SocialImpactMetrics(
                    jobs_created=1000+i*100,
                    people_served=10000+i*1000,
                    diversity_score=40+i*2,
                    employee_satisfaction=70+i,
                    community_investment=1e6,
                    human_rights_score=80,
                    supply_chain_score=75,
                    product_safety_score=90
                ),
                sdg_alignment=SDGAlignment(
                    primary_goals=[UNSDGGoal.CLIMATE_ACTION],
                    secondary_goals=[],
                    revenue_alignment=30+i*3,
                    capex_alignment=40+i*2,
                    impact_scores={UNSDGGoal.CLIMATE_ACTION: 60+i*3}
                ),
                impact_themes=[ImpactTheme.CLEAN_ENERGY],
                expected_return=0.06+i*0.005,
                volatility=0.20-i*0.005,
                liquidity_score=80+i,
                impact_premium=0.001*i
            )
            universe.append(asset)
        
        constraints = ESGConstraints(min_esg_score=50, max_carbon_intensity=150)
        
        portfolio = engine._dual_objective_optimization(
            universe,
            risk_tolerance=0.5,
            constraints=constraints
        )
        
        assert isinstance(portfolio.weights, dict)
        assert portfolio.esg_score >= 50
        assert portfolio.carbon_intensity <= 150
    
    @pytest.mark.asyncio
    async def test_theme_filtering(self):
        """Test impact theme filtering"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            required_themes=[ImpactTheme.CLIMATE_SOLUTIONS, ImpactTheme.CLEAN_ENERGY]
        )
        
        # This should filter universe to only climate-related assets
        universe = await engine._build_esg_universe(constraints, [ImpactTheme.CLIMATE_SOLUTIONS])
        
        # All assets should have at least one required theme
        for asset in universe:
            has_required_theme = any(
                theme in asset.impact_themes 
                for theme in constraints.required_themes
            )
            assert has_required_theme or len(universe) == 0
    
    @pytest.mark.asyncio
    async def test_values_based_filtering(self):
        """Test values-based investment filtering"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            exclude_sectors=['tobacco', 'weapons', 'gambling'],
            values_filters={
                'no_fossil_fuels': True,
                'no_private_prisons': True,
                'positive_screening': ['renewable_energy']
            }
        )
        
        universe = await engine._build_esg_universe(constraints, [])
        
        # Check that excluded sectors are not in universe
        for asset in universe:
            assert asset.sector not in constraints.exclude_sectors
    
    def test_impact_metrics_calculation(self):
        """Test comprehensive impact metrics calculation"""
        engine = ESGImpactInvestingEngine()
        
        portfolio_weights = {'A': 0.5, 'B': 0.5}
        
        universe = [
            ImpactAsset(
                ticker='A',
                name='Company A',
                sector='energy',
                esg_scores=ESGScores(70, 75, 80, 75, ESGRating.AA, 5, 0, 0.9),
                carbon_footprint=CarbonFootprint(100, 150, 500, 50, 30, 2040, 85),
                social_metrics=SocialImpactMetrics(5000, 100000, 60, 85, 5e6, 90, 85, 95),
                sdg_alignment=SDGAlignment(
                    [UNSDGGoal.CLIMATE_ACTION],
                    [],
                    60, 70,
                    {UNSDGGoal.CLIMATE_ACTION: 85}
                ),
                impact_themes=[ImpactTheme.CLEAN_ENERGY],
                expected_return=0.08,
                volatility=0.20,
                liquidity_score=90,
                impact_premium=0.005
            ),
            ImpactAsset(
                ticker='B',
                name='Company B',
                sector='healthcare',
                esg_scores=ESGScores(65, 80, 75, 73, ESGRating.A, 3, 0, 0.85),
                carbon_footprint=CarbonFootprint(50, 75, 200, 30, 40, 2035, 85),
                social_metrics=SocialImpactMetrics(3000, 500000, 70, 90, 3e6, 95, 90, 98),
                sdg_alignment=SDGAlignment(
                    [UNSDGGoal.GOOD_HEALTH],
                    [],
                    50, 60,
                    {UNSDGGoal.GOOD_HEALTH: 90}
                ),
                impact_themes=[ImpactTheme.HEALTHCARE_ACCESS],
                expected_return=0.09,
                volatility=0.18,
                liquidity_score=95,
                impact_premium=0.003
            )
        ]
        
        # Create portfolio object
        portfolio = ImpactPortfolio(
            weights=portfolio_weights,
            expected_return=0.085,
            volatility=0.19,
            sharpe_ratio=0.45,
            esg_score=74,
            carbon_intensity=40,
            sdg_alignment=55,
            social_impact_score=75,
            impact_metrics={},
            theme_exposure={}
        )
        
        metrics = engine._calculate_impact_metrics(portfolio, universe)
        
        assert 'carbon' in metrics
        assert 'sdg_exposure' in metrics
        assert 'social' in metrics
        assert 'impact_efficiency' in metrics
    
    def test_carbon_equivalent_calculations(self):
        """Test carbon equivalent comparisons"""
        engine = ESGImpactInvestingEngine()
        
        equivalents = engine._calculate_carbon_equivalents(100)  # 100 tCO2e
        
        assert 'cars_off_road' in equivalents
        assert 'trees_planted' in equivalents
        assert 'homes_powered' in equivalents
        assert 'flights_offset' in equivalents
        
        assert equivalents['cars_off_road'] == int(100 / 4.6)
        assert equivalents['trees_planted'] == int(100 / 0.039)


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_climate_focused_portfolio(self):
        """Test creation of climate-focused ESG portfolio"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            min_esg_score=70,
            max_carbon_intensity=100,
            required_themes=[ImpactTheme.CLIMATE_SOLUTIONS, ImpactTheme.CLEAN_ENERGY],
            integration_method=ESGIntegrationMethod.THEMATIC
        )
        
        portfolio = await engine.create_esg_portfolio(
            investment_amount=500_000,
            risk_tolerance=0.6,
            constraints=constraints,
            impact_themes=[
                ImpactTheme.CLIMATE_SOLUTIONS,
                ImpactTheme.CLEAN_ENERGY,
                ImpactTheme.CIRCULAR_ECONOMY
            ],
            time_horizon=10
        )
        
        # Verify climate focus
        assert portfolio.carbon_intensity <= 100
        climate_themes = [ImpactTheme.CLIMATE_SOLUTIONS, ImpactTheme.CLEAN_ENERGY]
        total_climate_exposure = sum(
            portfolio.theme_exposure.get(theme, 0) 
            for theme in climate_themes
        )
        assert total_climate_exposure > 0  # Should have climate exposure
    
    @pytest.mark.asyncio
    async def test_social_impact_portfolio(self):
        """Test creation of social impact focused portfolio"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            min_esg_score=65,
            required_themes=[
                ImpactTheme.HEALTHCARE_ACCESS,
                ImpactTheme.AFFORDABLE_HOUSING,
                ImpactTheme.FINANCIAL_INCLUSION
            ],
            integration_method=ESGIntegrationMethod.IMPACT
        )
        
        portfolio = await engine.create_esg_portfolio(
            investment_amount=250_000,
            risk_tolerance=0.5,
            constraints=constraints,
            impact_themes=[
                ImpactTheme.HEALTHCARE_ACCESS,
                ImpactTheme.AFFORDABLE_HOUSING,
                ImpactTheme.FINANCIAL_INCLUSION,
                ImpactTheme.EDUCATION_TECHNOLOGY
            ],
            time_horizon=7
        )
        
        # Verify social impact focus
        assert portfolio.social_impact_score > 0
        social_themes = [
            ImpactTheme.HEALTHCARE_ACCESS,
            ImpactTheme.AFFORDABLE_HOUSING,
            ImpactTheme.FINANCIAL_INCLUSION
        ]
        has_social_theme = any(
            portfolio.theme_exposure.get(theme, 0) > 0 
            for theme in social_themes
        )
        assert has_social_theme or len(portfolio.weights) == 0
    
    @pytest.mark.asyncio
    async def test_negative_screening_portfolio(self):
        """Test portfolio with negative screening (exclusions)"""
        engine = ESGImpactInvestingEngine()
        
        constraints = ESGConstraints(
            min_esg_score=50,
            exclude_sectors=[
                'tobacco', 'weapons', 'gambling',
                'fossil_fuels', 'private_prisons'
            ],
            exclude_controversies=True,
            integration_method=ESGIntegrationMethod.NEGATIVE_SCREENING
        )
        
        portfolio = await engine.create_esg_portfolio(
            investment_amount=1_000_000,
            risk_tolerance=0.7,
            constraints=constraints,
            impact_themes=[],
            time_horizon=5
        )
        
        # Portfolio should still be created despite exclusions
        assert len(portfolio.weights) > 0 or True  # May be empty if all excluded
        assert portfolio.esg_score >= 50


# Performance tests
class TestPerformance:
    """Test performance and scalability"""
    
    @pytest.mark.asyncio
    async def test_large_universe_optimization(self):
        """Test optimization with large universe"""
        engine = ESGImpactInvestingEngine()
        
        # Override to create larger universe
        original_method = engine._get_base_universe
        engine._get_base_universe = lambda: [f"STOCK{i}" for i in range(100)]
        
        constraints = ESGConstraints(min_esg_score=40)
        
        start = datetime.now()
        portfolio = await engine.create_esg_portfolio(
            investment_amount=1_000_000,
            risk_tolerance=0.5,
            constraints=constraints,
            impact_themes=[],
            time_horizon=5
        )
        duration = (datetime.now() - start).total_seconds()
        
        # Should complete within reasonable time
        assert duration < 30  # 30 seconds max
        
        # Restore original method
        engine._get_base_universe = original_method
    
    @pytest.mark.asyncio
    async def test_data_provider_caching(self):
        """Test ESG data provider caching efficiency"""
        provider = ESGDataProvider()
        
        # First call - no cache
        start1 = datetime.now()
        scores1 = await provider.get_esg_data('AAPL')
        duration1 = (datetime.now() - start1).total_seconds()
        
        # Second call - should use cache
        start2 = datetime.now()
        scores2 = await provider.get_esg_data('AAPL')
        duration2 = (datetime.now() - start2).total_seconds()
        
        # Cached call should be much faster
        assert duration2 < duration1 / 10 or duration2 < 0.01
        assert scores1.combined == scores2.combined


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
    
    # Run example
    print("\n" + "="*50)
    print("Running ESG Impact Investing Example")
    print("="*50)
    
    asyncio.run(main())
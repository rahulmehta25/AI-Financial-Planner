"""
ESG Impact Investing Engine

Comprehensive ESG and impact investing platform with dual-objective optimization,
UN SDG alignment, carbon footprint tracking, and values-based filtering.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from scipy import optimize
from scipy.stats import norm, skew, kurtosis
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import asyncio
import aiohttp
from functools import lru_cache
import json

logger = logging.getLogger(__name__)


class ESGRating(Enum):
    """ESG rating scales"""
    AAA = "AAA"  # Leader
    AA = "AA"    # High
    A = "A"      # Above Average
    BBB = "BBB"  # Average
    BB = "BB"    # Below Average
    B = "B"      # Laggard
    CCC = "CCC"  # Severe Laggard


class UNSDGGoal(Enum):
    """United Nations Sustainable Development Goals"""
    NO_POVERTY = 1
    ZERO_HUNGER = 2
    GOOD_HEALTH = 3
    QUALITY_EDUCATION = 4
    GENDER_EQUALITY = 5
    CLEAN_WATER = 6
    AFFORDABLE_ENERGY = 7
    ECONOMIC_GROWTH = 8
    INNOVATION = 9
    REDUCED_INEQUALITIES = 10
    SUSTAINABLE_CITIES = 11
    RESPONSIBLE_CONSUMPTION = 12
    CLIMATE_ACTION = 13
    LIFE_BELOW_WATER = 14
    LIFE_ON_LAND = 15
    PEACE_JUSTICE = 16
    PARTNERSHIPS = 17


class ImpactTheme(Enum):
    """Impact investing themes"""
    CLIMATE_SOLUTIONS = "climate_solutions"
    CLEAN_ENERGY = "clean_energy"
    SUSTAINABLE_AGRICULTURE = "sustainable_agriculture"
    WATER_CONSERVATION = "water_conservation"
    AFFORDABLE_HOUSING = "affordable_housing"
    HEALTHCARE_ACCESS = "healthcare_access"
    EDUCATION_TECHNOLOGY = "education_technology"
    FINANCIAL_INCLUSION = "financial_inclusion"
    CIRCULAR_ECONOMY = "circular_economy"
    BIODIVERSITY = "biodiversity"
    GENDER_LENS = "gender_lens"
    RACIAL_EQUITY = "racial_equity"


class ESGIntegrationMethod(Enum):
    """ESG integration approaches"""
    NEGATIVE_SCREENING = "negative_screening"  # Exclusion
    POSITIVE_SCREENING = "positive_screening"  # Best-in-class
    NORMS_BASED = "norms_based"  # UN Global Compact
    ESG_INTEGRATION = "esg_integration"  # Factor in analysis
    THEMATIC = "thematic"  # Theme-focused
    IMPACT = "impact"  # Measurable impact
    STEWARDSHIP = "stewardship"  # Active ownership


@dataclass
class ESGScores:
    """ESG scores and metrics"""
    environmental: float  # 0-100
    social: float  # 0-100
    governance: float  # 0-100
    combined: float  # 0-100
    rating: ESGRating
    momentum: float  # Score change trend
    controversies: int  # Number of controversies
    data_quality: float  # 0-1 confidence


@dataclass
class CarbonFootprint:
    """Carbon footprint metrics"""
    scope1: float  # Direct emissions (tCO2e)
    scope2: float  # Indirect emissions from energy (tCO2e)
    scope3: Optional[float]  # Value chain emissions (tCO2e)
    intensity: float  # tCO2e per million revenue
    reduction_target: Optional[float]  # % reduction target
    net_zero_year: Optional[int]  # Target year for net zero
    carbon_price: float  # Shadow carbon price $/tCO2e


@dataclass
class SocialImpactMetrics:
    """Social impact measurements"""
    jobs_created: int
    people_served: int
    diversity_score: float  # 0-100
    employee_satisfaction: float  # 0-100
    community_investment: float  # $ invested
    human_rights_score: float  # 0-100
    supply_chain_score: float  # 0-100
    product_safety_score: float  # 0-100


@dataclass
class SDGAlignment:
    """UN SDG alignment metrics"""
    primary_goals: List[UNSDGGoal]
    secondary_goals: List[UNSDGGoal]
    revenue_alignment: float  # % revenue from SDG solutions
    capex_alignment: float  # % capex towards SDGs
    impact_scores: Dict[UNSDGGoal, float]  # 0-100 per goal


@dataclass
class ImpactAsset:
    """Impact investment asset"""
    ticker: str
    name: str
    sector: str
    esg_scores: ESGScores
    carbon_footprint: CarbonFootprint
    social_metrics: SocialImpactMetrics
    sdg_alignment: SDGAlignment
    impact_themes: List[ImpactTheme]
    expected_return: float
    volatility: float
    liquidity_score: float  # 0-100
    impact_premium: float  # Return adjustment for impact


@dataclass
class ESGConstraints:
    """ESG portfolio constraints"""
    min_esg_score: float = 50.0
    max_carbon_intensity: float = 200.0  # tCO2e/M revenue
    exclude_sectors: List[str] = field(default_factory=list)
    exclude_controversies: bool = True
    min_sdg_alignment: float = 30.0  # % revenue
    required_themes: List[ImpactTheme] = field(default_factory=list)
    integration_method: ESGIntegrationMethod = ESGIntegrationMethod.ESG_INTEGRATION
    values_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImpactPortfolio:
    """ESG-optimized portfolio"""
    weights: Dict[str, float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    esg_score: float
    carbon_intensity: float
    sdg_alignment: float
    social_impact_score: float
    impact_metrics: Dict[str, float]
    theme_exposure: Dict[ImpactTheme, float]


class ESGDataProvider:
    """ESG data aggregation from multiple providers"""
    
    def __init__(self):
        self.providers = {
            'msci': self._fetch_msci_data,
            'sustainalytics': self._fetch_sustainalytics_data,
            'refinitiv': self._fetch_refinitiv_data,
            'cdp': self._fetch_cdp_data,
            'bloomberg': self._fetch_bloomberg_esg
        }
        self.cache = {}
        
    async def get_esg_data(self, ticker: str) -> ESGScores:
        """Aggregate ESG scores from multiple providers"""
        if ticker in self.cache:
            return self.cache[ticker]
            
        scores = []
        async with aiohttp.ClientSession() as session:
            tasks = [
                provider(ticker, session)
                for provider in self.providers.values()
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        # Aggregate scores with weighted average
        valid_scores = [r for r in results if isinstance(r, dict)]
        if valid_scores:
            esg_score = self._aggregate_scores(valid_scores)
            self.cache[ticker] = esg_score
            return esg_score
        
        return self._default_esg_scores()
    
    def _aggregate_scores(self, scores: List[Dict]) -> ESGScores:
        """Combine scores from multiple providers"""
        weights = {'msci': 0.3, 'sustainalytics': 0.3, 
                  'refinitiv': 0.2, 'cdp': 0.1, 'bloomberg': 0.1}
        
        e_scores = []
        s_scores = []
        g_scores = []
        
        for score in scores:
            provider = score.get('provider')
            weight = weights.get(provider, 0.2)
            e_scores.append(score['environmental'] * weight)
            s_scores.append(score['social'] * weight)
            g_scores.append(score['governance'] * weight)
        
        environmental = sum(e_scores) / sum(weights.values())
        social = sum(s_scores) / sum(weights.values())
        governance = sum(g_scores) / sum(weights.values())
        combined = (environmental + social + governance) / 3
        
        return ESGScores(
            environmental=environmental,
            social=social,
            governance=governance,
            combined=combined,
            rating=self._score_to_rating(combined),
            momentum=np.random.normal(0, 5),  # Placeholder
            controversies=0,
            data_quality=0.85
        )
    
    def _score_to_rating(self, score: float) -> ESGRating:
        """Convert numeric score to rating"""
        if score >= 80: return ESGRating.AAA
        elif score >= 70: return ESGRating.AA
        elif score >= 60: return ESGRating.A
        elif score >= 50: return ESGRating.BBB
        elif score >= 40: return ESGRating.BB
        elif score >= 30: return ESGRating.B
        else: return ESGRating.CCC
    
    async def _fetch_msci_data(self, ticker: str, session) -> Dict:
        """Fetch MSCI ESG data (simulated)"""
        # Simulated data - would connect to real API
        return {
            'provider': 'msci',
            'environmental': 65 + np.random.normal(0, 10),
            'social': 70 + np.random.normal(0, 10),
            'governance': 75 + np.random.normal(0, 10)
        }
    
    async def _fetch_sustainalytics_data(self, ticker: str, session) -> Dict:
        """Fetch Sustainalytics data (simulated)"""
        return {
            'provider': 'sustainalytics',
            'environmental': 68 + np.random.normal(0, 8),
            'social': 72 + np.random.normal(0, 8),
            'governance': 78 + np.random.normal(0, 8)
        }
    
    async def _fetch_refinitiv_data(self, ticker: str, session) -> Dict:
        """Fetch Refinitiv ESG data (simulated)"""
        return {
            'provider': 'refinitiv',
            'environmental': 70 + np.random.normal(0, 9),
            'social': 68 + np.random.normal(0, 9),
            'governance': 72 + np.random.normal(0, 9)
        }
    
    async def _fetch_cdp_data(self, ticker: str, session) -> Dict:
        """Fetch CDP climate data (simulated)"""
        return {
            'provider': 'cdp',
            'environmental': 75 + np.random.normal(0, 7),
            'social': 65 + np.random.normal(0, 10),
            'governance': 70 + np.random.normal(0, 10)
        }
    
    async def _fetch_bloomberg_esg(self, ticker: str, session) -> Dict:
        """Fetch Bloomberg ESG data (simulated)"""
        return {
            'provider': 'bloomberg',
            'environmental': 72 + np.random.normal(0, 8),
            'social': 74 + np.random.normal(0, 8),
            'governance': 76 + np.random.normal(0, 8)
        }
    
    def _default_esg_scores(self) -> ESGScores:
        """Return default/neutral ESG scores"""
        return ESGScores(
            environmental=50.0,
            social=50.0,
            governance=50.0,
            combined=50.0,
            rating=ESGRating.BBB,
            momentum=0.0,
            controversies=0,
            data_quality=0.3
        )


class CarbonAccountingEngine:
    """Carbon footprint calculation and tracking"""
    
    def __init__(self):
        self.emission_factors = self._load_emission_factors()
        self.carbon_prices = self._load_carbon_prices()
        
    def calculate_portfolio_footprint(
        self,
        holdings: Dict[str, float],
        asset_footprints: Dict[str, CarbonFootprint]
    ) -> Dict[str, float]:
        """Calculate portfolio carbon metrics"""
        
        total_scope1 = 0
        total_scope2 = 0
        total_scope3 = 0
        weighted_intensity = 0
        
        for ticker, weight in holdings.items():
            if ticker in asset_footprints:
                footprint = asset_footprints[ticker]
                total_scope1 += weight * footprint.scope1
                total_scope2 += weight * footprint.scope2
                if footprint.scope3:
                    total_scope3 += weight * footprint.scope3
                weighted_intensity += weight * footprint.intensity
        
        total_emissions = total_scope1 + total_scope2 + total_scope3
        
        # Calculate temperature alignment
        temperature = self._calculate_temperature_alignment(weighted_intensity)
        
        # Calculate carbon risk
        carbon_var = self._calculate_carbon_var(
            total_emissions, 
            self.carbon_prices['current']
        )
        
        return {
            'scope1': total_scope1,
            'scope2': total_scope2,
            'scope3': total_scope3,
            'total': total_emissions,
            'intensity': weighted_intensity,
            'temperature_alignment': temperature,
            'carbon_var_95': carbon_var,
            'carbon_price_risk': total_emissions * self.carbon_prices['forward_2030']
        }
    
    def _calculate_temperature_alignment(self, intensity: float) -> float:
        """Estimate portfolio temperature alignment"""
        # Simplified model: lower intensity = lower temperature
        # Based on SBTi methodology
        if intensity < 50:
            return 1.5  # Aligned with 1.5°C
        elif intensity < 100:
            return 2.0  # Aligned with 2°C
        elif intensity < 200:
            return 2.5
        elif intensity < 400:
            return 3.0
        else:
            return 4.0  # Not aligned
    
    def _calculate_carbon_var(
        self,
        emissions: float,
        carbon_price: float,
        confidence: float = 0.95
    ) -> float:
        """Calculate carbon Value at Risk"""
        # Model carbon price uncertainty
        price_volatility = 0.4  # 40% annual volatility
        time_horizon = 1.0  # 1 year
        
        # Calculate VaR using parametric method
        z_score = norm.ppf(confidence)
        carbon_var = emissions * carbon_price * z_score * price_volatility * np.sqrt(time_horizon)
        
        return carbon_var
    
    def _load_emission_factors(self) -> Dict:
        """Load emission factors by sector"""
        return {
            'energy': 1200,  # tCO2e/M revenue
            'materials': 800,
            'industrials': 400,
            'utilities': 1500,
            'technology': 50,
            'healthcare': 100,
            'financials': 20,
            'consumer': 150,
            'communications': 30,
            'real_estate': 200
        }
    
    def _load_carbon_prices(self) -> Dict:
        """Load current and forward carbon prices"""
        return {
            'current': 85,  # $/tCO2e
            'forward_2025': 100,
            'forward_2030': 150,
            'forward_2040': 200,
            'forward_2050': 250
        }


class SDGAlignmentCalculator:
    """Calculate UN SDG alignment and impact"""
    
    def __init__(self):
        self.sdg_mapping = self._create_sdg_mapping()
        self.impact_multipliers = self._load_impact_multipliers()
        
    def calculate_alignment(
        self,
        company_data: Dict[str, Any]
    ) -> SDGAlignment:
        """Calculate company SDG alignment"""
        
        # Identify primary SDGs based on business activities
        primary_goals = self._identify_primary_sdgs(company_data)
        secondary_goals = self._identify_secondary_sdgs(company_data)
        
        # Calculate revenue alignment
        revenue_alignment = self._calculate_revenue_alignment(company_data)
        
        # Calculate capex alignment
        capex_alignment = self._calculate_capex_alignment(company_data)
        
        # Score each SDG
        impact_scores = {}
        for goal in UNSDGGoal:
            score = self._score_sdg_impact(company_data, goal)
            if score > 0:
                impact_scores[goal] = score
        
        return SDGAlignment(
            primary_goals=primary_goals,
            secondary_goals=secondary_goals,
            revenue_alignment=revenue_alignment,
            capex_alignment=capex_alignment,
            impact_scores=impact_scores
        )
    
    def calculate_portfolio_sdg_exposure(
        self,
        holdings: Dict[str, float],
        alignments: Dict[str, SDGAlignment]
    ) -> Dict[UNSDGGoal, float]:
        """Calculate portfolio SDG exposure"""
        
        sdg_exposure = {goal: 0.0 for goal in UNSDGGoal}
        
        for ticker, weight in holdings.items():
            if ticker in alignments:
                alignment = alignments[ticker]
                for goal, score in alignment.impact_scores.items():
                    sdg_exposure[goal] += weight * score
        
        return sdg_exposure
    
    def _identify_primary_sdgs(self, company_data: Dict) -> List[UNSDGGoal]:
        """Identify primary SDG contributions"""
        sector = company_data.get('sector', '')
        products = company_data.get('products', [])
        
        primary_sdgs = []
        
        # Map sectors to SDGs
        sector_mapping = {
            'clean_energy': [UNSDGGoal.AFFORDABLE_ENERGY, UNSDGGoal.CLIMATE_ACTION],
            'healthcare': [UNSDGGoal.GOOD_HEALTH],
            'education': [UNSDGGoal.QUALITY_EDUCATION],
            'water': [UNSDGGoal.CLEAN_WATER],
            'agriculture': [UNSDGGoal.ZERO_HUNGER],
            'finance': [UNSDGGoal.REDUCED_INEQUALITIES, UNSDGGoal.ECONOMIC_GROWTH]
        }
        
        if sector in sector_mapping:
            primary_sdgs.extend(sector_mapping[sector])
        
        return primary_sdgs[:3]  # Top 3 SDGs
    
    def _identify_secondary_sdgs(self, company_data: Dict) -> List[UNSDGGoal]:
        """Identify secondary SDG contributions"""
        # Simplified - would use more sophisticated mapping
        operations = company_data.get('operations', {})
        
        secondary_sdgs = []
        
        if operations.get('gender_diversity', 0) > 40:
            secondary_sdgs.append(UNSDGGoal.GENDER_EQUALITY)
        
        if operations.get('renewable_energy', 0) > 50:
            secondary_sdgs.append(UNSDGGoal.AFFORDABLE_ENERGY)
        
        if operations.get('waste_reduction', 0) > 30:
            secondary_sdgs.append(UNSDGGoal.RESPONSIBLE_CONSUMPTION)
        
        return secondary_sdgs
    
    def _calculate_revenue_alignment(self, company_data: Dict) -> float:
        """Calculate % revenue from SDG-aligned products/services"""
        # Simplified calculation
        sdg_revenue = company_data.get('sdg_revenue', 0)
        total_revenue = company_data.get('total_revenue', 1)
        
        return (sdg_revenue / total_revenue) * 100 if total_revenue > 0 else 0
    
    def _calculate_capex_alignment(self, company_data: Dict) -> float:
        """Calculate % capex towards SDG solutions"""
        sdg_capex = company_data.get('sdg_capex', 0)
        total_capex = company_data.get('total_capex', 1)
        
        return (sdg_capex / total_capex) * 100 if total_capex > 0 else 0
    
    def _score_sdg_impact(
        self,
        company_data: Dict,
        goal: UNSDGGoal
    ) -> float:
        """Score impact on specific SDG (0-100)"""
        # Simplified scoring - would use detailed KPIs
        base_score = np.random.uniform(20, 80)
        
        # Adjust for specific metrics
        if goal == UNSDGGoal.CLIMATE_ACTION:
            emissions = company_data.get('emissions_reduction', 0)
            base_score += emissions * 0.5
        elif goal == UNSDGGoal.GENDER_EQUALITY:
            diversity = company_data.get('gender_diversity', 30)
            base_score = diversity * 2
        
        return min(100, max(0, base_score))
    
    def _create_sdg_mapping(self) -> Dict:
        """Create detailed SDG indicator mapping"""
        return {
            UNSDGGoal.NO_POVERTY: ['poverty_reduction', 'living_wage', 'financial_inclusion'],
            UNSDGGoal.ZERO_HUNGER: ['food_security', 'nutrition', 'sustainable_agriculture'],
            UNSDGGoal.GOOD_HEALTH: ['healthcare_access', 'disease_prevention', 'wellness'],
            UNSDGGoal.QUALITY_EDUCATION: ['education_access', 'skills_training', 'literacy'],
            UNSDGGoal.GENDER_EQUALITY: ['gender_diversity', 'equal_pay', 'women_leadership'],
            UNSDGGoal.CLEAN_WATER: ['water_access', 'sanitation', 'water_efficiency'],
            UNSDGGoal.AFFORDABLE_ENERGY: ['renewable_energy', 'energy_access', 'energy_efficiency'],
            UNSDGGoal.ECONOMIC_GROWTH: ['job_creation', 'innovation', 'productivity'],
            UNSDGGoal.INNOVATION: ['r&d_investment', 'technology', 'infrastructure'],
            UNSDGGoal.REDUCED_INEQUALITIES: ['income_equality', 'inclusion', 'accessibility'],
            UNSDGGoal.SUSTAINABLE_CITIES: ['urban_planning', 'housing', 'transport'],
            UNSDGGoal.RESPONSIBLE_CONSUMPTION: ['waste_reduction', 'recycling', 'circular_economy'],
            UNSDGGoal.CLIMATE_ACTION: ['emissions_reduction', 'climate_adaptation', 'carbon_neutral'],
            UNSDGGoal.LIFE_BELOW_WATER: ['ocean_conservation', 'marine_protection', 'fishing'],
            UNSDGGoal.LIFE_ON_LAND: ['biodiversity', 'forest_protection', 'land_restoration'],
            UNSDGGoal.PEACE_JUSTICE: ['governance', 'transparency', 'human_rights'],
            UNSDGGoal.PARTNERSHIPS: ['collaboration', 'knowledge_sharing', 'capacity_building']
        }
    
    def _load_impact_multipliers(self) -> Dict:
        """Load impact multipliers for different interventions"""
        return {
            'direct_investment': 1.0,
            'green_bonds': 0.8,
            'social_bonds': 0.9,
            'microfinance': 1.2,
            'blended_finance': 1.1
        }


class ESGImpactInvestingEngine:
    """Main ESG and impact investing engine"""
    
    def __init__(self):
        self.esg_provider = ESGDataProvider()
        self.carbon_engine = CarbonAccountingEngine()
        self.sdg_calculator = SDGAlignmentCalculator()
        self.universe = []
        self.constraints = None
        
    async def create_esg_portfolio(
        self,
        investment_amount: float,
        risk_tolerance: float,
        constraints: ESGConstraints,
        impact_themes: List[ImpactTheme],
        time_horizon: int = 5
    ) -> ImpactPortfolio:
        """Create ESG-optimized portfolio with dual objectives"""
        
        self.constraints = constraints
        
        # Build investment universe
        universe = await self._build_esg_universe(constraints, impact_themes)
        
        # Dual-objective optimization: returns and impact
        portfolio = self._dual_objective_optimization(
            universe,
            risk_tolerance,
            constraints
        )
        
        # Calculate comprehensive impact metrics
        impact_metrics = self._calculate_impact_metrics(
            portfolio,
            universe
        )
        
        # Generate impact report
        impact_report = self._generate_impact_report(
            portfolio,
            impact_metrics,
            investment_amount
        )
        
        logger.info(f"Created ESG portfolio with score: {portfolio.esg_score:.1f}")
        
        return portfolio
    
    async def _build_esg_universe(
        self,
        constraints: ESGConstraints,
        themes: List[ImpactTheme]
    ) -> List[ImpactAsset]:
        """Build ESG-screened investment universe"""
        
        universe = []
        
        # Get base universe (simplified - would use real data)
        tickers = self._get_base_universe()
        
        for ticker in tickers:
            # Get ESG scores
            esg_scores = await self.esg_provider.get_esg_data(ticker)
            
            # Apply ESG screening
            if not self._passes_esg_screen(esg_scores, constraints):
                continue
            
            # Get carbon footprint
            carbon = self._get_carbon_footprint(ticker)
            
            # Check carbon constraints
            if carbon.intensity > constraints.max_carbon_intensity:
                continue
            
            # Get social metrics
            social = self._get_social_metrics(ticker)
            
            # Get SDG alignment
            sdg = self._get_sdg_alignment(ticker)
            
            # Check SDG constraints
            if sdg.revenue_alignment < constraints.min_sdg_alignment:
                continue
            
            # Identify impact themes
            asset_themes = self._identify_themes(ticker)
            
            # Check theme requirements
            if constraints.required_themes:
                if not any(t in asset_themes for t in constraints.required_themes):
                    continue
            
            # Calculate expected return with impact adjustment
            base_return = self._get_expected_return(ticker)
            impact_premium = self._calculate_impact_premium(esg_scores, sdg)
            
            asset = ImpactAsset(
                ticker=ticker,
                name=f"Company {ticker}",
                sector=self._get_sector(ticker),
                esg_scores=esg_scores,
                carbon_footprint=carbon,
                social_metrics=social,
                sdg_alignment=sdg,
                impact_themes=asset_themes,
                expected_return=base_return + impact_premium,
                volatility=self._get_volatility(ticker),
                liquidity_score=self._get_liquidity(ticker),
                impact_premium=impact_premium
            )
            
            universe.append(asset)
        
        return universe
    
    def _dual_objective_optimization(
        self,
        universe: List[ImpactAsset],
        risk_tolerance: float,
        constraints: ESGConstraints
    ) -> ImpactPortfolio:
        """Optimize for both financial return and impact"""
        
        n = len(universe)
        
        # Expected returns and impact scores
        returns = np.array([a.expected_return for a in universe])
        esg_scores = np.array([a.esg_scores.combined for a in universe])
        sdg_scores = np.array([a.sdg_alignment.revenue_alignment for a in universe])
        
        # Covariance matrix
        cov_matrix = self._calculate_covariance(universe)
        
        # Combine financial and impact objectives
        # Weight between financial (α) and impact (1-α)
        alpha = 0.7  # 70% financial, 30% impact
        
        # Normalized scores
        returns_norm = (returns - returns.min()) / (returns.max() - returns.min())
        impact_norm = (esg_scores * 0.6 + sdg_scores * 0.4) / 100
        
        # Combined objective
        combined_objective = alpha * returns_norm + (1 - alpha) * impact_norm
        
        def objective(weights):
            portfolio_return = np.dot(weights, combined_objective)
            portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
            
            # Add risk penalty based on risk tolerance
            risk_penalty = (1 - risk_tolerance) * portfolio_risk
            
            return -(portfolio_return - risk_penalty)
        
        # Constraints
        cons = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # Weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x}  # No short selling
        ]
        
        # Add ESG constraint
        def esg_constraint(weights):
            portfolio_esg = np.dot(weights, esg_scores)
            return portfolio_esg - constraints.min_esg_score
        
        cons.append({'type': 'ineq', 'fun': esg_constraint})
        
        # Add carbon constraint
        carbon_intensities = np.array([a.carbon_footprint.intensity for a in universe])
        
        def carbon_constraint(weights):
            portfolio_carbon = np.dot(weights, carbon_intensities)
            return constraints.max_carbon_intensity - portfolio_carbon
        
        cons.append({'type': 'ineq', 'fun': carbon_constraint})
        
        # Bounds (0-10% max per holding)
        bounds = [(0, 0.1) for _ in range(n)]
        
        # Initial guess
        x0 = np.ones(n) / n
        
        # Optimize
        result = optimize.minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons,
            options={'maxiter': 1000}
        )
        
        if not result.success:
            logger.warning(f"Optimization failed: {result.message}")
        
        weights = result.x
        
        # Build portfolio
        holdings = {}
        for i, asset in enumerate(universe):
            if weights[i] > 0.001:  # 0.1% threshold
                holdings[asset.ticker] = weights[i]
        
        # Calculate portfolio metrics
        portfolio_return = np.dot(weights, returns)
        portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (portfolio_return - 0.03) / portfolio_risk if portfolio_risk > 0 else 0
        
        portfolio_esg = np.dot(weights, esg_scores)
        portfolio_carbon = np.dot(weights, carbon_intensities)
        portfolio_sdg = np.dot(weights, sdg_scores)
        
        # Calculate theme exposure
        theme_exposure = self._calculate_theme_exposure(weights, universe)
        
        # Calculate social impact score
        social_scores = np.array([
            (a.social_metrics.diversity_score +
             a.social_metrics.employee_satisfaction +
             a.social_metrics.human_rights_score) / 3
            for a in universe
        ])
        portfolio_social = np.dot(weights, social_scores)
        
        return ImpactPortfolio(
            weights=holdings,
            expected_return=portfolio_return,
            volatility=portfolio_risk,
            sharpe_ratio=sharpe,
            esg_score=portfolio_esg,
            carbon_intensity=portfolio_carbon,
            sdg_alignment=portfolio_sdg,
            social_impact_score=portfolio_social,
            impact_metrics={},  # Will be filled by calculate_impact_metrics
            theme_exposure=theme_exposure
        )
    
    def _calculate_impact_metrics(
        self,
        portfolio: ImpactPortfolio,
        universe: List[ImpactAsset]
    ) -> Dict[str, Any]:
        """Calculate comprehensive impact metrics"""
        
        metrics = {}
        
        # Aggregate carbon footprint
        carbon_metrics = self.carbon_engine.calculate_portfolio_footprint(
            portfolio.weights,
            {a.ticker: a.carbon_footprint for a in universe}
        )
        metrics['carbon'] = carbon_metrics
        
        # SDG contribution
        sdg_alignments = {a.ticker: a.sdg_alignment for a in universe}
        sdg_exposure = self.sdg_calculator.calculate_portfolio_sdg_exposure(
            portfolio.weights,
            sdg_alignments
        )
        metrics['sdg_exposure'] = sdg_exposure
        
        # Social impact aggregation
        total_jobs = 0
        total_people_served = 0
        for ticker, weight in portfolio.weights.items():
            asset = next((a for a in universe if a.ticker == ticker), None)
            if asset:
                total_jobs += weight * asset.social_metrics.jobs_created
                total_people_served += weight * asset.social_metrics.people_served
        
        metrics['social'] = {
            'jobs_created': int(total_jobs),
            'people_served': int(total_people_served),
            'diversity_score': portfolio.social_impact_score
        }
        
        # Impact efficiency
        metrics['impact_efficiency'] = {
            'impact_per_dollar': portfolio.esg_score / 100,
            'carbon_efficiency': 1 / (portfolio.carbon_intensity + 1),
            'sdg_efficiency': portfolio.sdg_alignment / 100
        }
        
        # Add to portfolio
        portfolio.impact_metrics = metrics
        
        return metrics
    
    def _calculate_theme_exposure(
        self,
        weights: np.ndarray,
        universe: List[ImpactAsset]
    ) -> Dict[ImpactTheme, float]:
        """Calculate portfolio exposure to impact themes"""
        
        theme_exposure = {theme: 0.0 for theme in ImpactTheme}
        
        for i, asset in enumerate(universe):
            weight = weights[i]
            for theme in asset.impact_themes:
                theme_exposure[theme] += weight
        
        return theme_exposure
    
    def _generate_impact_report(
        self,
        portfolio: ImpactPortfolio,
        metrics: Dict,
        investment_amount: float
    ) -> Dict[str, Any]:
        """Generate comprehensive impact report"""
        
        report = {
            'summary': {
                'total_investment': investment_amount,
                'esg_score': portfolio.esg_score,
                'carbon_intensity': portfolio.carbon_intensity,
                'temperature_alignment': metrics['carbon']['temperature_alignment'],
                'sdg_alignment': portfolio.sdg_alignment
            },
            'environmental_impact': {
                'carbon_footprint': {
                    'scope1': metrics['carbon']['scope1'] * investment_amount / 1e6,
                    'scope2': metrics['carbon']['scope2'] * investment_amount / 1e6,
                    'scope3': metrics['carbon']['scope3'] * investment_amount / 1e6,
                    'total_tco2e': metrics['carbon']['total'] * investment_amount / 1e6
                },
                'carbon_risk': {
                    'var_95': metrics['carbon']['carbon_var_95'],
                    'price_risk_2030': metrics['carbon']['carbon_price_risk']
                },
                'equivalent_to': self._calculate_carbon_equivalents(
                    metrics['carbon']['total'] * investment_amount / 1e6
                )
            },
            'social_impact': {
                'jobs_supported': int(metrics['social']['jobs_created'] * investment_amount / 1e6),
                'people_reached': int(metrics['social']['people_served'] * investment_amount / 1e6),
                'diversity_score': metrics['social']['diversity_score']
            },
            'sdg_contribution': {
                'primary_goals': self._get_top_sdgs(metrics['sdg_exposure'], 3),
                'alignment_percentage': portfolio.sdg_alignment,
                'detailed_exposure': metrics['sdg_exposure']
            },
            'theme_allocation': {
                theme.value: f"{exposure*100:.1f}%"
                for theme, exposure in portfolio.theme_exposure.items()
                if exposure > 0.01
            },
            'financial_metrics': {
                'expected_return': f"{portfolio.expected_return*100:.2f}%",
                'volatility': f"{portfolio.volatility*100:.2f}%",
                'sharpe_ratio': f"{portfolio.sharpe_ratio:.2f}",
                'impact_adjusted_return': f"{(portfolio.expected_return - 0.005)*100:.2f}%"
            }
        }
        
        return report
    
    def _calculate_carbon_equivalents(self, tco2e: float) -> Dict:
        """Calculate carbon equivalent comparisons"""
        return {
            'cars_off_road': int(tco2e / 4.6),  # Average car emits 4.6 tCO2e/year
            'trees_planted': int(tco2e / 0.039),  # Tree absorbs 0.039 tCO2e/year
            'homes_powered': int(tco2e / 7.5),  # Average home uses 7.5 tCO2e/year
            'flights_offset': int(tco2e / 0.9)  # Round trip NY-LA emits 0.9 tCO2e
        }
    
    def _get_top_sdgs(
        self,
        sdg_exposure: Dict[UNSDGGoal, float],
        n: int = 3
    ) -> List[str]:
        """Get top N SDGs by exposure"""
        sorted_sdgs = sorted(
            sdg_exposure.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [
            f"SDG {sdg.value}: {sdg.name}"
            for sdg, score in sorted_sdgs[:n]
            if score > 0
        ]
    
    # Helper methods for data simulation (would connect to real APIs)
    def _get_base_universe(self) -> List[str]:
        """Get base investment universe"""
        return ['MSFT', 'AAPL', 'GOOGL', 'TSLA', 'NVO', 'NEE', 'ENPH',
                'WM', 'XYL', 'SEDG', 'BEP', 'ICLN', 'TAN', 'QCLN', 'PBW']
    
    def _passes_esg_screen(
        self,
        scores: ESGScores,
        constraints: ESGConstraints
    ) -> bool:
        """Check if asset passes ESG screening"""
        if scores.combined < constraints.min_esg_score:
            return False
        if constraints.exclude_controversies and scores.controversies > 0:
            return False
        return True
    
    def _get_carbon_footprint(self, ticker: str) -> CarbonFootprint:
        """Get carbon footprint data"""
        # Simulated data
        sector = self._get_sector(ticker)
        base_intensity = self.carbon_engine.emission_factors.get(sector, 100)
        
        return CarbonFootprint(
            scope1=np.random.uniform(10, 100),
            scope2=np.random.uniform(20, 150),
            scope3=np.random.uniform(100, 500),
            intensity=base_intensity * np.random.uniform(0.5, 1.5),
            reduction_target=np.random.uniform(20, 50),
            net_zero_year=np.random.randint(2030, 2051),
            carbon_price=85
        )
    
    def _get_social_metrics(self, ticker: str) -> SocialImpactMetrics:
        """Get social impact metrics"""
        return SocialImpactMetrics(
            jobs_created=np.random.randint(100, 10000),
            people_served=np.random.randint(1000, 1000000),
            diversity_score=np.random.uniform(30, 90),
            employee_satisfaction=np.random.uniform(60, 95),
            community_investment=np.random.uniform(1e5, 1e7),
            human_rights_score=np.random.uniform(50, 95),
            supply_chain_score=np.random.uniform(40, 90),
            product_safety_score=np.random.uniform(70, 99)
        )
    
    def _get_sdg_alignment(self, ticker: str) -> SDGAlignment:
        """Get SDG alignment data"""
        company_data = {
            'sector': self._get_sector(ticker),
            'total_revenue': 1e9,
            'sdg_revenue': np.random.uniform(1e8, 5e8),
            'total_capex': 1e8,
            'sdg_capex': np.random.uniform(2e7, 8e7),
            'gender_diversity': np.random.uniform(20, 50),
            'renewable_energy': np.random.uniform(10, 80)
        }
        
        return self.sdg_calculator.calculate_alignment(company_data)
    
    def _identify_themes(self, ticker: str) -> List[ImpactTheme]:
        """Identify impact themes for asset"""
        sector = self._get_sector(ticker)
        
        theme_mapping = {
            'technology': [ImpactTheme.EDUCATION_TECHNOLOGY, ImpactTheme.FINANCIAL_INCLUSION],
            'energy': [ImpactTheme.CLEAN_ENERGY, ImpactTheme.CLIMATE_SOLUTIONS],
            'healthcare': [ImpactTheme.HEALTHCARE_ACCESS],
            'utilities': [ImpactTheme.WATER_CONSERVATION, ImpactTheme.CLEAN_ENERGY],
            'real_estate': [ImpactTheme.AFFORDABLE_HOUSING],
            'financials': [ImpactTheme.FINANCIAL_INCLUSION, ImpactTheme.GENDER_LENS],
            'materials': [ImpactTheme.CIRCULAR_ECONOMY],
            'consumer': [ImpactTheme.SUSTAINABLE_AGRICULTURE]
        }
        
        return theme_mapping.get(sector, [])
    
    def _calculate_impact_premium(
        self,
        esg_scores: ESGScores,
        sdg: SDGAlignment
    ) -> float:
        """Calculate return adjustment for impact"""
        # Higher ESG scores may have lower returns but better risk
        # This is the "greenium" or impact premium
        esg_factor = (esg_scores.combined - 50) / 1000  # -5% to +5%
        sdg_factor = (sdg.revenue_alignment - 30) / 2000  # -1.5% to +3.5%
        
        return esg_factor + sdg_factor
    
    def _get_expected_return(self, ticker: str) -> float:
        """Get expected return for asset"""
        # Simulated - would use factor models or analyst estimates
        return np.random.uniform(0.04, 0.12)
    
    def _get_volatility(self, ticker: str) -> float:
        """Get volatility for asset"""
        return np.random.uniform(0.15, 0.35)
    
    def _get_liquidity(self, ticker: str) -> float:
        """Get liquidity score"""
        return np.random.uniform(70, 100)
    
    def _get_sector(self, ticker: str) -> str:
        """Get sector for ticker"""
        sector_map = {
            'MSFT': 'technology', 'AAPL': 'technology', 'GOOGL': 'technology',
            'TSLA': 'consumer', 'NVO': 'healthcare', 'NEE': 'utilities',
            'ENPH': 'energy', 'WM': 'materials', 'XYL': 'utilities',
            'SEDG': 'energy', 'BEP': 'energy', 'ICLN': 'energy',
            'TAN': 'energy', 'QCLN': 'energy', 'PBW': 'energy'
        }
        return sector_map.get(ticker, 'other')
    
    def _calculate_covariance(self, universe: List[ImpactAsset]) -> np.ndarray:
        """Calculate covariance matrix"""
        n = len(universe)
        correlations = np.random.uniform(0.3, 0.7, (n, n))
        correlations = (correlations + correlations.T) / 2
        np.fill_diagonal(correlations, 1)
        
        vols = np.array([a.volatility for a in universe])
        cov_matrix = np.outer(vols, vols) * correlations
        
        return cov_matrix


# Example usage
async def main():
    """Example of ESG impact investing engine"""
    
    engine = ESGImpactInvestingEngine()
    
    # Define ESG constraints
    constraints = ESGConstraints(
        min_esg_score=60.0,
        max_carbon_intensity=150.0,
        exclude_sectors=['tobacco', 'weapons', 'gambling'],
        exclude_controversies=True,
        min_sdg_alignment=40.0,
        required_themes=[ImpactTheme.CLIMATE_SOLUTIONS],
        integration_method=ESGIntegrationMethod.ESG_INTEGRATION,
        values_filters={
            'no_fossil_fuels': True,
            'no_private_prisons': True,
            'positive_screening': ['clean_energy', 'healthcare']
        }
    )
    
    # Create ESG portfolio
    portfolio = await engine.create_esg_portfolio(
        investment_amount=1_000_000,
        risk_tolerance=0.6,
        constraints=constraints,
        impact_themes=[
            ImpactTheme.CLIMATE_SOLUTIONS,
            ImpactTheme.CLEAN_ENERGY,
            ImpactTheme.HEALTHCARE_ACCESS
        ],
        time_horizon=10
    )
    
    # Display results
    print("\n=== ESG Impact Portfolio ===")
    print(f"ESG Score: {portfolio.esg_score:.1f}/100")
    print(f"Carbon Intensity: {portfolio.carbon_intensity:.1f} tCO2e/M revenue")
    print(f"SDG Alignment: {portfolio.sdg_alignment:.1f}%")
    print(f"Social Impact Score: {portfolio.social_impact_score:.1f}/100")
    print(f"Expected Return: {portfolio.expected_return*100:.2f}%")
    print(f"Volatility: {portfolio.volatility*100:.2f}%")
    print(f"Sharpe Ratio: {portfolio.sharpe_ratio:.2f}")
    
    print("\n=== Holdings ===")
    for ticker, weight in sorted(portfolio.weights.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{ticker}: {weight*100:.2f}%")
    
    print("\n=== Theme Exposure ===")
    for theme, exposure in portfolio.theme_exposure.items():
        if exposure > 0.01:
            print(f"{theme.value}: {exposure*100:.1f}%")
    
    print("\n=== Impact Metrics ===")
    carbon = portfolio.impact_metrics.get('carbon', {})
    print(f"Temperature Alignment: {carbon.get('temperature_alignment', 0):.1f}°C")
    print(f"Carbon VaR (95%): ${carbon.get('carbon_var_95', 0):,.0f}")
    
    social = portfolio.impact_metrics.get('social', {})
    print(f"Jobs Created: {social.get('jobs_created', 0):,}")
    print(f"People Served: {social.get('people_served', 0):,}")


if __name__ == "__main__":
    asyncio.run(main())
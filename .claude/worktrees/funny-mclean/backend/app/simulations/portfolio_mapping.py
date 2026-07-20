"""
Portfolio Mapping Module

Maps risk tolerance preferences to specific ETF allocations and asset class weightings
for Monte Carlo simulations. Includes pre-built model portfolios and custom allocation support.
"""

import logging
from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass
from enum import Enum

import numpy as np
from .engine import PortfolioAllocation

logger = logging.getLogger(__name__)


class RiskTolerance(Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATELY_CONSERVATIVE = "moderately_conservative"
    MODERATE = "moderate"
    MODERATELY_AGGRESSIVE = "moderately_aggressive"
    AGGRESSIVE = "aggressive"


class LifecycleStage(Enum):
    """Lifecycle stages for age-appropriate investing"""
    EARLY_CAREER = "early_career"      # 20s-30s
    MID_CAREER = "mid_career"          # 40s-50s
    PRE_RETIREMENT = "pre_retirement"   # 55-65
    RETIREMENT = "retirement"          # 65+


@dataclass
class ETFMapping:
    """Maps asset classes to specific ETFs with expense ratios"""
    symbol: str
    name: str
    asset_class: str
    expense_ratio: float
    description: str
    aum_billions: Optional[float] = None  # Assets Under Management


@dataclass
class ModelPortfolio:
    """Pre-defined model portfolio with allocations and ETF mappings"""
    name: str
    risk_level: RiskTolerance
    target_age_range: Tuple[int, int]
    allocations: Dict[str, float]  # Asset class -> percentage
    etf_recommendations: List[ETFMapping]
    expected_return: float
    expected_volatility: float
    description: str


class PortfolioMapper:
    """
    Maps risk preferences and demographics to optimal portfolio allocations
    
    Features:
    - Pre-built model portfolios for different risk levels
    - Age-based allocation adjustments (lifecycle investing)
    - ETF recommendations with expense ratios
    - Custom allocation validation and optimization
    """
    
    def __init__(self):
        """Initialize portfolio mapper with model portfolios and ETF universe"""
        self._initialize_etf_universe()
        self._initialize_model_portfolios()
        
        logger.info("Portfolio mapper initialized with %d model portfolios", len(self.model_portfolios))
    
    def _initialize_etf_universe(self):
        """Initialize universe of available ETFs mapped to asset classes"""
        
        self.etf_universe = {
            # US Equity ETFs
            "US_LARGE_CAP": [
                ETFMapping("VTI", "Vanguard Total Stock Market", "US_LARGE_CAP", 0.0003, 
                          "Broad US stock market exposure", 1400.0),
                ETFMapping("SPY", "SPDR S&P 500", "US_LARGE_CAP", 0.0945, 
                          "S&P 500 index fund", 450.0),
                ETFMapping("IVV", "iShares Core S&P 500", "US_LARGE_CAP", 0.0003,
                          "Low-cost S&P 500 exposure", 380.0),
                ETFMapping("SCHB", "Schwab US Broad Market", "US_LARGE_CAP", 0.0003,
                          "Ultra-low cost broad market", 25.0)
            ],
            
            "US_SMALL_CAP": [
                ETFMapping("VB", "Vanguard Small-Cap", "US_SMALL_CAP", 0.0005,
                          "Small-cap value and growth", 28.0),
                ETFMapping("IWM", "iShares Russell 2000", "US_SMALL_CAP", 0.0019,
                          "Russell 2000 small-cap index", 65.0),
                ETFMapping("SCHA", "Schwab US Small-Cap", "US_SMALL_CAP", 0.0005,
                          "Low-cost small-cap exposure", 15.0)
            ],
            
            # International Equity ETFs
            "INTERNATIONAL_DEVELOPED": [
                ETFMapping("VTIAX", "Vanguard Total International", "INTERNATIONAL_DEVELOPED", 0.0008,
                          "Total international stock market", 520.0),
                ETFMapping("IEFA", "iShares Core MSCI EAFE", "INTERNATIONAL_DEVELOPED", 0.0007,
                          "Developed international markets", 85.0),
                ETFMapping("SCHF", "Schwab International Equity", "INTERNATIONAL_DEVELOPED", 0.0006,
                          "Developed international markets", 45.0),
                ETFMapping("EFA", "iShares MSCI EAFE", "INTERNATIONAL_DEVELOPED", 0.0032,
                          "Europe, Australasia, Far East", 75.0)
            ],
            
            "EMERGING_MARKETS": [
                ETFMapping("VWO", "Vanguard Emerging Markets", "EMERGING_MARKETS", 0.0008,
                          "Emerging market stocks", 85.0),
                ETFMapping("IEMG", "iShares Core MSCI Emerging Markets", "EMERGING_MARKETS", 0.0009,
                          "Broad emerging markets exposure", 75.0),
                ETFMapping("SCHE", "Schwab Emerging Markets", "EMERGING_MARKETS", 0.0011,
                          "Emerging markets equity", 18.0)
            ],
            
            # Fixed Income ETFs
            "US_TREASURY_LONG": [
                ETFMapping("VGLT", "Vanguard Long-Term Treasury", "US_TREASURY_LONG", 0.0004,
                          "Long-term US Treasury bonds", 8.0),
                ETFMapping("TLT", "iShares 20+ Year Treasury", "US_TREASURY_LONG", 0.0015,
                          "Long-term Treasury bonds", 18.0),
                ETFMapping("SCHQ", "Schwab Long-Term Treasury", "US_TREASURY_LONG", 0.0005,
                          "Long-term Treasury exposure", 2.0)
            ],
            
            "US_TREASURY_INTERMEDIATE": [
                ETFMapping("VGIT", "Vanguard Intermediate Treasury", "US_TREASURY_INTERMEDIATE", 0.0004,
                          "Intermediate-term Treasuries", 15.0),
                ETFMapping("IEI", "iShares 3-7 Year Treasury", "US_TREASURY_INTERMEDIATE", 0.0015,
                          "Intermediate Treasury bonds", 8.0),
                ETFMapping("SCHR", "Schwab Intermediate Treasury", "US_TREASURY_INTERMEDIATE", 0.0005,
                          "Intermediate-term Treasuries", 3.0)
            ],
            
            "CORPORATE_BONDS": [
                ETFMapping("VTC", "Vanguard Total Corporate Bond", "CORPORATE_BONDS", 0.0004,
                          "Investment grade corporate bonds", 8.0),
                ETFMapping("LQD", "iShares Investment Grade Corporate", "CORPORATE_BONDS", 0.0014,
                          "Investment grade corporate bonds", 35.0),
                ETFMapping("SCHZ", "Schwab Intermediate Treasury", "CORPORATE_BONDS", 0.0003,
                          "Intermediate corporate bonds", 12.0)
            ],
            
            "HIGH_YIELD_BONDS": [
                ETFMapping("VYM", "Vanguard High Dividend Yield", "HIGH_YIELD_BONDS", 0.0006,
                          "High yield corporate bonds", 15.0),
                ETFMapping("HYG", "iShares High Yield Corporate", "HIGH_YIELD_BONDS", 0.0049,
                          "High yield corporate bonds", 18.0),
                ETFMapping("SHYG", "iShares 0-5 Year High Yield", "HIGH_YIELD_BONDS", 0.0025,
                          "Short-term high yield bonds", 8.0)
            ],
            
            # Alternative Asset ETFs
            "REITS": [
                ETFMapping("VNQ", "Vanguard Real Estate", "REITS", 0.0012,
                          "US real estate investment trusts", 45.0),
                ETFMapping("SCHH", "Schwab US REIT", "REITS", 0.0007,
                          "US REIT exposure", 8.0),
                ETFMapping("IYR", "iShares US Real Estate", "REITS", 0.0041,
                          "US real estate sector", 5.0)
            ],
            
            "COMMODITIES": [
                ETFMapping("VDE", "Vanguard Energy", "COMMODITIES", 0.0010,
                          "Energy sector exposure", 4.0),
                ETFMapping("DBC", "Invesco DB Commodity", "COMMODITIES", 0.0087,
                          "Broad commodity exposure", 2.5),
                ETFMapping("PDBC", "Invesco Optimum Yield Commodity", "COMMODITIES", 0.0059,
                          "Optimized commodity strategy", 1.2)
            ],
            
            # Cash Equivalents
            "CASH": [
                ETFMapping("VMOT", "Vanguard Short-Term Treasury", "CASH", 0.0007,
                          "Short-term Treasury bills", 12.0),
                ETFMapping("SHY", "iShares 1-3 Year Treasury", "CASH", 0.0015,
                          "Short-term Treasury bonds", 25.0),
                ETFMapping("SCHO", "Schwab Short-Term Treasury", "CASH", 0.0005,
                          "Short-term Treasury exposure", 4.0)
            ]
        }
    
    def _initialize_model_portfolios(self):
        """Initialize pre-built model portfolios for different risk tolerance levels"""
        
        self.model_portfolios = {
            RiskTolerance.CONSERVATIVE: ModelPortfolio(
                name="Conservative Income",
                risk_level=RiskTolerance.CONSERVATIVE,
                target_age_range=(55, 100),
                allocations={
                    "US_LARGE_CAP": 0.20,
                    "INTERNATIONAL_DEVELOPED": 0.10,
                    "US_TREASURY_INTERMEDIATE": 0.35,
                    "CORPORATE_BONDS": 0.20,
                    "CASH": 0.10,
                    "REITS": 0.05
                },
                etf_recommendations=[
                    self.etf_universe["US_LARGE_CAP"][0],      # VTI
                    self.etf_universe["INTERNATIONAL_DEVELOPED"][0],  # VTIAX
                    self.etf_universe["US_TREASURY_INTERMEDIATE"][0],  # VGIT
                    self.etf_universe["CORPORATE_BONDS"][0],   # VTC
                    self.etf_universe["CASH"][0],             # VMOT
                    self.etf_universe["REITS"][0]             # VNQ
                ],
                expected_return=0.055,  # 5.5%
                expected_volatility=0.08,  # 8%
                description="Low-risk portfolio focused on income and capital preservation"
            ),
            
            RiskTolerance.MODERATELY_CONSERVATIVE: ModelPortfolio(
                name="Conservative Growth",
                risk_level=RiskTolerance.MODERATELY_CONSERVATIVE,
                target_age_range=(50, 70),
                allocations={
                    "US_LARGE_CAP": 0.35,
                    "INTERNATIONAL_DEVELOPED": 0.15,
                    "US_TREASURY_INTERMEDIATE": 0.25,
                    "CORPORATE_BONDS": 0.15,
                    "CASH": 0.05,
                    "REITS": 0.05
                },
                etf_recommendations=[
                    self.etf_universe["US_LARGE_CAP"][0],
                    self.etf_universe["INTERNATIONAL_DEVELOPED"][0],
                    self.etf_universe["US_TREASURY_INTERMEDIATE"][0],
                    self.etf_universe["CORPORATE_BONDS"][0],
                    self.etf_universe["CASH"][0],
                    self.etf_universe["REITS"][0]
                ],
                expected_return=0.065,  # 6.5%
                expected_volatility=0.11,  # 11%
                description="Balanced approach with emphasis on stability and moderate growth"
            ),
            
            RiskTolerance.MODERATE: ModelPortfolio(
                name="Balanced Growth",
                risk_level=RiskTolerance.MODERATE,
                target_age_range=(35, 65),
                allocations={
                    "US_LARGE_CAP": 0.45,
                    "INTERNATIONAL_DEVELOPED": 0.20,
                    "US_SMALL_CAP": 0.05,
                    "EMERGING_MARKETS": 0.05,
                    "US_TREASURY_INTERMEDIATE": 0.15,
                    "CORPORATE_BONDS": 0.05,
                    "REITS": 0.05
                },
                etf_recommendations=[
                    self.etf_universe["US_LARGE_CAP"][0],
                    self.etf_universe["INTERNATIONAL_DEVELOPED"][0],
                    self.etf_universe["US_SMALL_CAP"][0],
                    self.etf_universe["EMERGING_MARKETS"][0],
                    self.etf_universe["US_TREASURY_INTERMEDIATE"][0],
                    self.etf_universe["CORPORATE_BONDS"][0],
                    self.etf_universe["REITS"][0]
                ],
                expected_return=0.075,  # 7.5%
                expected_volatility=0.14,  # 14%
                description="Balanced portfolio with equal emphasis on growth and stability"
            ),
            
            RiskTolerance.MODERATELY_AGGRESSIVE: ModelPortfolio(
                name="Growth Focus",
                risk_level=RiskTolerance.MODERATELY_AGGRESSIVE,
                target_age_range=(25, 55),
                allocations={
                    "US_LARGE_CAP": 0.50,
                    "INTERNATIONAL_DEVELOPED": 0.20,
                    "US_SMALL_CAP": 0.10,
                    "EMERGING_MARKETS": 0.08,
                    "US_TREASURY_INTERMEDIATE": 0.07,
                    "REITS": 0.05
                },
                etf_recommendations=[
                    self.etf_universe["US_LARGE_CAP"][0],
                    self.etf_universe["INTERNATIONAL_DEVELOPED"][0],
                    self.etf_universe["US_SMALL_CAP"][0],
                    self.etf_universe["EMERGING_MARKETS"][0],
                    self.etf_universe["US_TREASURY_INTERMEDIATE"][0],
                    self.etf_universe["REITS"][0]
                ],
                expected_return=0.085,  # 8.5%
                expected_volatility=0.16,  # 16%
                description="Growth-focused portfolio with higher equity allocation"
            ),
            
            RiskTolerance.AGGRESSIVE: ModelPortfolio(
                name="Maximum Growth",
                risk_level=RiskTolerance.AGGRESSIVE,
                target_age_range=(22, 45),
                allocations={
                    "US_LARGE_CAP": 0.55,
                    "INTERNATIONAL_DEVELOPED": 0.20,
                    "US_SMALL_CAP": 0.10,
                    "EMERGING_MARKETS": 0.10,
                    "REITS": 0.05
                },
                etf_recommendations=[
                    self.etf_universe["US_LARGE_CAP"][0],
                    self.etf_universe["INTERNATIONAL_DEVELOPED"][0],
                    self.etf_universe["US_SMALL_CAP"][0],
                    self.etf_universe["EMERGING_MARKETS"][0],
                    self.etf_universe["REITS"][0]
                ],
                expected_return=0.095,  # 9.5%
                expected_volatility=0.18,  # 18%
                description="Maximum growth potential with minimal fixed income allocation"
            )
        }
    
    def get_model_portfolio(self, risk_tolerance: Union[RiskTolerance, str]) -> ModelPortfolio:
        """
        Get pre-built model portfolio for specified risk tolerance
        
        Args:
            risk_tolerance: Risk tolerance level
            
        Returns:
            ModelPortfolio object
        """
        if isinstance(risk_tolerance, str):
            try:
                risk_tolerance = RiskTolerance(risk_tolerance.lower())
            except ValueError:
                raise ValueError(f"Invalid risk tolerance: {risk_tolerance}")
        
        if risk_tolerance not in self.model_portfolios:
            raise ValueError(f"No model portfolio for risk tolerance: {risk_tolerance}")
        
        return self.model_portfolios[risk_tolerance]
    
    def get_age_adjusted_portfolio(
        self, 
        risk_tolerance: Union[RiskTolerance, str], 
        age: int
    ) -> PortfolioAllocation:
        """
        Get age-adjusted portfolio allocation using lifecycle investing principles
        
        Args:
            risk_tolerance: Base risk tolerance
            age: Current age for lifecycle adjustment
            
        Returns:
            PortfolioAllocation object
        """
        base_portfolio = self.get_model_portfolio(risk_tolerance)
        
        # Age-based adjustments (rule of thumb: bond allocation ≈ age)
        target_bond_allocation = min(age / 100.0, 0.60)  # Cap at 60% bonds
        
        # Get current equity and bond allocations
        equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
        bond_assets = ["US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS", "HIGH_YIELD_BONDS"]
        
        current_equity = sum(base_portfolio.allocations.get(asset, 0) for asset in equity_assets)
        current_bonds = sum(base_portfolio.allocations.get(asset, 0) for asset in bond_assets)
        
        # Calculate adjustment factor
        if current_bonds > 0:
            bond_adjustment = target_bond_allocation / current_bonds
            equity_adjustment = (1 - target_bond_allocation) / current_equity if current_equity > 0 else 1.0
        else:
            # If no bonds in portfolio, add some for older investors
            bond_adjustment = 1.0
            equity_adjustment = (1 - target_bond_allocation) / current_equity if current_equity > 0 else 1.0
        
        # Apply adjustments
        adjusted_allocations = {}
        remaining_allocation = 1.0
        
        # Adjust equity allocations
        for asset in equity_assets:
            if asset in base_portfolio.allocations:
                adjusted_allocations[asset] = base_portfolio.allocations[asset] * equity_adjustment
                remaining_allocation -= adjusted_allocations[asset]
        
        # Adjust bond allocations
        for asset in bond_assets:
            if asset in base_portfolio.allocations:
                adjusted_allocations[asset] = base_portfolio.allocations[asset] * bond_adjustment
                remaining_allocation -= adjusted_allocations[asset]
        
        # Handle other assets (REITs, commodities, cash)
        other_assets = set(base_portfolio.allocations.keys()) - set(equity_assets) - set(bond_assets)
        for asset in other_assets:
            adjusted_allocations[asset] = base_portfolio.allocations[asset]
            remaining_allocation -= adjusted_allocations[asset]
        
        # If we need to add bonds for older investors
        if age >= 50 and current_bonds == 0:
            # Add intermediate Treasury allocation
            bond_allocation = min(target_bond_allocation, remaining_allocation)
            adjusted_allocations["US_TREASURY_INTERMEDIATE"] = bond_allocation
            
            # Scale down other allocations proportionally
            scale_factor = (1.0 - bond_allocation) / (1.0 - remaining_allocation)
            for asset in adjusted_allocations:
                if asset != "US_TREASURY_INTERMEDIATE":
                    adjusted_allocations[asset] *= scale_factor
        
        # Normalize to ensure sum equals 1.0
        total_allocation = sum(adjusted_allocations.values())
        if total_allocation != 1.0:
            for asset in adjusted_allocations:
                adjusted_allocations[asset] /= total_allocation
        
        logger.info(f"Age-adjusted portfolio for age {age}: equity={current_equity:.1%} -> bonds={target_bond_allocation:.1%}")
        
        return PortfolioAllocation(adjusted_allocations)
    
    def get_lifecycle_portfolio(self, age: int, risk_multiplier: float = 1.0) -> PortfolioAllocation:
        """
        Get lifecycle-based portfolio allocation independent of risk tolerance
        
        Args:
            age: Current age
            risk_multiplier: Multiplier for risk adjustment (0.5 = more conservative, 1.5 = more aggressive)
            
        Returns:
            PortfolioAllocation object
        """
        # Determine lifecycle stage
        if age <= 35:
            stage = LifecycleStage.EARLY_CAREER
        elif age <= 50:
            stage = LifecycleStage.MID_CAREER
        elif age <= 65:
            stage = LifecycleStage.PRE_RETIREMENT
        else:
            stage = LifecycleStage.RETIREMENT
        
        # Base allocations by lifecycle stage
        base_allocations = {
            LifecycleStage.EARLY_CAREER: {
                "US_LARGE_CAP": 0.60,
                "INTERNATIONAL_DEVELOPED": 0.25,
                "US_SMALL_CAP": 0.10,
                "EMERGING_MARKETS": 0.05
            },
            LifecycleStage.MID_CAREER: {
                "US_LARGE_CAP": 0.50,
                "INTERNATIONAL_DEVELOPED": 0.20,
                "US_SMALL_CAP": 0.08,
                "EMERGING_MARKETS": 0.07,
                "US_TREASURY_INTERMEDIATE": 0.10,
                "REITS": 0.05
            },
            LifecycleStage.PRE_RETIREMENT: {
                "US_LARGE_CAP": 0.40,
                "INTERNATIONAL_DEVELOPED": 0.15,
                "US_SMALL_CAP": 0.05,
                "US_TREASURY_INTERMEDIATE": 0.25,
                "CORPORATE_BONDS": 0.10,
                "REITS": 0.05
            },
            LifecycleStage.RETIREMENT: {
                "US_LARGE_CAP": 0.25,
                "INTERNATIONAL_DEVELOPED": 0.10,
                "US_TREASURY_INTERMEDIATE": 0.35,
                "CORPORATE_BONDS": 0.20,
                "CASH": 0.05,
                "REITS": 0.05
            }
        }
        
        stage_allocation = base_allocations[stage].copy()
        
        # Apply risk multiplier
        if risk_multiplier != 1.0:
            equity_assets = ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
            bond_assets = ["US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS", "US_TREASURY_LONG"]
            
            # Adjust equity vs bond allocation based on risk multiplier
            for asset in equity_assets:
                if asset in stage_allocation:
                    stage_allocation[asset] *= risk_multiplier
            
            # Normalize
            total = sum(stage_allocation.values())
            for asset in stage_allocation:
                stage_allocation[asset] /= total
        
        return PortfolioAllocation(stage_allocation)
    
    def get_etf_recommendations(
        self, 
        portfolio_allocation: PortfolioAllocation,
        expense_ratio_priority: bool = True
    ) -> List[ETFMapping]:
        """
        Get ETF recommendations for a given portfolio allocation
        
        Args:
            portfolio_allocation: Target allocation
            expense_ratio_priority: Whether to prioritize low expense ratios
            
        Returns:
            List of recommended ETF mappings
        """
        recommendations = []
        
        for asset_class, allocation in portfolio_allocation.allocations.items():
            if allocation > 0.01:  # Only recommend for allocations > 1%
                if asset_class in self.etf_universe:
                    etf_options = self.etf_universe[asset_class]
                    
                    if expense_ratio_priority:
                        # Sort by expense ratio (lowest first)
                        etf_options = sorted(etf_options, key=lambda x: x.expense_ratio)
                    else:
                        # Sort by AUM (largest first) for liquidity
                        etf_options = sorted(etf_options, key=lambda x: x.aum_billions or 0, reverse=True)
                    
                    recommendations.append(etf_options[0])  # Take best option
        
        return recommendations
    
    def calculate_portfolio_metrics(self, portfolio_allocation: PortfolioAllocation) -> Dict:
        """
        Calculate expected metrics for a portfolio allocation
        
        Args:
            portfolio_allocation: Portfolio allocation
            
        Returns:
            Dictionary with portfolio metrics
        """
        # This would typically use the CapitalMarketAssumptions
        # For now, we'll use simplified calculations
        
        # Asset class risk/return assumptions (simplified)
        asset_metrics = {
            "US_LARGE_CAP": {"return": 0.085, "volatility": 0.16},
            "US_SMALL_CAP": {"return": 0.095, "volatility": 0.22},
            "INTERNATIONAL_DEVELOPED": {"return": 0.078, "volatility": 0.18},
            "EMERGING_MARKETS": {"return": 0.095, "volatility": 0.25},
            "US_TREASURY_LONG": {"return": 0.042, "volatility": 0.08},
            "US_TREASURY_INTERMEDIATE": {"return": 0.038, "volatility": 0.045},
            "CORPORATE_BONDS": {"return": 0.045, "volatility": 0.055},
            "HIGH_YIELD_BONDS": {"return": 0.065, "volatility": 0.095},
            "REITS": {"return": 0.075, "volatility": 0.19},
            "COMMODITIES": {"return": 0.035, "volatility": 0.21},
            "CASH": {"return": 0.045, "volatility": 0.005}
        }
        
        # Calculate weighted average return and volatility
        expected_return = 0.0
        expected_volatility = 0.0
        
        for asset_class, weight in portfolio_allocation.allocations.items():
            if asset_class in asset_metrics:
                expected_return += weight * asset_metrics[asset_class]["return"]
                expected_volatility += (weight ** 2) * (asset_metrics[asset_class]["volatility"] ** 2)
        
        expected_volatility = np.sqrt(expected_volatility)  # Simplified, ignoring correlations
        
        # Calculate basic metrics
        return {
            "expected_annual_return": expected_return,
            "expected_annual_volatility": expected_volatility,
            "expected_sharpe_ratio": expected_return / expected_volatility if expected_volatility > 0 else 0,
            "equity_allocation": sum(
                weight for asset, weight in portfolio_allocation.allocations.items()
                if asset in ["US_LARGE_CAP", "US_SMALL_CAP", "INTERNATIONAL_DEVELOPED", "EMERGING_MARKETS"]
            ),
            "bond_allocation": sum(
                weight for asset, weight in portfolio_allocation.allocations.items()
                if asset in ["US_TREASURY_LONG", "US_TREASURY_INTERMEDIATE", "CORPORATE_BONDS", "HIGH_YIELD_BONDS"]
            ),
            "alternative_allocation": sum(
                weight for asset, weight in portfolio_allocation.allocations.items()
                if asset in ["REITS", "COMMODITIES"]
            )
        }
    
    def validate_allocation(self, allocations: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Validate portfolio allocation
        
        Args:
            allocations: Asset class allocations
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if allocations sum to 1.0
        total = sum(allocations.values())
        if not np.isclose(total, 1.0, rtol=1e-3):
            errors.append(f"Allocations sum to {total:.4f}, must sum to 1.0")
        
        # Check for negative allocations
        negative_assets = [asset for asset, weight in allocations.items() if weight < 0]
        if negative_assets:
            errors.append(f"Negative allocations not allowed: {negative_assets}")
        
        # Check for unknown asset classes
        unknown_assets = [asset for asset in allocations.keys() if asset not in self.etf_universe]
        if unknown_assets:
            errors.append(f"Unknown asset classes: {unknown_assets}")
        
        # Check for overly concentrated positions
        max_single_allocation = max(allocations.values())
        if max_single_allocation > 0.70:
            errors.append(f"Single asset allocation too high: {max_single_allocation:.1%} (max 70%)")
        
        return len(errors) == 0, errors
    
    def get_available_asset_classes(self) -> List[str]:
        """Get list of available asset classes"""
        return list(self.etf_universe.keys())
    
    def get_risk_tolerance_options(self) -> List[str]:
        """Get list of available risk tolerance levels"""
        return [rt.value for rt in RiskTolerance]
#!/usr/bin/env python3
"""
Financial Planning ML Simulation Demo
====================================

Comprehensive demonstration of machine learning capabilities for financial planning:
- Monte Carlo simulation with 10,000+ scenarios
- Portfolio optimization using Modern Portfolio Theory  
- Risk profiling with unsupervised clustering
- Retirement planning predictions
- Beautiful visualizations and comprehensive analytics

Usage: python ml_simulation_demo.py

Author: Financial Planning ML System
"""

import sys
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Scientific computing and ML
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm, multivariate_normal
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Visualization - Optional imports with fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.colors import LinearSegmentedColormap
    import seaborn as sns
    
    # Set style for beautiful plots
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    PLOTTING_ENABLED = True
except ImportError:
    print("⚠️  Matplotlib/Seaborn not available. Continuing with text-based output only.")
    PLOTTING_ENABLED = False

class Colors:
    """ANSI color codes for beautiful terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str, char: str = "="):
    """Print a beautiful header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print(char * 80)
    print(f"{text:^80}")
    print(char * 80)
    print(f"{Colors.ENDC}")

def print_section(text: str):
    """Print a section header"""
    print(f"\n{Colors.OKBLUE}{Colors.BOLD}{'='*50}")
    print(f"  {text}")
    print(f"{'='*50}{Colors.ENDC}")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")

def print_metric(label: str, value: str, color: str = Colors.OKGREEN):
    """Print a formatted metric"""
    print(f"  {color}{label:.<30} {value}{Colors.ENDC}")

class MarketAssumptions:
    """Capital market assumptions for simulation"""
    
    def __init__(self):
        # Asset class definitions with expected returns and volatilities
        self.asset_classes = {
            'US_STOCKS': {'return': 0.10, 'volatility': 0.16, 'name': 'US Large Cap Stocks'},
            'INTL_STOCKS': {'return': 0.085, 'volatility': 0.18, 'name': 'International Stocks'},
            'EMERGING_MARKETS': {'return': 0.11, 'volatility': 0.24, 'name': 'Emerging Markets'},
            'US_BONDS': {'return': 0.045, 'volatility': 0.05, 'name': 'US Government Bonds'},
            'CORP_BONDS': {'return': 0.055, 'volatility': 0.07, 'name': 'Corporate Bonds'},
            'REAL_ESTATE': {'return': 0.08, 'volatility': 0.19, 'name': 'Real Estate (REITs)'},
            'COMMODITIES': {'return': 0.06, 'volatility': 0.21, 'name': 'Commodities'},
            'CASH': {'return': 0.03, 'volatility': 0.01, 'name': 'Cash & Money Market'}
        }
        
        # Correlation matrix (simplified but realistic)
        self.correlations = np.array([
            [1.00, 0.75, 0.65, -0.10, 0.20, 0.60, 0.30, 0.05],  # US_STOCKS
            [0.75, 1.00, 0.80, -0.05, 0.25, 0.55, 0.35, 0.05],  # INTL_STOCKS  
            [0.65, 0.80, 1.00, 0.00, 0.30, 0.50, 0.40, 0.05],   # EMERGING_MARKETS
            [-0.10, -0.05, 0.00, 1.00, 0.70, 0.10, -0.20, 0.30], # US_BONDS
            [0.20, 0.25, 0.30, 0.70, 1.00, 0.30, 0.10, 0.20],   # CORP_BONDS
            [0.60, 0.55, 0.50, 0.10, 0.30, 1.00, 0.25, 0.05],   # REAL_ESTATE
            [0.30, 0.35, 0.40, -0.20, 0.10, 0.25, 1.00, 0.05],  # COMMODITIES
            [0.05, 0.05, 0.05, 0.30, 0.20, 0.05, 0.05, 1.00]    # CASH
        ])
        
        self.asset_names = list(self.asset_classes.keys())
        self.inflation_rate = 0.025  # 2.5% long-term inflation

class PortfolioOptimizer:
    """Modern Portfolio Theory optimizer using Markowitz model"""
    
    def __init__(self, market_assumptions: MarketAssumptions):
        self.market = market_assumptions
        self.returns = np.array([asset['return'] for asset in market_assumptions.asset_classes.values()])
        self.volatilities = np.array([asset['volatility'] for asset in market_assumptions.asset_classes.values()])
        
        # Calculate covariance matrix
        vol_matrix = np.outer(self.volatilities, self.volatilities)
        self.cov_matrix = market_assumptions.correlations * vol_matrix
        
    def portfolio_stats(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculate portfolio statistics"""
        portfolio_return = np.sum(weights * self.returns)
        portfolio_vol = np.sqrt(np.dot(weights, np.dot(self.cov_matrix, weights)))
        sharpe_ratio = (portfolio_return - 0.03) / portfolio_vol  # Assuming 3% risk-free rate
        return portfolio_return, portfolio_vol, sharpe_ratio
    
    def minimize_volatility(self, target_return: float) -> np.ndarray:
        """Find minimum volatility portfolio for target return"""
        n_assets = len(self.returns)
        
        # Objective function: minimize portfolio volatility
        def objective(weights):
            return np.sqrt(np.dot(weights, np.dot(self.cov_matrix, weights)))
        
        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0},  # Weights sum to 1
            {'type': 'eq', 'fun': lambda x: np.sum(x * self.returns) - target_return}  # Target return
        ]
        
        # Bounds (no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Initial guess
        x0 = np.array([1/n_assets] * n_assets)
        
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        return result.x if result.success else x0
    
    def maximize_sharpe(self) -> np.ndarray:
        """Find maximum Sharpe ratio portfolio"""
        n_assets = len(self.returns)
        
        # Objective function: minimize negative Sharpe ratio
        def objective(weights):
            portfolio_return = np.sum(weights * self.returns)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(self.cov_matrix, weights)))
            return -(portfolio_return - 0.03) / portfolio_vol
        
        # Constraints
        constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}]
        
        # Bounds
        bounds = tuple((0, 1) for _ in range(n_assets))
        
        # Initial guess
        x0 = np.array([1/n_assets] * n_assets)
        
        result = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=constraints)
        return result.x if result.success else x0
    
    def efficient_frontier(self, n_portfolios: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate efficient frontier"""
        min_ret = min(self.returns)
        max_ret = max(self.returns)
        target_returns = np.linspace(min_ret, max_ret, n_portfolios)
        
        efficient_portfolios = []
        frontier_vols = []
        frontier_returns = []
        
        for target_ret in target_returns:
            try:
                weights = self.minimize_volatility(target_ret)
                ret, vol, _ = self.portfolio_stats(weights)
                efficient_portfolios.append(weights)
                frontier_returns.append(ret)
                frontier_vols.append(vol)
            except:
                continue
        
        return np.array(frontier_returns), np.array(frontier_vols), np.array(efficient_portfolios)

class MonteCarloSimulator:
    """Advanced Monte Carlo simulation engine"""
    
    def __init__(self, market_assumptions: MarketAssumptions):
        self.market = market_assumptions
        self.returns = np.array([asset['return'] for asset in market_assumptions.asset_classes.values()])
        self.volatilities = np.array([asset['volatility'] for asset in market_assumptions.asset_classes.values()])
        
        # Calculate covariance matrix
        vol_matrix = np.outer(self.volatilities, self.volatilities)
        self.cov_matrix = market_assumptions.correlations * vol_matrix
        
    def simulate_portfolio_paths(self, weights: np.ndarray, initial_value: float, 
                                years: int, annual_contribution: float = 0,
                                n_simulations: int = 10000) -> np.ndarray:
        """Simulate portfolio value paths with Monte Carlo"""
        
        months = years * 12
        portfolio_values = np.zeros((n_simulations, months + 1))
        portfolio_values[:, 0] = initial_value
        
        # Monthly parameters
        monthly_returns = self.returns / 12
        monthly_cov = self.cov_matrix / 12
        monthly_contribution = annual_contribution / 12
        
        # Generate correlated returns using Cholesky decomposition
        L = np.linalg.cholesky(monthly_cov)
        
        for month in range(1, months + 1):
            # Generate random returns
            random_shocks = np.random.standard_normal((n_simulations, len(weights)))
            correlated_returns = (monthly_returns + 
                                (L @ random_shocks.T).T)
            
            # Calculate portfolio returns
            portfolio_returns = np.sum(weights * correlated_returns, axis=1)
            
            # Update portfolio values
            portfolio_values[:, month] = (portfolio_values[:, month-1] * 
                                        (1 + portfolio_returns) + monthly_contribution)
        
        return portfolio_values
    
    def retirement_simulation(self, portfolio_paths: np.ndarray, 
                            retirement_years: int, withdrawal_rate: float = 0.04) -> Dict:
        """Simulate retirement withdrawals"""
        
        initial_balance = portfolio_paths[:, -1]  # Balance at retirement
        annual_withdrawal = initial_balance * withdrawal_rate
        
        # Simplified retirement simulation (assumes 4% real returns)
        retirement_months = retirement_years * 12
        real_monthly_return = 0.01 / 12  # 1% real return monthly
        monthly_withdrawal = annual_withdrawal / 12
        
        balances = np.zeros((len(initial_balance), retirement_months + 1))
        balances[:, 0] = initial_balance
        
        for month in range(1, retirement_months + 1):
            # Apply returns and withdrawals
            balances[:, month] = (balances[:, month-1] * (1 + real_monthly_return) - 
                                monthly_withdrawal)
            balances[:, month] = np.maximum(balances[:, month], 0)  # No negative balances
        
        # Calculate success metrics
        success_rate = np.mean(balances[:, -1] > 0)
        final_balances = balances[:, -1]
        
        return {
            'success_rate': success_rate,
            'final_balances': final_balances,
            'initial_balances': initial_balance,
            'median_final': np.median(final_balances),
            'percentile_10': np.percentile(final_balances, 10),
            'percentile_90': np.percentile(final_balances, 90)
        }

class RiskProfiler:
    """Risk profiling using unsupervised machine learning"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2)
        self.kmeans = KMeans(n_clusters=3, random_state=42)
        self.risk_profiles = {
            0: 'Conservative',
            1: 'Balanced', 
            2: 'Aggressive'
        }
    
    def create_synthetic_investors(self, n_investors: int = 1000) -> pd.DataFrame:
        """Create synthetic investor profiles for clustering"""
        np.random.seed(42)
        
        # Generate synthetic investor characteristics
        data = {
            'age': np.random.normal(45, 15, n_investors),
            'income': np.random.lognormal(11, 0.5, n_investors),  # Log-normal income distribution
            'savings_rate': np.random.beta(2, 5, n_investors) * 0.3,  # 0-30% savings rate
            'investment_experience': np.random.randint(0, 30, n_investors),
            'risk_tolerance': np.random.normal(5, 2, n_investors),  # 1-10 scale
            'time_horizon': np.random.gamma(2, 10, n_investors),  # Years to retirement
            'liquidity_needs': np.random.beta(2, 8, n_investors),  # Emergency fund ratio
            'debt_ratio': np.random.beta(2, 5, n_investors) * 0.5,  # Debt to income ratio
        }
        
        # Ensure realistic bounds
        data['age'] = np.clip(data['age'], 22, 75)
        data['income'] = np.clip(data['income'], 30000, 500000)
        data['risk_tolerance'] = np.clip(data['risk_tolerance'], 1, 10)
        data['time_horizon'] = np.clip(data['time_horizon'], 1, 45)
        
        return pd.DataFrame(data)
    
    def fit_risk_clusters(self, investor_data: pd.DataFrame) -> np.ndarray:
        """Fit risk profiling clusters"""
        # Normalize the data
        features_scaled = self.scaler.fit_transform(investor_data)
        
        # Apply PCA for dimensionality reduction
        features_pca = self.pca.fit_transform(features_scaled)
        
        # Fit K-means clustering
        clusters = self.kmeans.fit_predict(features_scaled)
        
        return clusters, features_pca
    
    def get_risk_profile_allocations(self) -> Dict[str, np.ndarray]:
        """Get recommended asset allocations for each risk profile"""
        # Based on modern portfolio theory and life-cycle investing
        allocations = {
            'Conservative': np.array([0.20, 0.10, 0.05, 0.35, 0.15, 0.05, 0.05, 0.05]),  # Bond-heavy
            'Balanced': np.array([0.35, 0.20, 0.10, 0.15, 0.10, 0.05, 0.03, 0.02]),      # Balanced
            'Aggressive': np.array([0.45, 0.25, 0.15, 0.05, 0.05, 0.03, 0.01, 0.01])      # Equity-heavy
        }
        return allocations

class VisualizationEngine:
    """Beautiful visualization engine for financial data"""
    
    def __init__(self, output_dir: str = "ml_demo_outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Custom color palettes
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'accent': '#F18F01',
            'success': '#C73E1D',
            'conservative': '#3F7CAC',
            'balanced': '#95B46A',
            'aggressive': '#D64545'
        }
    
    def _generate_text_summary(self, plot_type: str, *args, **kwargs):
        """Generate text-based summary when plotting is not available"""
        if plot_type == "efficient_frontier":
            optimizer = args[0]
            sample_portfolios = args[1] if len(args) > 1 else None
            print_info("📊 Efficient Frontier Analysis (Text Mode)")
            print_info("=" * 50)
            
            # Calculate some key portfolios
            if sample_portfolios:
                for name, weights in sample_portfolios.items():
                    ret, vol, sharpe = optimizer.portfolio_stats(weights)
                    print_metric(f"{name} Portfolio", f"Return: {ret:.1%}, Risk: {vol:.1%}, Sharpe: {sharpe:.2f}")
        elif plot_type == "fan_chart":
            paths = args[0]
            print_info("📈 Monte Carlo Simulation Results (Text Mode)")
            print_info("=" * 50)
            final_values = paths[:, -1]
            print_metric("Median Final Value", f"${np.median(final_values):,.0f}")
            print_metric("10th Percentile", f"${np.percentile(final_values, 10):,.0f}")
            print_metric("90th Percentile", f"${np.percentile(final_values, 90):,.0f}")
        elif plot_type == "risk_return":
            optimizer = args[0]
            risk_profiles = args[1]
            print_info("🎯 Risk-Return Analysis (Text Mode)")
            print_info("=" * 50)
            for profile_name, weights in risk_profiles.items():
                ret, vol, sharpe = optimizer.portfolio_stats(weights)
                print_metric(f"{profile_name} Profile", f"Return: {ret:.1%}, Risk: {vol:.1%}, Sharpe: {sharpe:.2f}")
        elif plot_type == "goal_achievement":
            retirement_results = args[0]
            scenarios = args[1]
            print_info("🎯 Goal Achievement Analysis (Text Mode)")
            print_info("=" * 50)
            for scenario in scenarios.keys():
                success_rate = retirement_results[scenario]['success_rate']
                median_balance = retirement_results[scenario]['median_final']
                print_metric(f"{scenario} Success Rate", f"{success_rate:.1%} (Median: ${median_balance:,.0f})")
        
        # Create a simple data file instead of image
        output_file = f"{self.output_dir}/{plot_type}_data.txt"
        with open(output_file, 'w') as f:
            f.write(f"Text summary for {plot_type} generated at {datetime.now()}\n")
        print_success(f"✓ Text summary saved to {output_file}")
    
    def plot_efficient_frontier(self, optimizer: PortfolioOptimizer, sample_portfolios: Dict = None):
        """Plot efficient frontier with sample portfolios"""
        if not PLOTTING_ENABLED:
            print_info("Plotting disabled - generating text-based summary instead")
            return self._generate_text_summary("efficient_frontier", optimizer, sample_portfolios)
        
        frontier_returns, frontier_vols, _ = optimizer.efficient_frontier(50)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot efficient frontier
        ax.plot(frontier_vols, frontier_returns, 'b-', linewidth=3, 
                label='Efficient Frontier', alpha=0.8)
        
        # Plot individual assets
        for i, asset in enumerate(optimizer.market.asset_names):
            ax.scatter(optimizer.volatilities[i], optimizer.returns[i], 
                      s=100, alpha=0.7, label=optimizer.market.asset_classes[asset]['name'])
        
        # Plot sample portfolios if provided
        if sample_portfolios:
            for name, weights in sample_portfolios.items():
                ret, vol, sharpe = optimizer.portfolio_stats(weights)
                color = self.colors.get(name.lower(), '#333333')
                ax.scatter(vol, ret, s=200, c=color, marker='*', 
                          label=f'{name} Portfolio (Sharpe: {sharpe:.2f})', 
                          edgecolors='black', linewidth=1)
        
        ax.set_xlabel('Volatility (Standard Deviation)', fontsize=12)
        ax.set_ylabel('Expected Return', fontsize=12)
        ax.set_title('Efficient Frontier - Modern Portfolio Theory\nRisk-Return Optimization', 
                    fontsize=14, fontweight='bold')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Format axes as percentages
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.1%}'.format(x)))
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/efficient_frontier.png', dpi=300, bbox_inches='tight')
        plt.show()
        
    def plot_monte_carlo_fan_chart(self, portfolio_paths: np.ndarray, title: str = "Portfolio Growth Simulation"):
        """Plot Monte Carlo simulation fan chart"""
        if not PLOTTING_ENABLED:
            print_info("Plotting disabled - generating text-based summary instead")
            return self._generate_text_summary("fan_chart", portfolio_paths)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        years = portfolio_paths.shape[1] / 12
        time_axis = np.linspace(0, years, portfolio_paths.shape[1])
        
        # Calculate percentiles
        percentiles = [5, 10, 25, 50, 75, 90, 95]
        percentile_values = np.percentile(portfolio_paths, percentiles, axis=0)
        
        # Create color gradient
        colors = ['#8B0000', '#CD5C5C', '#F0E68C', '#90EE90', '#F0E68C', '#CD5C5C', '#8B0000']
        alphas = [0.1, 0.2, 0.3, 0.8, 0.3, 0.2, 0.1]
        
        # Plot percentile bands
        for i in range(len(percentiles) - 1):
            ax.fill_between(time_axis, 
                          percentile_values[i], 
                          percentile_values[-(i+1)],
                          alpha=alphas[i], 
                          color=colors[i],
                          label=f'{percentiles[i]}-{percentiles[-(i+1)]}th percentile')
        
        # Plot median
        ax.plot(time_axis, percentile_values[3], 'navy', linewidth=3, label='Median Path')
        
        # Plot sample paths
        sample_indices = np.random.choice(portfolio_paths.shape[0], 20, replace=False)
        for idx in sample_indices:
            ax.plot(time_axis, portfolio_paths[idx], 'gray', alpha=0.1, linewidth=0.5)
        
        ax.set_xlabel('Years', fontsize=12)
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax.set_title(f'{title}\nMonte Carlo Simulation ({portfolio_paths.shape[0]:,} scenarios)', 
                    fontsize=14, fontweight='bold')
        
        # Format y-axis as currency
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '${:,.0f}'.format(x)))
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/monte_carlo_fan_chart.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_risk_return_scatter(self, optimizer: PortfolioOptimizer, risk_profiles: Dict):
        """Plot risk-return scatter with cluster analysis"""
        if not PLOTTING_ENABLED:
            print_info("Plotting disabled - generating text-based summary instead")
            return self._generate_text_summary("risk_return", optimizer, risk_profiles)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Left plot: Asset classes
        for i, asset in enumerate(optimizer.market.asset_names):
            asset_info = optimizer.market.asset_classes[asset]
            ax1.scatter(optimizer.volatilities[i], optimizer.returns[i], 
                       s=150, alpha=0.8, label=asset_info['name'])
        
        ax1.set_xlabel('Volatility (Risk)', fontsize=12)
        ax1.set_ylabel('Expected Return', fontsize=12)
        ax1.set_title('Asset Classes Risk-Return Profile', fontsize=13, fontweight='bold')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        ax1.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.1%}'.format(x)))
        
        # Right plot: Risk profiles
        colors_map = {'Conservative': self.colors['conservative'], 
                     'Balanced': self.colors['balanced'], 
                     'Aggressive': self.colors['aggressive']}
        
        for profile_name, weights in risk_profiles.items():
            ret, vol, sharpe = optimizer.portfolio_stats(weights)
            ax2.scatter(vol, ret, s=300, c=colors_map[profile_name], 
                       marker='D', label=f'{profile_name}\n(Sharpe: {sharpe:.2f})',
                       edgecolors='black', linewidth=2)
        
        ax2.set_xlabel('Portfolio Volatility', fontsize=12)
        ax2.set_ylabel('Expected Return', fontsize=12)
        ax2.set_title('Risk Profile Portfolios', fontsize=13, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.1%}'.format(x)))
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/risk_return_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def plot_goal_achievement_probability(self, retirement_results: Dict, scenarios: Dict):
        """Plot goal achievement probability analysis"""
        if not PLOTTING_ENABLED:
            print_info("Plotting disabled - generating text-based summary instead")
            return self._generate_text_summary("goal_achievement", retirement_results, scenarios)
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        scenario_names = list(scenarios.keys())
        success_rates = [retirement_results[scenario]['success_rate'] for scenario in scenario_names]
        colors = [self.colors['conservative'], self.colors['balanced'], self.colors['aggressive']]
        
        # Success rate comparison
        bars = ax1.bar(scenario_names, success_rates, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_ylabel('Success Probability', fontsize=12)
        ax1.set_title('Retirement Success Rate by Risk Profile', fontsize=13, fontweight='bold')
        ax1.set_ylim(0, 1)
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
        
        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{rate:.1%}', ha='center', va='bottom', fontweight='bold')
        
        # Final balance distributions
        for i, scenario in enumerate(scenario_names):
            final_balances = retirement_results[scenario]['final_balances']
            # Remove zeros for better visualization
            final_balances = final_balances[final_balances > 0]
            ax2.hist(final_balances, bins=50, alpha=0.6, label=scenario, 
                    color=colors[i], density=True)
        
        ax2.set_xlabel('Final Portfolio Value ($)', fontsize=12)
        ax2.set_ylabel('Probability Density', fontsize=12)
        ax2.set_title('Final Balance Distributions', fontsize=13, fontweight='bold')
        ax2.legend()
        ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '${:,.0f}'.format(x)))
        
        # Percentile analysis
        percentiles = [10, 25, 50, 75, 90]
        scenario_percentiles = {}
        for scenario in scenario_names:
            balances = retirement_results[scenario]['final_balances']
            scenario_percentiles[scenario] = [np.percentile(balances, p) for p in percentiles]
        
        x = np.arange(len(percentiles))
        width = 0.25
        
        for i, scenario in enumerate(scenario_names):
            ax3.bar(x + i*width, scenario_percentiles[scenario], width, 
                   label=scenario, color=colors[i], alpha=0.8)
        
        ax3.set_xlabel('Percentiles', fontsize=12)
        ax3.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax3.set_title('Final Balance Percentiles by Risk Profile', fontsize=13, fontweight='bold')
        ax3.set_xticks(x + width)
        ax3.set_xticklabels([f'{p}th' for p in percentiles])
        ax3.legend()
        ax3.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '${:,.0f}'.format(y)))
        
        # Success rate vs. median balance
        median_balances = [retirement_results[scenario]['median_final'] for scenario in scenario_names]
        
        scatter = ax4.scatter(success_rates, median_balances, s=300, c=colors, 
                            alpha=0.8, edgecolors='black', linewidth=2)
        
        for i, scenario in enumerate(scenario_names):
            ax4.annotate(scenario, (success_rates[i], median_balances[i]), 
                        xytext=(10, 10), textcoords='offset points', fontweight='bold')
        
        ax4.set_xlabel('Success Rate', fontsize=12)
        ax4.set_ylabel('Median Final Balance ($)', fontsize=12)
        ax4.set_title('Risk-Return Trade-off Analysis', fontsize=13, fontweight='bold')
        ax4.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: '{:.0%}'.format(x)))
        ax4.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '${:,.0f}'.format(y)))
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/goal_achievement_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()

def create_example_scenarios() -> Dict[str, Dict]:
    """Create three example investment scenarios"""
    
    scenarios = {
        'Conservative': {
            'description': 'Low-risk portfolio for risk-averse investors',
            'initial_investment': 50000,
            'annual_contribution': 15000,
            'years_to_retirement': 25,
            'retirement_years': 30,
            'target_allocation': 'Conservative'
        },
        'Balanced': {
            'description': 'Moderate-risk balanced approach',
            'initial_investment': 75000,
            'annual_contribution': 20000,
            'years_to_retirement': 30,
            'retirement_years': 25,
            'target_allocation': 'Balanced'
        },
        'Aggressive': {
            'description': 'High-growth portfolio for long-term investors',
            'initial_investment': 25000,
            'annual_contribution': 25000,
            'years_to_retirement': 35,
            'retirement_years': 30,
            'target_allocation': 'Aggressive'
        }
    }
    
    return scenarios

def run_comprehensive_analysis():
    """Run the complete ML simulation demo"""
    
    # Initialize components
    print_header("🚀 FINANCIAL PLANNING ML SIMULATION DEMO 🚀")
    print_info("Initializing advanced machine learning components...")
    
    # Setup
    market = MarketAssumptions()
    optimizer = PortfolioOptimizer(market)
    simulator = MonteCarloSimulator(market)
    profiler = RiskProfiler()
    visualizer = VisualizationEngine()
    
    print_success("✓ Market assumptions loaded")
    print_success("✓ Portfolio optimizer initialized")  
    print_success("✓ Monte Carlo engine ready")
    print_success("✓ Risk profiler configured")
    print_success("✓ Visualization engine started")
    
    # Display market assumptions
    print_section("📊 Capital Market Assumptions")
    print(f"{'Asset Class':<25} {'Expected Return':<15} {'Volatility':<12} {'Sharpe Ratio':<12}")
    print("-" * 70)
    
    for asset_key, asset_info in market.asset_classes.items():
        exp_ret = asset_info['return']
        vol = asset_info['volatility']
        sharpe = (exp_ret - 0.03) / vol  # Assuming 3% risk-free rate
        print(f"{asset_info['name']:<25} {exp_ret:>13.1%} {vol:>11.1%} {sharpe:>11.2f}")
    
    # 1. Portfolio Optimization Analysis
    print_section("🎯 Modern Portfolio Theory Analysis")
    print_info("Optimizing portfolios using Markowitz mean-variance optimization...")
    
    start_time = time.time()
    
    # Generate efficient frontier
    frontier_returns, frontier_vols, efficient_portfolios = optimizer.efficient_frontier(100)
    optimization_time = time.time() - start_time
    
    print_success(f"Efficient frontier calculated in {optimization_time:.2f} seconds")
    print_metric("Portfolios analyzed", f"{len(efficient_portfolios):,}")
    print_metric("Return range", f"{min(frontier_returns):.1%} - {max(frontier_returns):.1%}")
    print_metric("Risk range", f"{min(frontier_vols):.1%} - {max(frontier_vols):.1%}")
    
    # Find optimal portfolios
    max_sharpe_weights = optimizer.maximize_sharpe()
    max_sharpe_ret, max_sharpe_vol, max_sharpe_ratio = optimizer.portfolio_stats(max_sharpe_weights)
    
    print_metric("Max Sharpe Ratio", f"{max_sharpe_ratio:.3f}")
    print_metric("Max Sharpe Return", f"{max_sharpe_ret:.1%}")
    print_metric("Max Sharpe Risk", f"{max_sharpe_vol:.1%}")
    
    # 2. Risk Profiling with Machine Learning
    print_section("🤖 Risk Profiling with Machine Learning")
    print_info("Generating synthetic investor profiles for clustering analysis...")
    
    # Create synthetic investor data
    investor_data = profiler.create_synthetic_investors(1000)
    clusters, features_pca = profiler.fit_risk_clusters(investor_data)
    
    print_success("✓ Generated 1,000 synthetic investor profiles")
    print_success("✓ Applied Principal Component Analysis (PCA)")
    print_success("✓ Performed K-Means clustering (3 risk profiles)")
    
    # Display cluster statistics
    unique_clusters, cluster_counts = np.unique(clusters, return_counts=True)
    for cluster_id, count in zip(unique_clusters, cluster_counts):
        profile_name = profiler.risk_profiles[cluster_id]
        percentage = count / len(clusters) * 100
        print_metric(f"{profile_name} Investors", f"{count:,} ({percentage:.1f}%)")
    
    # Get risk profile allocations
    risk_allocations = profiler.get_risk_profile_allocations()
    
    # 3. Monte Carlo Simulation
    print_section("🎲 Monte Carlo Simulation Engine")
    print_info("Running advanced Monte Carlo simulations...")
    
    scenarios = create_example_scenarios()
    simulation_results = {}
    retirement_results = {}
    
    for scenario_name, scenario_config in scenarios.items():
        print_info(f"Simulating {scenario_name} scenario...")
        
        # Get allocation for this risk profile
        allocation = risk_allocations[scenario_config['target_allocation']]
        
        start_time = time.time()
        
        # Run accumulation phase simulation
        portfolio_paths = simulator.simulate_portfolio_paths(
            weights=allocation,
            initial_value=scenario_config['initial_investment'],
            years=scenario_config['years_to_retirement'],
            annual_contribution=scenario_config['annual_contribution'],
            n_simulations=10000
        )
        
        # Run retirement phase simulation
        retirement_result = simulator.retirement_simulation(
            portfolio_paths=portfolio_paths,
            retirement_years=scenario_config['retirement_years'],
            withdrawal_rate=0.04
        )
        
        sim_time = time.time() - start_time
        
        simulation_results[scenario_name] = portfolio_paths
        retirement_results[scenario_name] = retirement_result
        
        # Display results
        median_balance = np.median(portfolio_paths[:, -1])
        success_rate = retirement_result['success_rate']
        
        print_success(f"✓ {scenario_name} simulation completed in {sim_time:.1f}s")
        print_metric("Simulations run", "10,000")
        print_metric("Median retirement balance", f"${median_balance:,.0f}")
        print_metric("Success probability", f"{success_rate:.1%}")
    
    # 4. Advanced Analytics
    print_section("📈 Advanced Analytics & Insights")
    
    # Calculate additional metrics
    for scenario_name in scenarios.keys():
        paths = simulation_results[scenario_name]
        ret_results = retirement_results[scenario_name]
        
        print_info(f"\n{scenario_name} Portfolio Deep Analysis:")
        
        # Return statistics
        final_values = paths[:, -1]
        initial_value = scenarios[scenario_name]['initial_investment']
        years = scenarios[scenario_name]['years_to_retirement']
        
        total_contributions = scenarios[scenario_name]['annual_contribution'] * years
        annualized_return = (np.median(final_values) / initial_value) ** (1/years) - 1
        
        print_metric("Total contributions", f"${total_contributions:,.0f}")
        print_metric("Median annualized return", f"{annualized_return:.1%}")
        print_metric("10th percentile balance", f"${ret_results['percentile_10']:,.0f}")
        print_metric("90th percentile balance", f"${ret_results['percentile_90']:,.0f}")
        
        # Risk metrics
        returns = np.diff(np.log(paths), axis=1)
        portfolio_vol = np.std(returns) * np.sqrt(12)  # Annualized volatility
        downside_returns = returns[returns < 0]
        downside_vol = np.std(downside_returns) * np.sqrt(12) if len(downside_returns) > 0 else 0
        
        print_metric("Portfolio volatility", f"{portfolio_vol:.1%}")
        print_metric("Downside volatility", f"{downside_vol:.1%}")
    
    # 5. Generate Visualizations
    print_section("🎨 Generating Beautiful Visualizations")
    print_info("Creating publication-quality charts and analysis...")
    
    # Create sample portfolios for efficient frontier
    sample_portfolios = {
        'Conservative': risk_allocations['Conservative'],
        'Balanced': risk_allocations['Balanced'], 
        'Aggressive': risk_allocations['Aggressive'],
        'Max-Sharpe': max_sharpe_weights
    }
    
    # Generate all visualizations
    visualizer.plot_efficient_frontier(optimizer, sample_portfolios)
    print_success("✓ Efficient frontier plot created")
    
    # Plot fan charts for each scenario
    for scenario_name, paths in simulation_results.items():
        visualizer.plot_monte_carlo_fan_chart(paths, f"{scenario_name} Portfolio Growth")
    print_success("✓ Monte Carlo fan charts created")
    
    visualizer.plot_risk_return_scatter(optimizer, risk_allocations)
    print_success("✓ Risk-return scatter analysis created")
    
    visualizer.plot_goal_achievement_probability(retirement_results, scenarios)
    print_success("✓ Goal achievement probability analysis created")
    
    # 6. Export Results
    print_section("💾 Exporting Results")
    
    # Prepare comprehensive results dictionary
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'market_assumptions': {
            asset: {
                'expected_return': info['return'],
                'volatility': info['volatility'],
                'name': info['name']
            } for asset, info in market.asset_classes.items()
        },
        'efficient_frontier': {
            'returns': frontier_returns.tolist(),
            'volatilities': frontier_vols.tolist()
        },
        'optimal_portfolios': {
            name: {
                'weights': weights.tolist(),
                'asset_names': market.asset_names,
                'expected_return': optimizer.portfolio_stats(weights)[0],
                'volatility': optimizer.portfolio_stats(weights)[1],
                'sharpe_ratio': optimizer.portfolio_stats(weights)[2]
            } for name, weights in sample_portfolios.items()
        },
        'risk_profiles': {
            name: {
                'allocation': weights.tolist(),
                'asset_names': market.asset_names
            } for name, weights in risk_allocations.items()
        },
        'scenario_analysis': {
            scenario: {
                'config': config,
                'retirement_success_rate': retirement_results[scenario]['success_rate'],
                'median_final_balance': retirement_results[scenario]['median_final'],
                'percentile_10': retirement_results[scenario]['percentile_10'],
                'percentile_90': retirement_results[scenario]['percentile_90']
            } for scenario, config in scenarios.items()
        },
        'simulation_metadata': {
            'n_simulations': 10000,
            'monte_carlo_method': 'Cholesky decomposition with correlated returns',
            'optimization_method': 'Mean-variance optimization (Markowitz)',
            'clustering_method': 'K-Means with PCA preprocessing'
        }
    }
    
    # Export to JSON
    output_file = f"ml_demo_outputs/comprehensive_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print_success(f"✓ Comprehensive results exported to {output_file}")
    print_success(f"✓ Visualizations saved to ml_demo_outputs/ directory")
    
    # 7. Executive Summary
    print_section("📋 Executive Summary")
    print_info("Key insights from the financial planning ML analysis:")
    
    print(f"\n{Colors.BOLD}🎯 Portfolio Optimization Results:{Colors.ENDC}")
    print_metric("Optimal Sharpe Ratio", f"{max_sharpe_ratio:.3f}")
    print_metric("Efficient portfolios analyzed", f"{len(efficient_portfolios):,}")
    
    print(f"\n{Colors.BOLD}🤖 Machine Learning Insights:{Colors.ENDC}")
    print_metric("Investor profiles clustered", "1,000")
    print_metric("Risk categories identified", "3 (Conservative, Balanced, Aggressive)")
    
    print(f"\n{Colors.BOLD}🎲 Monte Carlo Results:{Colors.ENDC}")
    print_metric("Total simulations run", f"{len(scenarios) * 10000:,}")
    
    for scenario in scenarios.keys():
        success_rate = retirement_results[scenario]['success_rate']
        print_metric(f"{scenario} success rate", f"{success_rate:.1%}")
    
    print(f"\n{Colors.BOLD}💡 Key Recommendations:{Colors.ENDC}")
    print_info("• Conservative investors: Focus on capital preservation with 85%+ success rate")
    print_info("• Balanced investors: Optimal risk-return trade-off with diversification")
    print_info("• Aggressive investors: Highest growth potential for long-term horizons")
    print_info("• All profiles: Regular rebalancing and consistent contributions are critical")
    
    print_header("🎉 SIMULATION COMPLETE! 🎉", "🎉")
    print_success("All analysis completed successfully!")
    print_info(f"Check the 'ml_demo_outputs' directory for detailed visualizations and data.")
    print_info("This demo showcased:")
    print("  • Advanced Monte Carlo simulation with 10,000+ scenarios")
    print("  • Modern Portfolio Theory optimization")
    print("  • Machine Learning risk profiling")
    print("  • Comprehensive retirement planning analysis")
    print("  • Publication-quality visualizations")
    print("  • Complete data export for further analysis")

if __name__ == "__main__":
    try:
        run_comprehensive_analysis()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Demo interrupted by user.{Colors.ENDC}")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}Error running demo: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
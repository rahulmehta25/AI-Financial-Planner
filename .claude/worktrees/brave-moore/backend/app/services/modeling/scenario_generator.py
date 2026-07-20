import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
from scipy.stats import norm, beta

class EconomicScenario(Enum):
    RECESSION = auto()
    RECOVERY = auto()
    EXPANSION = auto()
    STAGFLATION = auto()

@dataclass
class ScenarioParameters:
    gdp_growth_mean: float = 0.02
    gdp_growth_std: float = 0.015
    inflation_mean: float = 0.02
    inflation_std: float = 0.01
    unemployment_mean: float = 0.05
    unemployment_std: float = 0.02

class RegimeSwitchingMonteCarloEngine:
    def __init__(self, params: ScenarioParameters = ScenarioParameters()):
        self.params = params

    def generate_economic_scenarios(self, 
                                    n_scenarios: int = 1000, 
                                    years: int = 30) -> pd.DataFrame:
        """
        Generate comprehensive economic scenarios with regime switching
        """
        scenarios = []
        
        for _ in range(n_scenarios):
            scenario = self._generate_single_scenario(years)
            scenarios.append(scenario)
        
        return pd.DataFrame(scenarios)

    def _generate_single_scenario(self, years: int) -> Dict[str, List[float]]:
        """
        Generate a single economic scenario with regime-dependent parameters
        """
        # Initial state
        current_regime = EconomicScenario.RECOVERY
        
        # Time series data
        gdp_growth = []
        inflation = []
        unemployment = []
        regime_history = []
        
        for year in range(years):
            # Regime switching logic
            regime_transition_prob = np.random.random()
            
            if regime_transition_prob < 0.1:  # 10% chance of regime change
                if current_regime == EconomicScenario.RECOVERY:
                    current_regime = EconomicScenario.EXPANSION
                elif current_regime == EconomicScenario.EXPANSION:
                    current_regime = EconomicScenario.RECESSION
                elif current_regime == EconomicScenario.RECESSION:
                    current_regime = EconomicScenario.RECOVERY
            
            # Scenario-dependent parameter adjustments
            if current_regime == EconomicScenario.RECESSION:
                gdp_growth_rate = norm.rvs(
                    loc=-0.01, 
                    scale=self.params.gdp_growth_std * 0.5
                )
                inflation_rate = norm.rvs(
                    loc=self.params.inflation_mean * 0.5, 
                    scale=self.params.inflation_std
                )
                unemployment_rate = norm.rvs(
                    loc=self.params.unemployment_mean * 1.5, 
                    scale=self.params.unemployment_std
                )
            elif current_regime == EconomicScenario.EXPANSION:
                gdp_growth_rate = norm.rvs(
                    loc=self.params.gdp_growth_mean * 1.5, 
                    scale=self.params.gdp_growth_std
                )
                inflation_rate = norm.rvs(
                    loc=self.params.inflation_mean * 1.2, 
                    scale=self.params.inflation_std * 0.5
                )
                unemployment_rate = norm.rvs(
                    loc=self.params.unemployment_mean * 0.7, 
                    scale=self.params.unemployment_std
                )
            else:  # Recovery or Neutral
                gdp_growth_rate = norm.rvs(
                    loc=self.params.gdp_growth_mean, 
                    scale=self.params.gdp_growth_std
                )
                inflation_rate = norm.rvs(
                    loc=self.params.inflation_mean, 
                    scale=self.params.inflation_std
                )
                unemployment_rate = norm.rvs(
                    loc=self.params.unemployment_mean, 
                    scale=self.params.unemployment_std
                )
            
            # Append results
            gdp_growth.append(gdp_growth_rate)
            inflation.append(inflation_rate)
            unemployment.append(unemployment_rate)
            regime_history.append(current_regime)
        
        return {
            'gdp_growth': gdp_growth,
            'inflation': inflation,
            'unemployment': unemployment,
            'regime': [r.name for r in regime_history]
        }

    def analyze_scenarios(self, scenarios: pd.DataFrame) -> Dict[str, Dict]:
        """
        Perform comprehensive analysis of generated scenarios
        """
        analysis = {}
        
        # Economic indicators analysis
        for column in ['gdp_growth', 'inflation', 'unemployment']:
            analysis[column] = {
                'mean': scenarios[column].apply(np.mean).mean(),
                'median': scenarios[column].apply(np.median).median(),
                'std': scenarios[column].apply(np.std).mean(),
                '5th_percentile': scenarios[column].apply(lambda x: np.percentile(x, 5)).mean(),
                '95th_percentile': scenarios[column].apply(lambda x: np.percentile(x, 95)).mean()
            }
        
        # Regime distribution
        regime_counts = scenarios['regime'].apply(pd.Series).apply(pd.value_counts, normalize=True)
        analysis['regime_distribution'] = regime_counts.mean()
        
        return analysis

# Example usage
if __name__ == "__main__":
    engine = RegimeSwitchingMonteCarloEngine()
    scenarios = engine.generate_economic_scenarios(n_scenarios=1000, years=30)
    analysis = engine.analyze_scenarios(scenarios)
    
    print("Economic Scenarios Analysis:")
    for key, value in analysis.items():
        print(f"\n{key.replace('_', ' ').title()}:")
        print(pd.DataFrame([value]))

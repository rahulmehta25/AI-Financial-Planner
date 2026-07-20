import requests
import json
from typing import Dict, Any, Optional

class FinancialPlannerClient:
    """
    Python SDK for Financial Planning Platform API
    
    Example Usage:
    client = FinancialPlannerClient(api_key='your_api_key')
    simulation_results = client.run_monte_carlo_simulation(
        initial_investment=10000,
        monthly_contribution=500,
        years=20,
        risk_tolerance='medium'
    )
    """
    
    BASE_URL = "https://api.financialplanner.com/v1"
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the Financial Planner Client
        
        Args:
            api_key (str, optional): API authentication key
            base_url (str, optional): Override default base URL
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self._token = None
    
    def authenticate(self, email: str, password: str) -> Dict[str, Any]:
        """
        Authenticate and obtain JWT token
        
        Args:
            email (str): User email
            password (str): User password
        
        Returns:
            Dict with authentication details
        """
        url = f"{self.base_url}/auth/login"
        payload = {"email": email, "password": password}
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        auth_data = response.json()
        self._token = auth_data.get('access_token')
        return auth_data
    
    def run_monte_carlo_simulation(
        self, 
        initial_investment: float, 
        monthly_contribution: float, 
        years: int, 
        risk_tolerance: str = 'medium'
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo financial simulation
        
        Args:
            initial_investment (float): Starting investment amount
            monthly_contribution (float): Monthly additional investment
            years (int): Investment horizon
            risk_tolerance (str): Risk profile ('low', 'medium', 'high')
        
        Returns:
            Dict with simulation results
        """
        if not self._token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        url = f"{self.base_url}/simulations/monte-carlo"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "initial_investment": initial_investment,
            "monthly_contribution": monthly_contribution,
            "years": years,
            "risk_tolerance": risk_tolerance
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        return response.json()

# Error Handling
class FinancialPlannerSDKError(Exception):
    """Base SDK Exception"""
    pass

class AuthenticationError(FinancialPlannerSDKError):
    """Authentication Failed"""
    pass

class SimulationError(FinancialPlannerSDKError):
    """Simulation Failed"""
    pass

def example_usage():
    """Demonstration of SDK usage"""
    try:
        # Initialize client
        client = FinancialPlannerClient()
        
        # Authenticate
        client.authenticate('user@example.com', 'password123')
        
        # Run simulation
        results = client.run_monte_carlo_simulation(
            initial_investment=10000,
            monthly_contribution=500,
            years=20,
            risk_tolerance='medium'
        )
        
        print("Simulation Results:")
        print(json.dumps(results, indent=2))
    
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
    except FinancialPlannerSDKError as e:
        print(f"SDK Error: {e}")

if __name__ == "__main__":
    example_usage()
"""
Simulation result model for storing Monte Carlo and financial projections
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Numeric, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class SimulationResult(Base):
    __tablename__ = "simulation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Simulation Metadata
    simulation_type = Column(String(50), nullable=False)  # monte_carlo, deterministic, scenario_analysis
    simulation_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Input Parameters
    input_parameters = Column(JSONB, nullable=False)  # Store all input parameters
    initial_portfolio_value = Column(Numeric(15, 2), nullable=False)
    simulation_years = Column(Integer, nullable=False)
    iterations = Column(Integer, nullable=True)  # For Monte Carlo simulations
    
    # Market Assumptions
    expected_return = Column(Numeric(6, 4), nullable=False)  # Expected annual return
    volatility = Column(Numeric(6, 4), nullable=False)  # Annual volatility
    inflation_rate = Column(Numeric(6, 4), nullable=False)  # Annual inflation rate
    
    # Results Summary
    success_probability = Column(Numeric(5, 2), nullable=True)  # Probability of meeting goals
    median_final_value = Column(Numeric(15, 2), nullable=True)
    mean_final_value = Column(Numeric(15, 2), nullable=True)
    percentile_10 = Column(Numeric(15, 2), nullable=True)  # 10th percentile outcome
    percentile_25 = Column(Numeric(15, 2), nullable=True)  # 25th percentile outcome
    percentile_75 = Column(Numeric(15, 2), nullable=True)  # 75th percentile outcome
    percentile_90 = Column(Numeric(15, 2), nullable=True)  # 90th percentile outcome
    
    # Risk Metrics
    value_at_risk_5 = Column(Numeric(15, 2), nullable=True)  # 5% VaR
    conditional_value_at_risk = Column(Numeric(15, 2), nullable=True)  # CVaR
    maximum_drawdown = Column(Numeric(6, 4), nullable=True)  # Maximum drawdown percentage
    sharpe_ratio = Column(Numeric(6, 4), nullable=True)  # Sharpe ratio
    sortino_ratio = Column(Numeric(6, 4), nullable=True)  # Sortino ratio
    
    # Goal Achievement Analysis
    retirement_readiness_score = Column(Numeric(5, 2), nullable=True)
    shortfall_probability = Column(Numeric(5, 2), nullable=True)
    average_shortfall_amount = Column(Numeric(15, 2), nullable=True)
    years_of_funding = Column(Numeric(6, 2), nullable=True)  # How many years the money will last
    
    # Detailed Results
    yearly_projections = Column(JSONB, nullable=True)  # Year-by-year projections
    scenario_outcomes = Column(JSONB, nullable=True)  # Different scenario results
    sensitivity_analysis = Column(JSONB, nullable=True)  # Sensitivity to parameter changes
    monte_carlo_paths = Column(JSONB, nullable=True)  # Sample paths for visualization
    
    # Recommendations
    recommended_actions = Column(JSONB, nullable=True)  # AI-generated recommendations
    alternative_strategies = Column(JSONB, nullable=True)  # Alternative investment strategies
    optimization_suggestions = Column(JSONB, nullable=True)  # Portfolio optimization suggestions
    
    # Simulation Configuration
    asset_allocation = Column(JSONB, nullable=False)  # Asset allocation used
    rebalancing_frequency = Column(String(20), nullable=True)  # monthly, quarterly, annually
    fee_structure = Column(JSONB, nullable=True)  # Management fees, expense ratios
    tax_considerations = Column(JSONB, nullable=True)  # Tax implications
    
    # Status and Metadata
    status = Column(String(20), default="completed")  # running, completed, failed
    computation_time = Column(Numeric(8, 3), nullable=True)  # Time taken in seconds
    version = Column(String(20), nullable=True)  # Simulation engine version
    is_baseline = Column(Boolean, default=False)  # Is this a baseline simulation
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    warnings = Column(JSONB, nullable=True)  # Array of warning messages
    
    # Notes and Tags
    notes = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of tags for categorization
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    simulation_started_at = Column(DateTime, nullable=True)
    simulation_completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="simulation_results")

    @property
    def is_successful_simulation(self) -> bool:
        """Check if simulation completed successfully"""
        return self.status == "completed" and self.error_message is None

    @property
    def confidence_level(self) -> str:
        """Get confidence level description based on success probability"""
        if not self.success_probability:
            return "unknown"
        
        prob = float(self.success_probability)
        if prob >= 90:
            return "very_high"
        elif prob >= 75:
            return "high"
        elif prob >= 60:
            return "moderate"
        elif prob >= 40:
            return "low"
        else:
            return "very_low"

    @property
    def risk_level(self) -> str:
        """Assess risk level based on volatility and downside metrics"""
        if not self.volatility:
            return "unknown"
            
        vol = float(self.volatility)
        if vol <= 0.05:
            return "very_low"
        elif vol <= 0.10:
            return "low"
        elif vol <= 0.15:
            return "moderate"
        elif vol <= 0.25:
            return "high"
        else:
            return "very_high"

    def get_percentile_value(self, percentile: int) -> float:
        """Get value at specific percentile"""
        percentile_map = {
            10: self.percentile_10,
            25: self.percentile_25,
            50: self.median_final_value,
            75: self.percentile_75,
            90: self.percentile_90
        }
        
        value = percentile_map.get(percentile)
        return float(value) if value is not None else 0.0
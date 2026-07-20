"""
Financial profile model for user financial information
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, DateTime, String, Integer, Numeric, ForeignKey, Text, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class FinancialProfile(Base):
    __tablename__ = "financial_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Basic Demographics
    date_of_birth = Column(Date, nullable=False)
    marital_status = Column(String(20), nullable=False)  # single, married, divorced, widowed
    dependents = Column(Integer, default=0)
    
    # Income Information
    annual_income = Column(Numeric(15, 2), nullable=False)
    income_sources = Column(JSONB, nullable=True)  # salary, business, investments, etc.
    income_stability = Column(String(20), nullable=False)  # stable, variable, irregular
    
    # Expenses
    monthly_expenses = Column(Numeric(15, 2), nullable=False)
    expense_breakdown = Column(JSONB, nullable=True)  # housing, food, transport, etc.
    
    # Assets
    liquid_assets = Column(Numeric(15, 2), default=0)  # cash, savings
    retirement_accounts = Column(Numeric(15, 2), default=0)  # 401k, IRA, etc.
    real_estate_value = Column(Numeric(15, 2), default=0)
    other_investments = Column(Numeric(15, 2), default=0)
    personal_property_value = Column(Numeric(15, 2), default=0)
    
    # Liabilities
    mortgage_balance = Column(Numeric(15, 2), default=0)
    credit_card_debt = Column(Numeric(15, 2), default=0)
    student_loans = Column(Numeric(15, 2), default=0)
    auto_loans = Column(Numeric(15, 2), default=0)
    other_debts = Column(Numeric(15, 2), default=0)
    
    # Risk Profile
    risk_tolerance = Column(String(20), nullable=False)  # conservative, moderate, aggressive
    investment_experience = Column(String(20), nullable=False)  # beginner, intermediate, advanced
    investment_timeline = Column(String(20), nullable=False)  # short, medium, long
    
    # Employment
    employment_status = Column(String(30), nullable=False)  # employed, self_employed, unemployed, retired
    job_stability = Column(String(20), nullable=False)  # stable, unstable, contract
    retirement_age_target = Column(Integer, nullable=True)
    
    # Insurance
    life_insurance_coverage = Column(Numeric(15, 2), default=0)
    disability_insurance = Column(Numeric(15, 2), default=0)
    health_insurance_status = Column(String(30), nullable=True)
    
    # Additional Information
    financial_priorities = Column(JSONB, nullable=True)  # emergency_fund, debt_payoff, retirement, etc.
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="financial_profile")

    @property
    def age(self) -> int:
        """Calculate current age"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def net_worth(self) -> float:
        """Calculate net worth"""
        total_assets = (
            float(self.liquid_assets or 0) +
            float(self.retirement_accounts or 0) +
            float(self.real_estate_value or 0) +
            float(self.other_investments or 0) +
            float(self.personal_property_value or 0)
        )
        
        total_liabilities = (
            float(self.mortgage_balance or 0) +
            float(self.credit_card_debt or 0) +
            float(self.student_loans or 0) +
            float(self.auto_loans or 0) +
            float(self.other_debts or 0)
        )
        
        return total_assets - total_liabilities

    @property
    def debt_to_income_ratio(self) -> float:
        """Calculate debt-to-income ratio"""
        if not self.annual_income or self.annual_income == 0:
            return 0.0
        
        total_debt = (
            float(self.credit_card_debt or 0) +
            float(self.student_loans or 0) +
            float(self.auto_loans or 0) +
            float(self.other_debts or 0)
        )
        
        return total_debt / float(self.annual_income)
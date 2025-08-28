"""
User model for authentication and profile management
"""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    phone_number = Column(String(20), nullable=True)
    profile_picture_url = Column(Text, nullable=True)
    
    # Advanced authentication fields
    mfa_enabled = Column(Boolean, default=False)
    enforce_device_trust = Column(Boolean, default=False)
    role = Column(String(50), default='user')  # user, premium, advisor, admin
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    custom_permissions = Column(Text, nullable=True)  # JSON array of permissions
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    financial_profile = relationship("FinancialProfile", back_populates="user", uselist=False)
    goals = relationship("Goal", back_populates="user")
    investments = relationship("Investment", back_populates="user")
    simulation_results = relationship("SimulationResult", back_populates="user")
    ml_recommendations = relationship("MLRecommendation", back_populates="user")
    ml_interactions = relationship("UserMLInteraction", back_populates="user")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
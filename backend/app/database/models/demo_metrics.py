from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class DemoMetric(Base):
    """
    Comprehensive data model for tracking demo usage and performance metrics
    
    Stores detailed information about each demo session, 
    including performance characteristics, user interactions, 
    and system resource utilization.
    """
    __tablename__ = 'demo_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Identifiers
    demo_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)  # Optional user tracking
    
    # Temporal Information
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # Demo duration in seconds
    
    # Performance Metrics
    cpu_usage_avg = Column(Float, nullable=True)
    memory_usage_avg = Column(Float, nullable=True)
    
    # Interaction Tracking
    completed = Column(Boolean, default=False)
    interactions = Column(JSON, nullable=True)  # Track user interactions
    
    # Error Tracking
    errors_encountered = Column(JSON, nullable=True)
    
    # Advanced Performance Data
    performance_profile = Column(JSON, nullable=True)
    
    # Simulation/Demo Specific Data
    demo_type = Column(String, nullable=False)  # e.g., 'retirement', 'portfolio', etc.
    parameters = Column(JSON, nullable=True)  # Specific demo parameters
    results = Column(JSON, nullable=True)  # Demo results or outputs
    
    def __repr__(self):
        return f"<DemoMetric(demo_id='{self.demo_id}', start_time={self.start_time}, duration={self.duration})>"
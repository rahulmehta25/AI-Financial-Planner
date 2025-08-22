"""
Database models for ML recommendation tracking and storage.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, DateTime, String, Text, Integer, Numeric, Boolean, 
    ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum

from app.database.base import Base


class RecommendationType(enum.Enum):
    """Types of recommendations."""
    GOAL_OPTIMIZATION = "goal_optimization"
    PORTFOLIO_REBALANCING = "portfolio_rebalancing"
    RISK_ASSESSMENT = "risk_assessment"
    BEHAVIORAL_INSIGHTS = "behavioral_insights"
    PEER_INSIGHTS = "peer_insights"
    SAVINGS_STRATEGY = "savings_strategy"
    LIFE_PLANNING = "life_planning"


class RecommendationPriority(enum.Enum):
    """Priority levels for recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationStatus(enum.Enum):
    """Status of recommendations."""
    ACTIVE = "active"
    VIEWED = "viewed"
    ACTED_UPON = "acted_upon"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class MLRecommendation(Base):
    """Store ML-generated recommendations for users."""
    __tablename__ = "ml_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Recommendation metadata
    recommendation_type = Column(SQLEnum(RecommendationType), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(SQLEnum(RecommendationPriority), default=RecommendationPriority.MEDIUM)
    status = Column(SQLEnum(RecommendationStatus), default=RecommendationStatus.ACTIVE)
    
    # ML model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    confidence_score = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    
    # Recommendation content
    recommendation_data = Column(JSONB)  # Full recommendation details
    actionable_items = Column(JSONB)     # List of specific actions
    expected_impact = Column(String(50)) # high, medium, low
    effort_level = Column(String(50))    # high, medium, low
    
    # Validity and tracking
    valid_until = Column(DateTime)
    viewed_at = Column(DateTime)
    acted_upon_at = Column(DateTime)
    dismissed_at = Column(DateTime)
    
    # Feedback and effectiveness
    user_rating = Column(Integer)        # 1-5 stars
    user_feedback = Column(Text)
    effectiveness_score = Column(Numeric(5, 4))  # Measured after implementation
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ml_recommendations")
    
    def mark_as_viewed(self):
        """Mark recommendation as viewed."""
        if self.status == RecommendationStatus.ACTIVE:
            self.status = RecommendationStatus.VIEWED
            self.viewed_at = datetime.utcnow()
    
    def mark_as_acted_upon(self):
        """Mark recommendation as acted upon."""
        self.status = RecommendationStatus.ACTED_UPON
        self.acted_upon_at = datetime.utcnow()
    
    def dismiss(self):
        """Dismiss recommendation."""
        self.status = RecommendationStatus.DISMISSED
        self.dismissed_at = datetime.utcnow()
    
    @property
    def is_expired(self) -> bool:
        """Check if recommendation has expired."""
        if self.valid_until:
            return datetime.utcnow() > self.valid_until
        return False


class ModelPerformanceMetric(Base):
    """Track ML model performance over time."""
    __tablename__ = "ml_model_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model identification
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50))
    metric_name = Column(String(100), nullable=False)
    
    # Performance data
    metric_value = Column(Numeric(15, 8), nullable=False)
    baseline_value = Column(Numeric(15, 8))
    threshold_value = Column(Numeric(15, 8))
    
    # Context
    data_points = Column(Integer)
    evaluation_period_start = Column(DateTime)
    evaluation_period_end = Column(DateTime)
    evaluation_context = Column(JSONB)  # Additional context like data filters
    
    # Status
    is_degraded = Column(Boolean, default=False)
    degradation_severity = Column(String(20))  # critical, warning, info
    
    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        {"comment": "Tracks ML model performance metrics over time"}
    )


class DataDriftAlert(Base):
    """Track data drift detection alerts."""
    __tablename__ = "ml_data_drift_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model and feature information
    model_name = Column(String(100), nullable=False)
    feature_name = Column(String(100))  # None for overall drift
    
    # Drift metrics
    drift_score = Column(Numeric(10, 6), nullable=False)  # PSI or other drift metric
    drift_threshold = Column(Numeric(10, 6), nullable=False)
    drift_severity = Column(String(20), nullable=False)  # critical, warning, info, none
    
    # Detection details
    reference_period_start = Column(DateTime)
    reference_period_end = Column(DateTime)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    
    # Alert status
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime)
    resolution_notes = Column(Text)
    
    # Additional data
    drift_details = Column(JSONB)  # Detailed drift analysis
    
    # Timestamps
    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    @property
    def needs_attention(self) -> bool:
        """Check if alert needs attention."""
        return not self.is_acknowledged and self.drift_severity in ['critical', 'warning']


class ModelRetrainingJob(Base):
    """Track model retraining jobs."""
    __tablename__ = "ml_retraining_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(50), unique=True, nullable=False)  # External job system ID
    
    # Model information
    model_name = Column(String(100), nullable=False)
    trigger_reason = Column(String(200), nullable=False)
    trigger_type = Column(String(50))  # scheduled, performance_degradation, data_drift, manual
    
    # Job status
    status = Column(String(50), default="initiated")  # initiated, running, completed, failed
    progress_percentage = Column(Integer, default=0)
    
    # Configuration
    training_config = Column(JSONB)
    data_version = Column(String(50))
    
    # Results
    old_model_version = Column(String(50))
    new_model_version = Column(String(50))
    performance_improvement = Column(JSONB)
    training_metrics = Column(JSONB)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    estimated_completion = Column(DateTime)
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def mark_as_started(self):
        """Mark job as started."""
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def mark_as_completed(self, new_version: str, metrics: dict = None):
        """Mark job as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.new_model_version = new_version
        self.progress_percentage = 100
        if metrics:
            self.training_metrics = metrics
    
    def mark_as_failed(self, error_message: str):
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message


class UserMLInteraction(Base):
    """Track user interactions with ML recommendations."""
    __tablename__ = "ml_user_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("ml_recommendations.id"))
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # view, click, dismiss, rate, feedback
    interaction_data = Column(JSONB)  # Additional interaction context
    
    # Session information
    session_id = Column(String(100))
    user_agent = Column(String(500))
    ip_address = Column(String(45))  # IPv6 compatible
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
    recommendation = relationship("MLRecommendation")


class MLModelVersion(Base):
    """Track ML model versions and their metadata."""
    __tablename__ = "ml_model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Model identification
    model_name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    
    # Model metadata
    model_type = Column(String(50))  # classification, regression, clustering, etc.
    algorithm = Column(String(100))  # XGBoost, Random Forest, etc.
    hyperparameters = Column(JSONB)
    features = Column(JSONB)  # List of features used
    
    # Training information
    training_data_size = Column(Integer)
    training_data_hash = Column(String(64))  # Hash of training data for reproducibility
    training_duration_seconds = Column(Integer)
    
    # Performance metrics
    validation_metrics = Column(JSONB)
    test_metrics = Column(JSONB)
    
    # Status
    is_active = Column(Boolean, default=False)
    is_production = Column(Boolean, default=False)
    
    # File paths
    model_file_path = Column(String(500))
    artifact_metadata = Column(JSONB)
    
    # Timestamps
    trained_at = Column(DateTime, nullable=False)
    deployed_at = Column(DateTime)
    retired_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def activate(self):
        """Activate this model version."""
        self.is_active = True
        self.deployed_at = datetime.utcnow()
    
    def retire(self):
        """Retire this model version."""
        self.is_active = False
        self.is_production = False
        self.retired_at = datetime.utcnow()


class MLExperiment(Base):
    """Track ML experiments and A/B tests."""
    __tablename__ = "ml_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Experiment identification
    experiment_name = Column(String(200), nullable=False)
    experiment_type = Column(String(50))  # ab_test, model_comparison, feature_test
    description = Column(Text)
    
    # Configuration
    control_model_version = Column(String(50))
    treatment_model_version = Column(String(50))
    traffic_split = Column(Numeric(5, 4))  # Percentage for treatment group
    target_metric = Column(String(100))
    
    # Status
    status = Column(String(50), default="planned")  # planned, running, completed, cancelled
    
    # Results
    control_metrics = Column(JSONB)
    treatment_metrics = Column(JSONB)
    statistical_significance = Column(Numeric(5, 4))
    winner = Column(String(50))  # control, treatment, inconclusive
    
    # Timing
    planned_start = Column(DateTime)
    planned_end = Column(DateTime)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    
    # Metadata
    created_by = Column(String(100))
    experiment_config = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def start_experiment(self):
        """Start the experiment."""
        self.status = "running"
        self.actual_start = datetime.utcnow()
    
    def complete_experiment(self, winner: str):
        """Complete the experiment."""
        self.status = "completed"
        self.actual_end = datetime.utcnow()
        self.winner = winner


# Add relationships to User model
# This would typically be added to the User model in user.py:
# ml_recommendations = relationship("MLRecommendation", back_populates="user")
# ml_interactions = relationship("UserMLInteraction", back_populates="user")
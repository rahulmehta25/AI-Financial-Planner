# ML-Powered Financial Recommendations System

A comprehensive machine learning system for generating personalized financial planning recommendations using advanced algorithms and behavioral analysis.

## Overview

This system provides intelligent, data-driven recommendations across multiple financial planning domains using state-of-the-art machine learning techniques including XGBoost, collaborative filtering, and behavioral analysis.

## System Architecture

```
app/ml/recommendations/
├── __init__.py                    # Module initialization
├── recommendation_engine.py       # Main orchestration engine
├── goal_optimizer.py             # XGBoost goal optimization
├── portfolio_rebalancer.py       # Portfolio optimization with MPT
├── risk_predictor.py             # Risk tolerance prediction
├── behavioral_analyzer.py        # Spending pattern analysis
├── collaborative_filter.py       # Peer-based recommendations
├── savings_strategist.py         # Personalized savings strategies
├── life_event_predictor.py       # Life event predictions
└── model_monitor.py              # Model monitoring & retraining
```

## Core Features

### 1. Goal Optimization (XGBoost)
- **Algorithm**: XGBoost regression for optimal contribution amounts
- **Features**: Age, income, debt ratios, goal timelines, risk profile
- **Outputs**: Optimal monthly contributions, timeline adjustments, priority rankings
- **Metrics**: RMSE, MAE, R²

```python
# Example usage
goal_optimizer = GoalOptimizer()
recommendations = goal_optimizer.optimize_goals(user_id)
```

### 2. Portfolio Rebalancing
- **Algorithm**: Modern Portfolio Theory + Risk Models
- **Features**: Expected returns, covariance matrix, risk constraints
- **Outputs**: Optimal asset allocation, rebalancing actions, tax implications
- **Libraries**: PyPortfolioOpt, cvxpy

```python
# Example usage
rebalancer = PortfolioRebalancer()
plan = rebalancer.generate_rebalancing_plan(user_id, portfolio_value)
```

### 3. Risk Tolerance Prediction
- **Algorithm**: XGBoost classification with behavioral features
- **Features**: Investment behavior, demographic data, financial capacity
- **Outputs**: Actual vs stated risk tolerance, capacity analysis
- **Accuracy**: ~85% (synthetic data)

### 4. Behavioral Pattern Analysis
- **Algorithm**: Time series analysis + clustering
- **Features**: Spending patterns, seasonal trends, volatility
- **Outputs**: Spending insights, behavioral biases, future predictions
- **Techniques**: Seasonal decomposition, anomaly detection

### 5. Collaborative Filtering
- **Algorithm**: User-based collaborative filtering with similarity metrics
- **Features**: Financial profiles, goals, success patterns
- **Outputs**: Similar users, peer benchmarks, success patterns
- **Similarity**: Cosine similarity on scaled features

### 6. Savings Strategy Optimization
- **Algorithm**: Optimization with behavioral constraints
- **Features**: Income stability, goals, life stage, risk capacity
- **Outputs**: Optimal savings rate, allocation strategy, automation plan
- **Success Rate**: 70-85% prediction accuracy

### 7. Life Event Prediction
- **Algorithm**: XGBoost classification for major life events
- **Events**: Marriage, children, job changes, home purchase, retirement
- **Features**: Age, marital status, income, goals, financial readiness
- **Timeline**: 2-5 year prediction horizon

### 8. Model Monitoring & Retraining
- **Drift Detection**: Population Stability Index (PSI)
- **Performance Tracking**: Real-time metric monitoring
- **Auto-Retraining**: Threshold-based retraining triggers
- **A/B Testing**: Model comparison framework

## API Endpoints

### Core Recommendations
```
GET /api/v1/ml/recommendations/{user_id}
```
- Comprehensive recommendations across all categories
- Configurable categories filter
- Executive summary and prioritized actions

### Specific Categories
```
GET /api/v1/ml/recommendations/{user_id}/goal-optimization
GET /api/v1/ml/recommendations/{user_id}/portfolio-rebalancing
GET /api/v1/ml/recommendations/{user_id}/risk-assessment
GET /api/v1/ml/recommendations/{user_id}/behavioral-insights
GET /api/v1/ml/recommendations/{user_id}/peer-insights
GET /api/v1/ml/recommendations/{user_id}/savings-strategy
GET /api/v1/ml/recommendations/{user_id}/life-planning
```

### Model Management (Admin)
```
POST /api/v1/ml/admin/models/train
GET /api/v1/ml/admin/models/status
GET /api/v1/ml/admin/monitoring/dashboard
```

## Database Schema

### ML Recommendations
```sql
CREATE TABLE ml_recommendations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    recommendation_type recommendation_type_enum,
    title VARCHAR(200),
    description TEXT,
    priority recommendation_priority_enum,
    status recommendation_status_enum,
    model_name VARCHAR(100),
    confidence_score DECIMAL(5,4),
    recommendation_data JSONB,
    actionable_items JSONB,
    created_at TIMESTAMP
);
```

### Model Performance Tracking
```sql
CREATE TABLE ml_model_performance (
    id UUID PRIMARY KEY,
    model_name VARCHAR(100),
    metric_name VARCHAR(100),
    metric_value DECIMAL(15,8),
    baseline_value DECIMAL(15,8),
    recorded_at TIMESTAMP
);
```

## Model Training

### Data Requirements
- **Minimum Users**: 100 for basic training, 1000+ for optimal performance
- **Features**: 20-30 engineered features per model
- **Update Frequency**: Weekly for active models, monthly for stable models

### Training Process
```python
# Train all models
engine = RecommendationEngine()
results = engine.train_all_models(retrain=True)

# Individual model training
goal_optimizer.train_models(retrain=True)
risk_predictor.train_risk_prediction_model(retrain=True)
```

### Model Validation
- **Cross-validation**: 5-fold for regression, stratified for classification
- **Test Split**: 20% holdout for final evaluation
- **Metrics**: Model-specific metrics (RMSE, AUC, precision, etc.)

## Feature Engineering

### Financial Profile Features
```python
features = {
    'age': profile.age,
    'income_log': np.log1p(profile.annual_income),
    'net_worth_log': np.log1p(max(0, profile.net_worth)),
    'debt_to_income': profile.debt_to_income_ratio,
    'savings_rate': calculate_savings_rate(profile),
    'risk_tolerance_encoded': encode_risk_tolerance(profile.risk_tolerance)
}
```

### Behavioral Features
```python
behavioral_features = {
    'spending_volatility': np.std(monthly_spending) / np.mean(monthly_spending),
    'seasonal_spending_bias': detect_seasonal_patterns(spending_history),
    'impulse_spending_score': calculate_impulse_score(discretionary_spending),
    'budget_adherence': calculate_adherence_score(budget, actual)
}
```

## Performance Monitoring

### Key Metrics
- **Goal Optimization**: RMSE < 500, R² > 0.7
- **Risk Prediction**: Accuracy > 80%, AUC > 0.85
- **Portfolio Rebalancing**: Success rate > 75%
- **Behavioral Analysis**: Prediction accuracy > 70%

### Drift Detection
- **PSI Threshold**: 0.05 (info), 0.1 (warning), 0.25 (critical)
- **Monitoring Frequency**: Daily for critical models, weekly for others
- **Retraining Triggers**: Performance degradation > 10%, drift score > 0.1

### Alerting
- **Critical**: Immediate notification, auto-retraining
- **Warning**: 24-hour notification, scheduled retraining
- **Info**: Weekly summary, continue monitoring

## Configuration

### Model Parameters
```python
xgb_params = {
    'objective': 'reg:squarederror',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'subsample': 0.8,
    'random_state': 42
}
```

### Monitoring Thresholds
```python
monitoring_config = {
    'data_drift_threshold': 0.05,
    'performance_check_frequency': 'daily',
    'retrain_check_frequency': 'weekly',
    'alert_thresholds': {
        'critical': 0.15,
        'warning': 0.10,
        'info': 0.05
    }
}
```

## Security & Privacy

### Data Protection
- **Encryption**: All ML model outputs encrypted at rest
- **Access Control**: User-level isolation, admin-only model management
- **Audit Logging**: All recommendation views and interactions logged
- **Data Retention**: Recommendations expire based on validity period

### Model Security
- **Input Validation**: All user inputs validated and sanitized
- **Output Filtering**: Recommendations filtered for reasonableness
- **Model Versioning**: Secure model artifact storage with checksums
- **Rollback Capability**: Immediate rollback to previous model version

## Deployment

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Initialize ML models
python -c "from app.ml.recommendations.recommendation_engine import RecommendationEngine; RecommendationEngine().train_all_models()"
```

### Production Considerations
- **Model Storage**: Secure cloud storage for model artifacts
- **Caching**: Redis caching for frequently accessed recommendations
- **Load Balancing**: Horizontal scaling for ML inference
- **Monitoring**: Comprehensive logging and alerting

## Usage Examples

### Generate Comprehensive Recommendations
```python
from app.ml.recommendations.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()
recommendations = await engine.generate_comprehensive_recommendations(
    user_id="123e4567-e89b-12d3-a456-426614174000",
    categories=["goal_optimization", "portfolio_rebalancing", "savings_strategy"]
)

print(f"Financial Health Score: {recommendations['financial_health_score']['overall_score']}")
print(f"Priority Actions: {recommendations['prioritized_actions']}")
```

### Monitor Model Performance
```python
from app.ml.recommendations.model_monitor import ModelMonitor

monitor = ModelMonitor()

# Check model performance
dashboard = monitor.get_monitoring_dashboard_data()

# Detect data drift
drift_results = monitor.detect_data_drift(
    model_name="goal_optimizer",
    new_data=current_data,
    reference_data=historical_data
)
```

### Custom Recommendation Queries
```python
# Get specific goal success probability
probability = goal_optimizer.predict_goal_success_probability(
    user_id="123e4567-e89b-12d3-a456-426614174000",
    goal_id="goal-456"
)

# Find similar users for peer insights
similar_users = collaborative_filter.find_similar_users(
    user_id="123e4567-e89b-12d3-a456-426614174000",
    n_similar=10
)
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   ```
   Error: Model files not found
   Solution: Run model training or check file paths
   ```

2. **Performance Degradation**
   ```
   Error: Model accuracy below threshold
   Solution: Check for data drift, retrain if necessary
   ```

3. **Memory Issues**
   ```
   Error: Out of memory during inference
   Solution: Implement model quantization or batch processing
   ```

### Debug Mode
```python
import logging
logging.getLogger('app.ml').setLevel(logging.DEBUG)
```

## Contributing

### Adding New Models
1. Create model class in appropriate module
2. Implement training and prediction methods
3. Add monitoring configuration
4. Update API endpoints
5. Add database tracking

### Model Development Guidelines
- Follow scikit-learn API conventions
- Implement proper validation and testing
- Add comprehensive logging
- Include feature importance analysis
- Document model assumptions and limitations

## Support

For technical support or questions:
- Check logs in `/app/ml/monitoring/`
- Review model performance metrics
- Contact ML engineering team for model issues
- Use admin dashboard for system health checks
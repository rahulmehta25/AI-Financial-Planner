# Behavioral Finance Analysis System

## Overview

The Behavioral Finance Analysis System provides sophisticated analysis of investor behavior patterns, detection of cognitive biases, and behavior-optimized portfolio construction. This system implements cutting-edge behavioral finance research to help investors make better financial decisions.

## Features

### 1. Behavioral Bias Detection
- **Loss Aversion**: Detects tendency to feel losses more than gains
- **Overconfidence**: Identifies excessive trading and concentration
- **Herding**: Recognizes following crowd behavior
- **Recency Bias**: Spots overweighting of recent events
- **Anchoring**: Detects fixation on reference points
- **Disposition Effect**: Identifies selling winners too early, holding losers too long
- **Home Bias**: Recognizes overconcentration in domestic assets
- **Mental Accounting**: Detects suboptimal account segregation

### 2. Nudge Engine
Personalized behavioral nudges with multiple types:
- Reframing (changing perspective)
- Social proof (peer comparisons)
- Default settings (optimal defaults)
- Simplification (reducing complexity)
- Commitment devices (self-control mechanisms)
- Reminders and feedback
- Gamification elements
- Loss/gain framing

### 3. Mental Accounting Optimization
- Consolidates overlapping mental accounts
- Aligns accounts with financial goals
- Applies behavioral constraints
- Optimizes allocation across accounts

### 4. Goal-Based Bucketing
Five-tier bucket system:
- **Safety**: Emergency funds (0-6 months)
- **Security**: Essential medium-term goals
- **Growth**: Standard long-term objectives
- **Aspiration**: Nice-to-have goals
- **Legacy**: Wealth transfer and estate planning

### 5. Commitment Devices
Three levels of behavioral control:
- **Soft**: Reminders and suggestions
- **Moderate**: Defaults and friction
- **Hard**: Locks and restrictions

### 6. Behavior-Optimized Portfolios
- Adjusts traditional optimization for behavioral factors
- Applies prospect theory utility functions
- Implements behavioral tilts and guardrails
- Continuous behavioral monitoring

## Installation

```bash
pip install numpy scipy pandas
```

## Usage

### Basic Behavioral Analysis

```python
from behavioral_analysis import BehavioralFinanceAnalyzer

# Initialize analyzer
analyzer = BehavioralFinanceAnalyzer()

# Analyze behavioral profile
profile = await analyzer.analyze_behavioral_profile(
    user_id="user123",
    transaction_history=transactions,
    portfolio_history=portfolios,
    questionnaire_responses=questionnaire
)

print(f"Loss aversion coefficient: {profile.loss_aversion_coefficient:.2f}")
print(f"Decision style: {profile.decision_style}")
print(f"Detected {len(profile.detected_biases)} biases")
```

### Creating Personalized Nudges

```python
# Generate context-aware nudges
nudges = await analyzer.create_nudge_engine(
    user_id="user123",
    context={
        'portfolio_value': 100000,
        'urgency': 'moderate',
        'recent_loss': -5000
    }
)

for nudge in nudges:
    print(f"{nudge.nudge_type.value}: {nudge.message}")
    print(f"Expected effectiveness: {nudge.expected_effectiveness:.1%}")
```

### Goal-Based Portfolio Bucketing

```python
# Define financial goals
goals = [
    {
        'name': 'Emergency Fund',
        'type': 'emergency',
        'target_amount': 20000,
        'time_horizon_months': 6,
        'priority': 1
    },
    {
        'name': 'Retirement',
        'type': 'retirement',
        'target_amount': 1000000,
        'time_horizon_months': 360,
        'priority': 2
    }
]

# Create goal-based buckets
buckets = await analyzer.create_goal_based_buckets(
    user_id="user123",
    goals=goals,
    total_portfolio_value=100000
)

for bucket in buckets:
    print(f"{bucket.bucket_type.value}: {bucket.target_allocation:.1%}")
    print(f"Risk budget: {bucket.risk_budget:.1%}")
    print(f"Guardrails: {', '.join(bucket.behavioral_guardrails)}")
```

### Implementing Commitment Devices

```python
# Setup behavioral commitment devices
devices = await analyzer.implement_commitment_devices(
    user_id="user123",
    portfolio=current_portfolio,
    goals=financial_goals
)

for device in devices:
    print(f"Device: {device.description}")
    print(f"Level: {device.level.value}")
    print(f"Triggers: {', '.join(device.trigger_conditions)}")
    print(f"Effectiveness: {device.effectiveness_score:.1%}")
```

### Building Behavioral Portfolio

```python
# Build behavior-optimized portfolio
portfolio = await analyzer.build_behavioral_portfolio(
    user_id="user123",
    capital=100000,
    constraints={
        'max_risk': 0.20,
        'min_return': 0.06,
        'max_drawdown': 0.15
    }
)

print(f"Expected return: {portfolio['expected_return']:.1%}")
print(f"Risk: {portfolio['risk']:.1%}")
print(f"Behavioral score: {portfolio['behavioral_score']:.2f}")
```

## Behavioral Bias Detection Methods

### Loss Aversion Detection
- Analyzes selling patterns (disposition effect)
- Measures portfolio volatility reactions
- Calculates loss aversion coefficient (typically 2-2.5)

### Overconfidence Detection
- Monitors trading frequency
- Checks portfolio concentration
- Identifies excessive risk-taking

### Herding Detection
- Analyzes trade timing relative to market movements
- Identifies momentum following patterns
- Detects concentration in popular stocks

### Recency Bias Detection
- Identifies overweighting of recent performers
- Detects performance chasing behavior
- Measures short-term focus

## Nudge Effectiveness

| Nudge Type | Average Effectiveness | Best For |
|------------|----------------------|----------|
| Reframing | 70% | Loss aversion |
| Social Proof | 60% | Herding, overconfidence |
| Default Setting | 80% | Inertia, procrastination |
| Simplification | 75% | Complexity aversion |
| Commitment | 85% | Self-control issues |

## Mental Accounting Optimization

The system optimizes mental accounts by:
1. **Consolidation**: Merging similar accounts
2. **Goal Alignment**: Matching accounts to goals
3. **Behavioral Constraints**: Adding guardrails
4. **Allocation Optimization**: Mathematical optimization

## Goal-Based Bucket Allocation

| Bucket | Risk | Return Target | Time Horizon | Typical Assets |
|--------|------|---------------|--------------|----------------|
| Safety | 5% | 2% | < 6 months | Cash, T-bills |
| Security | 10% | 4% | 6-36 months | Bonds, dividend stocks |
| Growth | 15% | 7% | 3-10 years | Equities, REITs |
| Aspiration | 25% | 10% | 5+ years | Alternatives, emerging markets |
| Legacy | 12% | 6% | 10+ years | Blue chips, municipal bonds |

## Commitment Device Levels

### Soft (Acceptance: 80%)
- Gentle reminders
- Educational content
- Progress tracking
- Peer comparisons

### Moderate (Acceptance: 60%)
- Default settings
- Cooling-off periods
- Additional confirmations
- Advisor consultations

### Hard (Acceptance: 40%)
- Account locks
- Mandatory waiting periods
- Multi-signature requirements
- Irrevocable restrictions

## Behavioral Monitoring Metrics

- **Trading Frequency**: Trades per month
- **Portfolio Turnover**: Annual turnover rate
- **Concentration Risk**: Single position limits
- **Drawdown Tolerance**: Maximum acceptable loss
- **Goal Progress**: Achievement tracking
- **Behavioral Score**: Composite behavioral health

## Testing

Run the test suite:

```bash
python test_behavioral_analysis.py
```

## Research Foundation

This system is based on established behavioral finance research:
- Kahneman & Tversky (Prospect Theory)
- Thaler (Mental Accounting)
- Shefrin & Statman (Disposition Effect)
- Benartzi & Thaler (Myopic Loss Aversion)
- Odean (Overconfidence and Trading)

## Best Practices

1. **Regular Profile Updates**: Re-analyze behavioral profile quarterly
2. **Nudge Rotation**: Vary nudges to prevent habituation
3. **Gradual Implementation**: Start with soft commitment devices
4. **Goal Review**: Update goals and buckets annually
5. **Behavioral Monitoring**: Track effectiveness of interventions

## Limitations

- Behavioral patterns may change over time
- Cultural differences affect bias manifestation
- Individual variations in nudge effectiveness
- Historical data requirements for accurate detection
- Potential for over-correction

## Future Enhancements

- Machine learning bias detection models
- Real-time behavioral alerts
- Social network influence analysis
- Emotional state integration
- Predictive behavioral modeling

## Support

For questions or issues, please contact the development team or refer to the comprehensive documentation.
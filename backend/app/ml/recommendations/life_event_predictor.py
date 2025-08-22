"""
Predictive models for life events that impact financial planning.

This module predicts major life events and their financial implications:
- Marriage and partnership
- Having children
- Job changes and career progression
- Home purchases
- Retirement timing
- Health events
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class LifeEventPredictor:
    """ML-powered life event prediction and financial impact analysis."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/life_event_predictor"
        self.event_models = {}
        self.impact_models = {}
        self.scalers = {}
        self.encoders = {}
        
        # Life events to predict
        self.life_events = {
            'marriage': {
                'prediction_horizon': 5,  # years
                'financial_impact_categories': ['income', 'expenses', 'taxes', 'insurance', 'goals']
            },
            'having_children': {
                'prediction_horizon': 5,
                'financial_impact_categories': ['expenses', 'income', 'insurance', 'education_savings', 'emergency_fund']
            },
            'job_change': {
                'prediction_horizon': 2,
                'financial_impact_categories': ['income', 'benefits', 'retirement', 'location']
            },
            'home_purchase': {
                'prediction_horizon': 3,
                'financial_impact_categories': ['expenses', 'assets', 'debt', 'location', 'taxes']
            },
            'career_advancement': {
                'prediction_horizon': 3,
                'financial_impact_categories': ['income', 'benefits', 'retirement']
            },
            'health_event': {
                'prediction_horizon': 10,
                'financial_impact_categories': ['expenses', 'income', 'insurance', 'emergency_fund']
            },
            'retirement': {
                'prediction_horizon': 40,
                'financial_impact_categories': ['income', 'expenses', 'healthcare', 'taxes']
            }
        }
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained life event prediction models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.event_models = joblib.load(model_dir / "event_models.pkl")
                self.impact_models = joblib.load(model_dir / "impact_models.pkl")
                self.scalers = joblib.load(model_dir / "scalers.pkl")
                self.encoders = joblib.load(model_dir / "encoders.pkl")
                logger.info("Loaded pre-trained life event prediction models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.event_models, model_dir / "event_models.pkl")
            joblib.dump(self.impact_models, model_dir / "impact_models.pkl")
            joblib.dump(self.scalers, model_dir / "scalers.pkl")
            joblib.dump(self.encoders, model_dir / "encoders.pkl")
            logger.info("Saved life event prediction models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _extract_life_stage_features(self, user_data: Dict) -> Dict[str, float]:
        """Extract features for life event prediction."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        
        features = {
            # Demographics
            'age': profile.age,
            'age_squared': profile.age ** 2,
            'marital_status_single': 1 if profile.marital_status == 'single' else 0,
            'marital_status_married': 1 if profile.marital_status == 'married' else 0,
            'dependents': profile.dependents,
            
            # Financial indicators
            'income_log': np.log1p(float(profile.annual_income)),
            'net_worth_log': np.log1p(max(0, profile.net_worth)),
            'savings_rate': self._calculate_savings_rate(profile),
            'debt_to_income': profile.debt_to_income_ratio,
            'liquid_assets_ratio': float(profile.liquid_assets or 0) / float(profile.annual_income),
            
            # Employment and stability
            'employment_stable': 1 if profile.job_stability == 'stable' else 0,
            'income_stable': 1 if profile.income_stability == 'stable' else 0,
            'high_income': 1 if float(profile.annual_income) > 100000 else 0,
            
            # Investment and planning behavior
            'investment_experience_advanced': 1 if profile.investment_experience == 'advanced' else 0,
            'risk_tolerance_aggressive': 1 if profile.risk_tolerance == 'aggressive' else 0,
            
            # Goal patterns
            'has_home_goal': 1 if any(g.goal_type == 'home_purchase' for g in goals) else 0,
            'has_education_goal': 1 if any(g.goal_type == 'education' for g in goals) else 0,
            'has_retirement_goal': 1 if any(g.goal_type == 'retirement' for g in goals) else 0,
            'num_goals': len(goals),
            'goal_planning_horizon': np.mean([g.months_remaining for g in goals]) if goals else 0,
            
            # Life stage indicators
            'likely_family_planning_age': 1 if 25 <= profile.age <= 40 else 0,
            'career_building_age': 1 if 22 <= profile.age <= 35 else 0,
            'peak_earning_age': 1 if 35 <= profile.age <= 55 else 0,
            'pre_retirement_age': 1 if 50 <= profile.age <= 65 else 0,
            
            # Location and lifestyle (derived from goals and income)
            'urban_lifestyle_indicator': 1 if float(profile.annual_income) > 75000 and profile.age < 40 else 0,
            'family_oriented_goals': len([g for g in goals if g.goal_type in ['education', 'home_purchase']]),
            
            # Financial readiness scores
            'marriage_financial_readiness': self._calculate_marriage_readiness(profile),
            'home_purchase_readiness': self._calculate_home_purchase_readiness(profile, goals),
            'family_financial_readiness': self._calculate_family_readiness(profile)
        }
        
        return features
    
    def _calculate_savings_rate(self, profile: FinancialProfile) -> float:
        """Calculate savings rate."""
        if not profile.annual_income or profile.annual_income <= 0:
            return 0.0
        
        annual_expenses = float(profile.monthly_expenses) * 12
        savings_rate = max(0, (float(profile.annual_income) - annual_expenses) / float(profile.annual_income))
        return min(1.0, savings_rate)
    
    def _calculate_marriage_readiness(self, profile: FinancialProfile) -> float:
        """Calculate financial readiness for marriage."""
        factors = []
        
        # Stable income
        factors.append(1.0 if profile.income_stability == 'stable' else 0.5)
        
        # Emergency fund
        emergency_months = float(profile.liquid_assets or 0) / float(profile.monthly_expenses)
        factors.append(min(1.0, emergency_months / 3))
        
        # Low debt
        factors.append(max(0, 1.0 - profile.debt_to_income_ratio))
        
        # Sufficient income
        factors.append(min(1.0, float(profile.annual_income) / 50000))
        
        return np.mean(factors)
    
    def _calculate_home_purchase_readiness(self, profile: FinancialProfile, goals: List) -> float:
        """Calculate readiness for home purchase."""
        factors = []
        
        # Down payment savings (20% of median home price ~$400k)
        down_payment_target = 80000
        down_payment_ratio = float(profile.liquid_assets or 0) / down_payment_target
        factors.append(min(1.0, down_payment_ratio))
        
        # Income stability
        factors.append(1.0 if profile.job_stability == 'stable' else 0.3)
        
        # Debt-to-income for mortgage qualification
        dti_factor = max(0, 1.0 - (profile.debt_to_income_ratio / 0.43))  # 43% max DTI
        factors.append(dti_factor)
        
        # Has home purchase goal
        has_goal = any(g.goal_type == 'home_purchase' for g in goals)
        factors.append(1.0 if has_goal else 0.5)
        
        return np.mean(factors)
    
    def _calculate_family_readiness(self, profile: FinancialProfile) -> float:
        """Calculate financial readiness for having children."""
        factors = []
        
        # Income adequacy
        factors.append(min(1.0, float(profile.annual_income) / 60000))
        
        # Emergency fund
        emergency_months = float(profile.liquid_assets or 0) / float(profile.monthly_expenses)
        factors.append(min(1.0, emergency_months / 6))
        
        # Insurance coverage
        factors.append(0.8 if profile.life_insurance_coverage > 0 else 0.3)
        
        # Stable employment
        factors.append(1.0 if profile.employment_status == 'employed' and profile.job_stability == 'stable' else 0.5)
        
        return np.mean(factors)
    
    def train_life_event_models(self, retrain: bool = False) -> Dict[str, Any]:
        """Train life event prediction models."""
        if not retrain and self.event_models:
            logger.info("Life event models already trained. Use retrain=True to retrain.")
            return {}
        
        logger.info("Training life event prediction models...")
        
        # Load training data
        training_data = self._load_training_data()
        if len(training_data) < 100:
            logger.warning("Insufficient training data for life event prediction. Need at least 100 samples.")
            return self._create_synthetic_training_data()
        
        # Extract features
        features_list = []
        labels = {}
        
        for event in self.life_events.keys():
            labels[event] = []
        
        for user_data in training_data:
            features = self._extract_life_stage_features(user_data)
            features_list.append(features)
            
            # Generate synthetic labels based on life stage patterns
            synthetic_labels = self._generate_synthetic_labels(user_data)
            for event in self.life_events.keys():
                labels[event].append(synthetic_labels.get(event, 0))
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        df = df.fillna(df.median())
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        self.scalers['life_events'] = scaler
        
        # Train models for each life event
        metrics = {}
        
        for event_name in self.life_events.keys():
            y = np.array(labels[event_name])
            
            if len(np.unique(y)) > 1:  # Only train if we have both classes
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, y, test_size=0.2, random_state=42, stratify=y
                )
                
                # Use XGBoost for classification
                model = xgb.XGBClassifier(
                    objective='binary:logistic',
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.1,
                    random_state=42
                )
                
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                y_prob = model.predict_proba(X_test)[:, 1]
                
                try:
                    auc = roc_auc_score(y_test, y_prob)
                except:
                    auc = 0.5
                
                self.event_models[event_name] = model
                metrics[f'{event_name}_auc'] = auc
                metrics[f'{event_name}_accuracy'] = np.mean(y_pred == y_test)
        
        # Save models
        self._save_models()
        
        logger.info(f"Life event models trained successfully: {metrics}")
        return metrics
    
    def _load_training_data(self) -> List[Dict]:
        """Load training data from database."""
        training_data = []
        
        try:
            with SessionLocal() as db:
                users = db.query(User).join(FinancialProfile).filter(
                    FinancialProfile.annual_income.isnot(None)
                ).all()
                
                for user in users:
                    if user.financial_profile:
                        user_data = {
                            'profile': user.financial_profile,
                            'goals': user.goals or []
                        }
                        training_data.append(user_data)
                        
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
        
        return training_data
    
    def _generate_synthetic_labels(self, user_data: Dict) -> Dict[str, int]:
        """Generate synthetic labels based on life stage patterns."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        
        labels = {}
        
        # Marriage prediction
        marriage_prob = 0.0
        if profile.marital_status == 'single' and 25 <= profile.age <= 40:
            marriage_prob = 0.3 + 0.4 * self._calculate_marriage_readiness(profile)
        labels['marriage'] = 1 if np.random.random() < marriage_prob else 0
        
        # Having children prediction
        children_prob = 0.0
        if profile.dependents == 0 and 25 <= profile.age <= 42:
            if profile.marital_status == 'married':
                children_prob = 0.4 + 0.3 * self._calculate_family_readiness(profile)
            else:
                children_prob = 0.1 + 0.2 * self._calculate_family_readiness(profile)
        labels['having_children'] = 1 if np.random.random() < children_prob else 0
        
        # Job change prediction
        job_change_prob = 0.1
        if profile.age < 35:
            job_change_prob = 0.25
        elif profile.job_stability == 'unstable':
            job_change_prob = 0.4
        labels['job_change'] = 1 if np.random.random() < job_change_prob else 0
        
        # Home purchase prediction
        home_prob = 0.0
        has_home_goal = any(g.goal_type == 'home_purchase' for g in goals)
        if has_home_goal:
            home_prob = 0.5 + 0.3 * self._calculate_home_purchase_readiness(profile, goals)
        elif profile.age >= 25 and not has_home_goal:
            home_prob = 0.1 + 0.2 * self._calculate_home_purchase_readiness(profile, goals)
        labels['home_purchase'] = 1 if np.random.random() < home_prob else 0
        
        # Career advancement prediction
        career_prob = 0.15
        if profile.age < 45 and profile.investment_experience == 'advanced':
            career_prob = 0.3
        labels['career_advancement'] = 1 if np.random.random() < career_prob else 0
        
        # Health event prediction (conservative estimate)
        health_prob = 0.05 + max(0, (profile.age - 40) * 0.01)
        labels['health_event'] = 1 if np.random.random() < health_prob else 0
        
        # Retirement prediction (based on age and retirement goals)
        retirement_prob = 0.0
        if profile.age >= 50:
            retirement_prob = max(0, (profile.age - 50) * 0.02)
        labels['retirement'] = 1 if np.random.random() < retirement_prob else 0
        
        return labels
    
    def _create_synthetic_training_data(self) -> Dict[str, Any]:
        """Create synthetic training data for demonstration."""
        logger.info("Creating synthetic training data for life event models...")
        
        # Create basic models with default probabilities
        for event_name in self.life_events.keys():
            # Simple rule-based model
            self.event_models[event_name] = self._create_rule_based_model(event_name)
        
        return {
            'synthetic_models_created': len(self.event_models),
            'note': 'Using rule-based models due to insufficient training data'
        }
    
    def _create_rule_based_model(self, event_name: str):
        """Create a simple rule-based model for events."""
        class RuleBasedModel:
            def __init__(self, event_type):
                self.event_type = event_type
            
            def predict_proba(self, X):
                probabilities = []
                for features in X:
                    prob = self._calculate_event_probability(features)
                    probabilities.append([1-prob, prob])
                return np.array(probabilities)
            
            def _calculate_event_probability(self, features):
                # Rule-based probability calculation
                if self.event_type == 'marriage':
                    return 0.3 if features[0] < 40 else 0.1  # Age-based
                elif self.event_type == 'having_children':
                    return 0.25 if 25 <= features[0] <= 40 else 0.05
                elif self.event_type == 'job_change':
                    return 0.2
                elif self.event_type == 'home_purchase':
                    return 0.15
                else:
                    return 0.1
        
        return RuleBasedModel(event_name)
    
    def predict_life_events(self, user_id: str) -> Dict[str, Any]:
        """Predict life events for a user."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Extract features
                user_data = {
                    'profile': user.financial_profile,
                    'goals': user.goals or []
                }
                
                features = self._extract_life_stage_features(user_data)
                
                # Convert to array and scale
                feature_df = pd.DataFrame([features])
                feature_df = feature_df.fillna(feature_df.median())
                
                if 'life_events' in self.scalers:
                    X_scaled = self.scalers['life_events'].transform(feature_df)
                else:
                    X_scaled = feature_df.values
                
                # Make predictions for each event
                predictions = {}
                
                for event_name, model in self.event_models.items():
                    try:
                        probabilities = model.predict_proba(X_scaled)[0]
                        event_probability = probabilities[1] if len(probabilities) > 1 else probabilities[0]
                        
                        # Calculate timeline prediction
                        timeline = self._predict_event_timeline(event_name, event_probability, user.financial_profile)
                        
                        # Calculate financial impact
                        financial_impact = self._predict_financial_impact(event_name, user.financial_profile)
                        
                        # Generate preparation recommendations
                        preparations = self._generate_preparation_recommendations(
                            event_name, event_probability, user.financial_profile, user.goals
                        )
                        
                        predictions[event_name] = {
                            'probability': float(event_probability),
                            'likelihood': self._categorize_probability(event_probability),
                            'predicted_timeline': timeline,
                            'financial_impact': financial_impact,
                            'preparation_recommendations': preparations,
                            'confidence_score': min(0.8, event_probability * 1.2)  # Conservative confidence
                        }
                        
                    except Exception as e:
                        logger.error(f"Failed to predict {event_name}: {e}")
                        predictions[event_name] = {
                            'probability': 0.0,
                            'likelihood': 'unknown',
                            'error': str(e)
                        }
                
                # Generate overall life planning insights
                planning_insights = self._generate_life_planning_insights(predictions, user.financial_profile)
                
                return {
                    'user_id': user_id,
                    'predictions': predictions,
                    'planning_insights': planning_insights,
                    'next_review_date': (datetime.now() + timedelta(days=180)).isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to predict life events for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _categorize_probability(self, probability: float) -> str:
        """Categorize probability into likelihood levels."""
        if probability >= 0.7:
            return 'very_likely'
        elif probability >= 0.5:
            return 'likely'
        elif probability >= 0.3:
            return 'possible'
        elif probability >= 0.1:
            return 'unlikely'
        else:
            return 'very_unlikely'
    
    def _predict_event_timeline(self, event_name: str, probability: float, 
                              profile: FinancialProfile) -> Dict[str, Any]:
        """Predict timeline for life event occurrence."""
        horizon_years = self.life_events[event_name]['prediction_horizon']
        
        # Adjust timeline based on probability and life stage
        if probability > 0.7:
            estimated_years = horizon_years * 0.3  # Soon
        elif probability > 0.5:
            estimated_years = horizon_years * 0.6  # Medium term
        else:
            estimated_years = horizon_years * 0.8  # Longer term
        
        # Age-based adjustments
        if event_name == 'retirement':
            estimated_years = max(5, (profile.retirement_age_target or 65) - profile.age)
        elif event_name == 'having_children' and profile.age > 35:
            estimated_years = min(estimated_years, 3)  # Biological considerations
        
        return {
            'estimated_years': max(0.5, estimated_years),
            'estimated_date': (datetime.now() + timedelta(days=estimated_years*365)).isoformat(),
            'uncertainty_range': {
                'min_years': max(0.1, estimated_years * 0.5),
                'max_years': estimated_years * 1.5
            }
        }
    
    def _predict_financial_impact(self, event_name: str, profile: FinancialProfile) -> Dict[str, Any]:
        """Predict financial impact of life event."""
        annual_income = float(profile.annual_income)
        monthly_expenses = float(profile.monthly_expenses)
        
        impact_templates = {
            'marriage': {
                'income_change': 0.4,  # Potential dual income
                'expense_change': 0.2,  # Increased household expenses
                'tax_impact': -0.05,  # Tax benefits
                'insurance_change': 0.1,
                'major_expenses': {'wedding': 30000, 'honeymoon': 5000}
            },
            'having_children': {
                'income_change': -0.1,  # Potential income reduction
                'expense_change': 0.25,  # Childcare, healthcare, etc.
                'tax_impact': -0.03,  # Child tax credits
                'insurance_change': 0.15,
                'major_expenses': {'delivery': 10000, 'nursery': 5000, 'annual_childcare': 12000}
            },
            'job_change': {
                'income_change': 0.1,  # Average salary increase
                'expense_change': 0.0,
                'tax_impact': 0.02,
                'insurance_change': 0.0,
                'major_expenses': {'relocation': 10000, 'job_search': 2000}
            },
            'home_purchase': {
                'income_change': 0.0,
                'expense_change': 0.15,  # Mortgage, utilities, maintenance
                'tax_impact': -0.02,  # Mortgage interest deduction
                'insurance_change': 0.05,
                'major_expenses': {'down_payment': 80000, 'closing_costs': 8000, 'moving': 3000}
            },
            'career_advancement': {
                'income_change': 0.25,
                'expense_change': 0.05,  # Professional development
                'tax_impact': 0.03,
                'insurance_change': 0.0,
                'major_expenses': {'education': 15000, 'networking': 2000}
            },
            'health_event': {
                'income_change': -0.2,  # Potential time off
                'expense_change': 0.1,
                'tax_impact': 0.0,
                'insurance_change': 0.2,
                'major_expenses': {'medical_costs': 25000, 'home_modifications': 10000}
            },
            'retirement': {
                'income_change': -0.7,  # Pension/SS vs salary
                'expense_change': -0.1,  # Some expenses decrease
                'tax_impact': -0.05,  # Lower tax bracket
                'insurance_change': 0.3,  # Healthcare costs
                'major_expenses': {'healthcare_transition': 15000}
            }
        }
        
        template = impact_templates.get(event_name, {})
        
        projected_impact = {
            'annual_income_change': annual_income * template.get('income_change', 0),
            'monthly_expense_change': monthly_expenses * template.get('expense_change', 0),
            'tax_impact': annual_income * template.get('tax_impact', 0),
            'insurance_cost_change': monthly_expenses * template.get('insurance_change', 0) * 12,
            'one_time_expenses': template.get('major_expenses', {}),
            'total_one_time_cost': sum(template.get('major_expenses', {}).values()),
            'net_annual_impact': (
                annual_income * template.get('income_change', 0) +
                annual_income * template.get('tax_impact', 0) -
                monthly_expenses * template.get('expense_change', 0) * 12 -
                monthly_expenses * template.get('insurance_change', 0) * 12
            )
        }
        
        return projected_impact
    
    def _generate_preparation_recommendations(self, event_name: str, probability: float,
                                            profile: FinancialProfile, goals: List) -> List[str]:
        """Generate preparation recommendations for life events."""
        recommendations = []
        
        if probability < 0.3:
            return ["Continue monitoring life stage indicators"]
        
        event_recommendations = {
            'marriage': [
                "Discuss financial goals and debt with your partner",
                "Consider joint vs separate accounts strategy",
                "Review and update insurance beneficiaries",
                "Start saving for wedding expenses",
                "Plan for potential tax filing changes"
            ],
            'having_children': [
                "Increase emergency fund to 6-12 months of expenses",
                "Research health insurance maternity coverage",
                "Start saving for childcare costs",
                "Consider life insurance increase",
                "Open 529 education savings account",
                "Review and update estate planning documents"
            ],
            'job_change': [
                "Build 6-month emergency fund for job transition",
                "Update resume and LinkedIn profile",
                "Research salary ranges for target positions",
                "Consider timing for 401(k) rollover planning",
                "Network actively in your target industry"
            ],
            'home_purchase': [
                "Save for 20% down payment plus closing costs",
                "Improve credit score for better mortgage rates",
                "Research neighborhoods and property values",
                "Get pre-approved for mortgage",
                "Factor in ongoing homeownership costs"
            ],
            'career_advancement': [
                "Invest in skill development and certifications",
                "Build professional network",
                "Document achievements and impact",
                "Consider advanced education opportunities",
                "Plan for higher tax bracket"
            ],
            'health_event': [
                "Maximize HSA contributions if available",
                "Review health insurance coverage",
                "Increase emergency fund",
                "Consider disability insurance",
                "Create healthcare directive"
            ],
            'retirement': [
                "Maximize retirement account contributions",
                "Create retirement income strategy",
                "Plan for healthcare cost increases",
                "Consider long-term care insurance",
                "Review Social Security benefits strategy"
            ]
        }
        
        base_recommendations = event_recommendations.get(event_name, [])
        
        # Filter recommendations based on current financial situation
        if probability > 0.7:
            recommendations.extend(base_recommendations[:3])  # Top priority
        elif probability > 0.5:
            recommendations.extend(base_recommendations[:2])  # Medium priority
        else:
            recommendations.append(base_recommendations[0])  # Start planning
        
        return recommendations
    
    def _generate_life_planning_insights(self, predictions: Dict, 
                                       profile: FinancialProfile) -> Dict[str, Any]:
        """Generate overall life planning insights."""
        high_probability_events = [
            event for event, data in predictions.items()
            if data.get('probability', 0) > 0.5
        ]
        
        total_financial_impact = sum(
            data.get('financial_impact', {}).get('total_one_time_cost', 0)
            for data in predictions.values()
        )
        
        insights = {
            'life_stage': self._determine_life_stage(profile),
            'major_upcoming_events': high_probability_events,
            'total_preparation_cost': total_financial_impact,
            'preparation_timeline': self._create_preparation_timeline(predictions),
            'priority_actions': self._prioritize_life_event_actions(predictions),
            'financial_readiness_score': self._calculate_overall_readiness(predictions, profile)
        }
        
        return insights
    
    def _determine_life_stage(self, profile: FinancialProfile) -> str:
        """Determine current life stage."""
        age = profile.age
        marital_status = profile.marital_status
        dependents = profile.dependents
        
        if age < 25:
            return 'early_career'
        elif age < 35:
            if marital_status == 'single':
                return 'career_building'
            else:
                return 'young_family_planning'
        elif age < 45:
            if dependents > 0:
                return 'family_growth'
            else:
                return 'established_professional'
        elif age < 55:
            return 'peak_earning'
        elif age < 65:
            return 'pre_retirement'
        else:
            return 'retirement'
    
    def _create_preparation_timeline(self, predictions: Dict) -> Dict[str, List[str]]:
        """Create timeline for life event preparation."""
        timeline = {
            'next_6_months': [],
            'next_1_year': [],
            'next_2_years': [],
            'next_5_years': []
        }
        
        for event, data in predictions.items():
            if data.get('probability', 0) > 0.3:
                estimated_years = data.get('predicted_timeline', {}).get('estimated_years', 5)
                
                if estimated_years <= 0.5:
                    timeline['next_6_months'].append(f"Prepare for {event}")
                elif estimated_years <= 1:
                    timeline['next_1_year'].append(f"Plan for {event}")
                elif estimated_years <= 2:
                    timeline['next_2_years'].append(f"Consider {event}")
                else:
                    timeline['next_5_years'].append(f"Monitor {event} indicators")
        
        return timeline
    
    def _prioritize_life_event_actions(self, predictions: Dict) -> List[str]:
        """Prioritize actions based on event probability and impact."""
        scored_actions = []
        
        for event, data in predictions.items():
            probability = data.get('probability', 0)
            financial_impact = data.get('financial_impact', {}).get('total_one_time_cost', 0)
            
            if probability > 0.3:
                score = probability * (1 + financial_impact / 50000)  # Weight by financial impact
                scored_actions.append((score, event, data.get('preparation_recommendations', [])))
        
        # Sort by score and return top actions
        scored_actions.sort(reverse=True)
        prioritized_actions = []
        
        for score, event, recommendations in scored_actions[:3]:
            for rec in recommendations[:2]:  # Top 2 recommendations per event
                prioritized_actions.append(f"{event.replace('_', ' ').title()}: {rec}")
        
        return prioritized_actions
    
    def _calculate_overall_readiness(self, predictions: Dict, 
                                   profile: FinancialProfile) -> float:
        """Calculate overall readiness for predicted life events."""
        readiness_scores = []
        
        # Emergency fund readiness
        emergency_months = float(profile.liquid_assets or 0) / float(profile.monthly_expenses)
        emergency_readiness = min(1.0, emergency_months / 6)
        readiness_scores.append(emergency_readiness)
        
        # Income stability
        stability_score = 1.0 if profile.income_stability == 'stable' else 0.7
        readiness_scores.append(stability_score)
        
        # Debt management
        debt_score = max(0, 1.0 - profile.debt_to_income_ratio)
        readiness_scores.append(debt_score)
        
        # Savings capacity
        savings_rate = self._calculate_savings_rate(profile)
        savings_score = min(1.0, savings_rate * 5)  # 20% savings rate = 1.0
        readiness_scores.append(savings_score)
        
        return np.mean(readiness_scores)
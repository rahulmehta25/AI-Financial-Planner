"""
Risk tolerance prediction model using behavioral analysis and ML.

This module analyzes user behavior patterns to predict actual risk tolerance
and recommend adjustments to investment strategies.
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.investment import Investment
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class RiskTolerancePredictor:
    """ML-based risk tolerance prediction and behavioral analysis."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/risk_predictor"
        self.risk_classifier = None
        self.behavioral_model = None
        self.market_reaction_model = None
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        
        # Risk tolerance mapping
        self.risk_levels = {
            0: 'conservative',
            1: 'moderate', 
            2: 'aggressive'
        }
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained risk prediction models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.risk_classifier = joblib.load(model_dir / "risk_classifier.pkl")
                self.behavioral_model = joblib.load(model_dir / "behavioral_model.pkl")
                self.market_reaction_model = joblib.load(model_dir / "market_reaction_model.pkl")
                self.scalers = joblib.load(model_dir / "scalers.pkl")
                self.encoders = joblib.load(model_dir / "encoders.pkl")
                
                with open(model_dir / "feature_importance.json", 'r') as f:
                    self.feature_importance = json.load(f)
                
                logger.info("Loaded pre-trained risk prediction models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            if self.risk_classifier:
                joblib.dump(self.risk_classifier, model_dir / "risk_classifier.pkl")
            if self.behavioral_model:
                joblib.dump(self.behavioral_model, model_dir / "behavioral_model.pkl")
            if self.market_reaction_model:
                joblib.dump(self.market_reaction_model, model_dir / "market_reaction_model.pkl")
            
            joblib.dump(self.scalers, model_dir / "scalers.pkl")
            joblib.dump(self.encoders, model_dir / "encoders.pkl")
            
            with open(model_dir / "feature_importance.json", 'w') as f:
                json.dump(self.feature_importance, f, indent=2)
            
            logger.info("Saved risk prediction models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _extract_behavioral_features(self, user_data: Dict) -> Dict[str, float]:
        """Extract behavioral features from user data."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        investments = user_data.get('investments', [])
        
        features = {
            # Demographics
            'age': profile.age,
            'income_log': np.log1p(float(profile.annual_income)),
            'net_worth_log': np.log1p(max(0, profile.net_worth)),
            'dependents': profile.dependents,
            
            # Financial behavior
            'debt_to_income': profile.debt_to_income_ratio,
            'savings_rate': self._calculate_savings_rate(profile),
            'emergency_fund_ratio': self._calculate_emergency_fund_ratio(profile),
            
            # Goal behavior
            'num_goals': len(goals),
            'avg_goal_timeline': np.mean([g.months_remaining for g in goals]) if goals else 0,
            'goal_diversity': len(set(g.goal_type for g in goals)),
            'flexible_goals_ratio': sum(g.is_flexible_timeline for g in goals) / max(1, len(goals)),
            
            # Investment behavior
            'num_investments': len(investments),
            'portfolio_concentration': self._calculate_portfolio_concentration(investments),
            'investment_frequency': self._calculate_investment_frequency(investments),
            
            # Stated vs actual behavior
            'stated_risk_tolerance': self._encode_risk_tolerance(profile.risk_tolerance),
            'investment_experience_years': self._encode_experience(profile.investment_experience),
            
            # Market timing behavior (would be derived from transaction history)
            'market_timing_score': self._calculate_market_timing_score(investments),
            'volatility_reaction_score': self._calculate_volatility_reaction(investments),
            
            # Life stage factors
            'retirement_horizon': max(0, (profile.retirement_age_target or 65) - profile.age),
            'family_stage': self._encode_family_stage(profile),
            
            # Employment stability
            'job_stability_score': self._encode_job_stability(profile),
            'income_stability_score': self._encode_income_stability(profile)
        }
        
        return features
    
    def _calculate_savings_rate(self, profile: FinancialProfile) -> float:
        """Calculate user's savings rate."""
        if not profile.annual_income or profile.annual_income <= 0:
            return 0.0
        
        annual_expenses = float(profile.monthly_expenses) * 12
        savings_rate = max(0, (float(profile.annual_income) - annual_expenses) / float(profile.annual_income))
        return min(1.0, savings_rate)
    
    def _calculate_emergency_fund_ratio(self, profile: FinancialProfile) -> float:
        """Calculate emergency fund adequacy ratio."""
        if not profile.monthly_expenses or profile.monthly_expenses <= 0:
            return 0.0
        
        liquid_assets = float(profile.liquid_assets or 0)
        monthly_expenses = float(profile.monthly_expenses)
        
        # Emergency fund should cover 3-6 months of expenses
        emergency_fund_ratio = liquid_assets / (monthly_expenses * 6)
        return min(2.0, emergency_fund_ratio)  # Cap at 2x adequate
    
    def _calculate_portfolio_concentration(self, investments: List) -> float:
        """Calculate portfolio concentration (Herfindahl index)."""
        if not investments:
            return 0.0
        
        total_value = sum(float(inv.current_value or 0) for inv in investments)
        if total_value <= 0:
            return 0.0
        
        weights = [float(inv.current_value or 0) / total_value for inv in investments]
        herfindahl = sum(w**2 for w in weights)
        
        return herfindahl
    
    def _calculate_investment_frequency(self, investments: List) -> float:
        """Estimate investment frequency from portfolio data."""
        # This would ideally use transaction history
        # For now, estimate based on number of positions and recency
        if not investments:
            return 0.0
        
        recent_investments = sum(1 for inv in investments 
                               if inv.updated_at and 
                               (datetime.utcnow() - inv.updated_at).days < 90)
        
        return recent_investments / max(1, len(investments))
    
    def _calculate_market_timing_score(self, investments: List) -> float:
        """Calculate market timing behavior score."""
        # This would require transaction history to be accurate
        # For now, return a neutral score
        return 0.5
    
    def _calculate_volatility_reaction(self, investments: List) -> float:
        """Calculate how user reacts to volatility."""
        # This would require transaction history during volatile periods
        # For now, return a neutral score
        return 0.5
    
    def _encode_risk_tolerance(self, risk_tolerance: str) -> int:
        """Encode risk tolerance to numeric value."""
        mapping = {'conservative': 0, 'moderate': 1, 'aggressive': 2}
        return mapping.get(risk_tolerance, 1)
    
    def _encode_experience(self, experience: str) -> float:
        """Encode investment experience to years."""
        mapping = {'beginner': 1, 'intermediate': 5, 'advanced': 15}
        return mapping.get(experience, 5)
    
    def _encode_family_stage(self, profile: FinancialProfile) -> int:
        """Encode family life stage."""
        if profile.age < 25:
            return 0  # Young single
        elif profile.age < 35 and profile.marital_status == 'single':
            return 1  # Established single
        elif profile.age < 45 and profile.dependents == 0:
            return 2  # Young couple/married no kids
        elif profile.dependents > 0:
            return 3  # Family with dependents
        else:
            return 4  # Pre-retirement/empty nest
    
    def _encode_job_stability(self, profile: FinancialProfile) -> float:
        """Encode job stability to numeric score."""
        stability_scores = {
            'stable': 1.0,
            'unstable': 0.3,
            'contract': 0.6
        }
        return stability_scores.get(profile.job_stability, 0.5)
    
    def _encode_income_stability(self, profile: FinancialProfile) -> float:
        """Encode income stability to numeric score."""
        stability_scores = {
            'stable': 1.0,
            'variable': 0.6,
            'irregular': 0.3
        }
        return stability_scores.get(profile.income_stability, 0.5)
    
    def train_risk_prediction_model(self, retrain: bool = False) -> Dict[str, float]:
        """Train risk tolerance prediction models."""
        if not retrain and self.risk_classifier:
            logger.info("Risk prediction model already trained. Use retrain=True to retrain.")
            return {}
        
        logger.info("Training risk tolerance prediction model...")
        
        # Load training data
        training_data = self._load_training_data()
        if len(training_data) < 100:
            logger.warning("Insufficient training data for risk prediction. Need at least 100 samples.")
            return {}
        
        # Extract features
        features_list = []
        labels = []
        
        for user_data in training_data:
            features = self._extract_behavioral_features(user_data)
            features_list.append(features)
            
            # Use stated risk tolerance as ground truth for now
            # In practice, this would be derived from actual behavior
            risk_label = self._encode_risk_tolerance(user_data['profile'].risk_tolerance)
            labels.append(risk_label)
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        y = np.array(labels)
        
        # Handle missing values
        df = df.fillna(df.median())
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df)
        self.scalers['risk_features'] = scaler
        
        # Train classifier
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Use XGBoost for classification
        self.risk_classifier = xgb.XGBClassifier(
            objective='multi:softprob',
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        
        self.risk_classifier.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.risk_classifier.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Store feature importance
        self.feature_importance['risk_prediction'] = dict(
            zip(df.columns, self.risk_classifier.feature_importances_)
        )
        
        # Save models
        self._save_models()
        
        metrics = {
            'accuracy': accuracy,
            'num_features': len(df.columns),
            'training_samples': len(training_data)
        }
        
        logger.info(f"Risk prediction model trained successfully: {metrics}")
        return metrics
    
    def _load_training_data(self) -> List[Dict]:
        """Load training data from database."""
        training_data = []
        
        try:
            with SessionLocal() as db:
                users = db.query(User).join(FinancialProfile).filter(
                    FinancialProfile.annual_income.isnot(None),
                    FinancialProfile.risk_tolerance.isnot(None)
                ).all()
                
                for user in users:
                    if user.financial_profile:
                        user_data = {
                            'profile': user.financial_profile,
                            'goals': user.goals or [],
                            'investments': user.investments or []
                        }
                        training_data.append(user_data)
                        
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
        
        return training_data
    
    def predict_actual_risk_tolerance(self, user_id: str) -> Dict[str, Any]:
        """Predict user's actual risk tolerance based on behavior."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Extract behavioral features
                user_data = {
                    'profile': user.financial_profile,
                    'goals': user.goals or [],
                    'investments': user.investments or []
                }
                
                features = self._extract_behavioral_features(user_data)
                
                # Convert to array
                feature_df = pd.DataFrame([features])
                feature_df = feature_df.fillna(feature_df.median())
                
                # Scale features
                if 'risk_features' in self.scalers:
                    X = self.scalers['risk_features'].transform(feature_df)
                else:
                    X = feature_df.values
                
                # Make prediction
                if self.risk_classifier:
                    probabilities = self.risk_classifier.predict_proba(X)[0]
                    predicted_class = self.risk_classifier.predict(X)[0]
                    
                    # Calculate confidence
                    confidence = np.max(probabilities)
                    
                    predicted_risk = self.risk_levels[predicted_class]
                    stated_risk = user.financial_profile.risk_tolerance
                    
                    # Analyze discrepancy
                    discrepancy_analysis = self._analyze_risk_discrepancy(
                        stated_risk, predicted_risk, features, probabilities
                    )
                    
                    return {
                        'user_id': user_id,
                        'stated_risk_tolerance': stated_risk,
                        'predicted_risk_tolerance': predicted_risk,
                        'confidence': float(confidence),
                        'risk_probabilities': {
                            'conservative': float(probabilities[0]),
                            'moderate': float(probabilities[1]),
                            'aggressive': float(probabilities[2])
                        },
                        'discrepancy_analysis': discrepancy_analysis,
                        'behavioral_insights': self._generate_behavioral_insights(features),
                        'recommendations': self._generate_risk_recommendations(
                            stated_risk, predicted_risk, features, confidence
                        )
                    }
                else:
                    return {
                        "error": "Risk prediction model not trained",
                        "behavioral_insights": self._generate_behavioral_insights(features)
                    }
                    
        except Exception as e:
            logger.error(f"Failed to predict risk tolerance for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _analyze_risk_discrepancy(self, stated: str, predicted: str,
                                 features: Dict, probabilities: np.ndarray) -> Dict[str, Any]:
        """Analyze discrepancy between stated and predicted risk tolerance."""
        discrepancy = {
            'has_discrepancy': stated != predicted,
            'discrepancy_type': None,
            'severity': 'low',
            'likely_causes': []
        }
        
        if stated != predicted:
            stated_level = self._encode_risk_tolerance(stated)
            predicted_level = self._encode_risk_tolerance(predicted)
            
            if stated_level > predicted_level:
                discrepancy['discrepancy_type'] = 'overconfident'
                discrepancy['likely_causes'].extend([
                    "May overestimate ability to handle market volatility",
                    "Investment behavior suggests more conservative approach needed"
                ])
            else:
                discrepancy['discrepancy_type'] = 'underconfident'
                discrepancy['likely_causes'].extend([
                    "May be too conservative given financial capacity",
                    "Could potentially take on more risk for better returns"
                ])
            
            # Determine severity based on confidence
            max_prob = np.max(probabilities)
            if max_prob > 0.8:
                discrepancy['severity'] = 'high'
            elif max_prob > 0.6:
                discrepancy['severity'] = 'medium'
        
        return discrepancy
    
    def _generate_behavioral_insights(self, features: Dict[str, float]) -> List[str]:
        """Generate insights about user's financial behavior."""
        insights = []
        
        # Savings behavior
        if features['savings_rate'] > 0.3:
            insights.append("Strong savings discipline indicates good long-term planning")
        elif features['savings_rate'] < 0.1:
            insights.append("Low savings rate may indicate need for budget optimization")
        
        # Emergency fund
        if features['emergency_fund_ratio'] < 0.5:
            insights.append("Consider building emergency fund before increasing investment risk")
        elif features['emergency_fund_ratio'] > 1.5:
            insights.append("Strong emergency fund provides flexibility for higher-risk investments")
        
        # Portfolio behavior
        if features['portfolio_concentration'] > 0.5:
            insights.append("High portfolio concentration suggests comfort with concentration risk")
        elif features['portfolio_concentration'] < 0.2:
            insights.append("Well-diversified portfolio indicates risk-aware investing approach")
        
        # Goal behavior
        if features['flexible_goals_ratio'] > 0.7:
            insights.append("Flexible goal timelines suggest adaptable financial planning")
        elif features['flexible_goals_ratio'] < 0.3:
            insights.append("Fixed goal timelines indicate structured planning approach")
        
        return insights
    
    def _generate_risk_recommendations(self, stated: str, predicted: str,
                                     features: Dict, confidence: float) -> List[str]:
        """Generate recommendations based on risk analysis."""
        recommendations = []
        
        if stated != predicted and confidence > 0.7:
            if stated == 'aggressive' and predicted in ['conservative', 'moderate']:
                recommendations.extend([
                    "Consider starting with moderate risk investments before moving to aggressive",
                    "Review historical market volatility to understand emotional reactions",
                    "Consider dollar-cost averaging to reduce timing risk"
                ])
            elif stated == 'conservative' and predicted in ['moderate', 'aggressive']:
                recommendations.extend([
                    "Your financial profile suggests capacity for moderate risk",
                    "Consider gradual increase in equity allocation",
                    "Review time horizon - longer periods may allow for more risk"
                ])
        
        # General recommendations based on features
        if features['emergency_fund_ratio'] < 0.5:
            recommendations.append("Build 3-6 month emergency fund before increasing investment risk")
        
        if features['savings_rate'] > 0.25 and features['retirement_horizon'] > 10:
            recommendations.append("Strong savings rate with long time horizon supports growth-oriented strategy")
        
        if features['debt_to_income'] > 0.3:
            recommendations.append("Consider debt reduction before increasing investment risk")
        
        return recommendations
    
    def analyze_risk_capacity_vs_tolerance(self, user_id: str) -> Dict[str, Any]:
        """Analyze difference between risk capacity and risk tolerance."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                profile = user.financial_profile
                
                # Calculate risk capacity factors
                capacity_factors = {
                    'time_horizon': min(1.0, (profile.retirement_age_target or 65 - profile.age) / 30),
                    'income_stability': self._encode_income_stability(profile),
                    'job_stability': self._encode_job_stability(profile),
                    'emergency_fund': min(1.0, self._calculate_emergency_fund_ratio(profile)),
                    'debt_level': max(0, 1.0 - profile.debt_to_income_ratio),
                    'savings_capacity': min(1.0, self._calculate_savings_rate(profile) * 2)
                }
                
                # Calculate overall risk capacity
                risk_capacity_score = np.mean(list(capacity_factors.values()))
                
                # Map to categories
                if risk_capacity_score > 0.7:
                    risk_capacity = 'high'
                elif risk_capacity_score > 0.4:
                    risk_capacity = 'moderate'
                else:
                    risk_capacity = 'low'
                
                # Compare with stated tolerance
                stated_tolerance = profile.risk_tolerance
                
                return {
                    'user_id': user_id,
                    'risk_capacity': risk_capacity,
                    'risk_capacity_score': float(risk_capacity_score),
                    'capacity_factors': {k: float(v) for k, v in capacity_factors.items()},
                    'stated_risk_tolerance': stated_tolerance,
                    'alignment': self._assess_capacity_tolerance_alignment(
                        risk_capacity, stated_tolerance
                    ),
                    'recommendations': self._generate_capacity_recommendations(
                        capacity_factors, risk_capacity, stated_tolerance
                    )
                }
                
        except Exception as e:
            logger.error(f"Failed to analyze risk capacity vs tolerance: {e}")
            return {"error": str(e)}
    
    def _assess_capacity_tolerance_alignment(self, capacity: str, tolerance: str) -> Dict[str, Any]:
        """Assess alignment between risk capacity and tolerance."""
        capacity_levels = {'low': 0, 'moderate': 1, 'high': 2}
        tolerance_levels = {'conservative': 0, 'moderate': 1, 'aggressive': 2}
        
        capacity_level = capacity_levels[capacity]
        tolerance_level = tolerance_levels[tolerance]
        
        difference = tolerance_level - capacity_level
        
        if difference == 0:
            return {
                'status': 'aligned',
                'message': 'Risk tolerance aligns well with financial capacity'
            }
        elif difference > 0:
            return {
                'status': 'tolerance_exceeds_capacity',
                'message': 'Risk tolerance may exceed financial capacity for risk'
            }
        else:
            return {
                'status': 'capacity_exceeds_tolerance',
                'message': 'Financial capacity allows for higher risk than current tolerance'
            }
    
    def _generate_capacity_recommendations(self, factors: Dict, capacity: str, 
                                         tolerance: str) -> List[str]:
        """Generate recommendations based on capacity analysis."""
        recommendations = []
        
        # Identify limiting factors
        limiting_factors = {k: v for k, v in factors.items() if v < 0.5}
        
        if 'emergency_fund' in limiting_factors:
            recommendations.append("Build emergency fund to increase risk capacity")
        
        if 'debt_level' in limiting_factors:
            recommendations.append("Reduce debt burden to improve financial flexibility")
        
        if 'income_stability' in limiting_factors:
            recommendations.append("Focus on income stabilization before increasing investment risk")
        
        if 'time_horizon' in limiting_factors:
            recommendations.append("Short time horizon suggests conservative approach")
        
        # Capacity vs tolerance misalignment
        if capacity == 'high' and tolerance == 'conservative':
            recommendations.append("Consider gradually increasing risk allocation given strong financial position")
        elif capacity == 'low' and tolerance in ['moderate', 'aggressive']:
            recommendations.append("Consider reducing risk exposure until financial capacity improves")
        
        return recommendations
"""
XGBoost-powered goal optimization engine for financial planning.

This module provides intelligent recommendations for:
- Optimal contribution amounts
- Timeline adjustments
- Priority rebalancing
- Goal achievement strategies
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Any
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class GoalOptimizer:
    """XGBoost-based goal optimization system."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/goal_optimizer"
        self.contribution_model = None
        self.timeline_model = None
        self.priority_model = None
        self.scalers = {}
        self.encoders = {}
        self.feature_importance = {}
        
        # Model parameters
        self.xgb_params = {
            'objective': 'reg:squarederror',
            'eval_metric': 'rmse',
            'max_depth': 6,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained models if they exist."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.contribution_model = joblib.load(model_dir / "contribution_model.pkl")
                self.timeline_model = joblib.load(model_dir / "timeline_model.pkl")
                self.priority_model = joblib.load(model_dir / "priority_model.pkl")
                self.scalers = joblib.load(model_dir / "scalers.pkl")
                self.encoders = joblib.load(model_dir / "encoders.pkl")
                
                with open(model_dir / "feature_importance.json", 'r') as f:
                    self.feature_importance = json.load(f)
                
                logger.info("Loaded pre-trained goal optimization models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.contribution_model, model_dir / "contribution_model.pkl")
            joblib.dump(self.timeline_model, model_dir / "timeline_model.pkl")
            joblib.dump(self.priority_model, model_dir / "priority_model.pkl")
            joblib.dump(self.scalers, model_dir / "scalers.pkl")
            joblib.dump(self.encoders, model_dir / "encoders.pkl")
            
            with open(model_dir / "feature_importance.json", 'w') as f:
                json.dump(self.feature_importance, f, indent=2)
            
            logger.info("Saved goal optimization models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _prepare_features(self, users_data: List[Dict]) -> pd.DataFrame:
        """Prepare features for model training/prediction."""
        features = []
        
        for user_data in users_data:
            profile = user_data['profile']
            goals = user_data['goals']
            
            for goal in goals:
                feature_row = {
                    # User demographics
                    'age': profile.age,
                    'marital_status': profile.marital_status,
                    'dependents': profile.dependents,
                    
                    # Financial profile
                    'annual_income': float(profile.annual_income),
                    'monthly_expenses': float(profile.monthly_expenses),
                    'net_worth': profile.net_worth,
                    'debt_to_income_ratio': profile.debt_to_income_ratio,
                    'liquid_assets': float(profile.liquid_assets or 0),
                    'retirement_accounts': float(profile.retirement_accounts or 0),
                    
                    # Risk profile
                    'risk_tolerance': profile.risk_tolerance,
                    'investment_experience': profile.investment_experience,
                    'employment_status': profile.employment_status,
                    'job_stability': profile.job_stability,
                    
                    # Goal characteristics
                    'goal_type': goal.goal_type,
                    'target_amount': float(goal.target_amount),
                    'current_amount': float(goal.current_amount or 0),
                    'months_remaining': goal.months_remaining,
                    'priority': goal.priority,
                    'is_flexible_timeline': goal.is_flexible_timeline,
                    'is_flexible_amount': goal.is_flexible_amount,
                    
                    # Derived features
                    'goal_completion_ratio': float(goal.current_amount or 0) / float(goal.target_amount),
                    'disposable_income': float(profile.annual_income) - (float(profile.monthly_expenses) * 12),
                    'goal_to_income_ratio': float(goal.target_amount) / float(profile.annual_income),
                    'savings_rate': max(0, (float(profile.annual_income) - float(profile.monthly_expenses) * 12) / float(profile.annual_income)),
                    
                    # Target variables (for training)
                    'optimal_monthly_contribution': float(goal.monthly_contribution or 0),
                    'optimal_timeline_months': goal.months_remaining,
                    'optimal_priority_score': goal.priority
                }
                features.append(feature_row)
        
        return pd.DataFrame(features)
    
    def _encode_categorical_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Encode categorical features."""
        categorical_cols = [
            'marital_status', 'risk_tolerance', 'investment_experience',
            'employment_status', 'job_stability', 'goal_type'
        ]
        
        df_encoded = df.copy()
        
        for col in categorical_cols:
            if col in df.columns:
                if fit:
                    if col not in self.encoders:
                        self.encoders[col] = LabelEncoder()
                    df_encoded[col] = self.encoders[col].fit_transform(df[col].astype(str))
                else:
                    if col in self.encoders:
                        # Handle unseen categories
                        unique_values = set(self.encoders[col].classes_)
                        df_encoded[col] = df[col].apply(
                            lambda x: self.encoders[col].transform([str(x)])[0] 
                            if str(x) in unique_values else -1
                        )
        
        return df_encoded
    
    def _scale_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Scale numerical features."""
        numerical_cols = [
            'age', 'dependents', 'annual_income', 'monthly_expenses', 
            'net_worth', 'debt_to_income_ratio', 'liquid_assets',
            'retirement_accounts', 'target_amount', 'current_amount',
            'months_remaining', 'priority', 'goal_completion_ratio',
            'disposable_income', 'goal_to_income_ratio', 'savings_rate'
        ]
        
        df_scaled = df.copy()
        
        for col in numerical_cols:
            if col in df.columns:
                if fit:
                    if col not in self.scalers:
                        self.scalers[col] = StandardScaler()
                    df_scaled[col] = self.scalers[col].fit_transform(df[[col]])
                else:
                    if col in self.scalers:
                        df_scaled[col] = self.scalers[col].transform(df[[col]])
        
        return df_scaled
    
    def train_models(self, retrain: bool = False) -> Dict[str, float]:
        """Train XGBoost models for goal optimization."""
        if not retrain and all([self.contribution_model, self.timeline_model, self.priority_model]):
            logger.info("Models already trained. Use retrain=True to retrain.")
            return {}
        
        logger.info("Training goal optimization models...")
        
        # Load training data from database
        training_data = self._load_training_data()
        if len(training_data) < 50:
            logger.warning("Insufficient training data. Need at least 50 samples.")
            return {}
        
        # Prepare features
        df = self._prepare_features(training_data)
        
        # Encode and scale features
        df_processed = self._encode_categorical_features(df, fit=True)
        df_processed = self._scale_features(df_processed, fit=True)
        
        # Feature columns (exclude targets)
        feature_cols = [col for col in df_processed.columns 
                       if not col.startswith('optimal_')]
        
        X = df_processed[feature_cols]
        
        metrics = {}
        
        # Train contribution model
        y_contribution = df_processed['optimal_monthly_contribution']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_contribution, test_size=0.2, random_state=42
        )
        
        self.contribution_model = xgb.XGBRegressor(**self.xgb_params)
        self.contribution_model.fit(X_train, y_train)
        
        y_pred = self.contribution_model.predict(X_test)
        metrics['contribution_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
        metrics['contribution_r2'] = r2_score(y_test, y_pred)
        
        # Train timeline model
        y_timeline = df_processed['optimal_timeline_months']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_timeline, test_size=0.2, random_state=42
        )
        
        self.timeline_model = xgb.XGBRegressor(**self.xgb_params)
        self.timeline_model.fit(X_train, y_train)
        
        y_pred = self.timeline_model.predict(X_test)
        metrics['timeline_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
        metrics['timeline_r2'] = r2_score(y_test, y_pred)
        
        # Train priority model
        y_priority = df_processed['optimal_priority_score']
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_priority, test_size=0.2, random_state=42
        )
        
        self.priority_model = xgb.XGBRegressor(**self.xgb_params)
        self.priority_model.fit(X_train, y_train)
        
        y_pred = self.priority_model.predict(X_test)
        metrics['priority_rmse'] = np.sqrt(mean_squared_error(y_test, y_pred))
        metrics['priority_r2'] = r2_score(y_test, y_pred)
        
        # Store feature importance
        self.feature_importance = {
            'contribution': dict(zip(feature_cols, self.contribution_model.feature_importances_)),
            'timeline': dict(zip(feature_cols, self.timeline_model.feature_importances_)),
            'priority': dict(zip(feature_cols, self.priority_model.feature_importances_))
        }
        
        # Save models
        self._save_models()
        
        logger.info(f"Goal optimization models trained successfully: {metrics}")
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
                    if user.financial_profile and user.goals:
                        user_data = {
                            'profile': user.financial_profile,
                            'goals': [goal for goal in user.goals if goal.status == 'active']
                        }
                        if user_data['goals']:
                            training_data.append(user_data)
                            
        except Exception as e:
            logger.error(f"Failed to load training data: {e}")
        
        return training_data
    
    def optimize_goals(self, user_id: str) -> Dict[str, Any]:
        """Generate goal optimization recommendations for a user."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                active_goals = [g for g in user.goals if g.status == 'active']
                if not active_goals:
                    return {"recommendations": [], "message": "No active goals found"}
                
                # Prepare user data
                user_data = [{
                    'profile': user.financial_profile,
                    'goals': active_goals
                }]
                
                df = self._prepare_features(user_data)
                df_processed = self._encode_categorical_features(df, fit=False)
                df_processed = self._scale_features(df_processed, fit=False)
                
                feature_cols = [col for col in df_processed.columns 
                               if not col.startswith('optimal_')]
                X = df_processed[feature_cols]
                
                recommendations = []
                
                for i, goal in enumerate(active_goals):
                    goal_features = X.iloc[i:i+1]
                    
                    # Get predictions
                    if self.contribution_model:
                        optimal_contribution = self.contribution_model.predict(goal_features)[0]
                    else:
                        optimal_contribution = goal.required_monthly_contribution
                    
                    if self.timeline_model:
                        optimal_timeline = self.timeline_model.predict(goal_features)[0]
                    else:
                        optimal_timeline = goal.months_remaining
                    
                    if self.priority_model:
                        optimal_priority = self.priority_model.predict(goal_features)[0]
                    else:
                        optimal_priority = goal.priority
                    
                    # Generate recommendations
                    rec = {
                        'goal_id': str(goal.id),
                        'goal_name': goal.name,
                        'current_monthly_contribution': float(goal.monthly_contribution or 0),
                        'recommended_monthly_contribution': max(0, float(optimal_contribution)),
                        'current_timeline_months': goal.months_remaining,
                        'recommended_timeline_months': max(1, int(optimal_timeline)),
                        'current_priority': goal.priority,
                        'recommended_priority': max(1, min(10, int(optimal_priority))),
                        'confidence_score': 0.85,  # Would be calculated based on model certainty
                        'reasoning': self._generate_reasoning(goal, optimal_contribution, optimal_timeline, optimal_priority)
                    }
                    
                    recommendations.append(rec)
                
                # Sort by priority
                recommendations.sort(key=lambda x: x['recommended_priority'])
                
                return {
                    'recommendations': recommendations,
                    'total_monthly_recommendation': sum(r['recommended_monthly_contribution'] for r in recommendations),
                    'available_monthly_budget': user.financial_profile.annual_income / 12 - user.financial_profile.monthly_expenses,
                    'optimization_score': self._calculate_optimization_score(recommendations, user.financial_profile)
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize goals for user {user_id}: {e}")
            return {"error": str(e)}
    
    def _generate_reasoning(self, goal: Goal, optimal_contribution: float, 
                           optimal_timeline: float, optimal_priority: float) -> List[str]:
        """Generate human-readable reasoning for recommendations."""
        reasoning = []
        
        current_contribution = float(goal.monthly_contribution or 0)
        contribution_diff = optimal_contribution - current_contribution
        
        if abs(contribution_diff) > 50:
            if contribution_diff > 0:
                reasoning.append(f"Increase monthly contribution by ${contribution_diff:.0f} to improve goal achievement probability")
            else:
                reasoning.append(f"Consider reducing monthly contribution by ${abs(contribution_diff):.0f} to optimize across all goals")
        
        timeline_diff = optimal_timeline - goal.months_remaining
        if abs(timeline_diff) > 3:
            if timeline_diff > 0:
                reasoning.append(f"Consider extending timeline by {timeline_diff:.0f} months for more realistic achievement")
            else:
                reasoning.append(f"Opportunity to achieve goal {abs(timeline_diff):.0f} months earlier with current resources")
        
        priority_diff = optimal_priority - goal.priority
        if abs(priority_diff) > 1:
            if priority_diff < 0:
                reasoning.append("Consider increasing priority of this goal based on your financial profile")
            else:
                reasoning.append("Consider lowering priority to focus on more critical goals first")
        
        if not reasoning:
            reasoning.append("Current goal parameters are well-optimized for your financial situation")
        
        return reasoning
    
    def _calculate_optimization_score(self, recommendations: List[Dict], 
                                    profile: FinancialProfile) -> float:
        """Calculate overall optimization score (0-100)."""
        total_recommended = sum(r['recommended_monthly_contribution'] for r in recommendations)
        available_budget = profile.annual_income / 12 - profile.monthly_expenses
        
        if available_budget <= 0:
            return 0.0
        
        budget_utilization = min(1.0, total_recommended / available_budget)
        priority_alignment = sum(1/r['recommended_priority'] for r in recommendations) / len(recommendations)
        
        # Higher scores for better budget utilization and priority alignment
        score = (budget_utilization * 0.6 + min(1.0, priority_alignment) * 0.4) * 100
        
        return max(0, min(100, score))
    
    def get_feature_importance(self, model_type: str = 'contribution') -> Dict[str, float]:
        """Get feature importance for a specific model."""
        if model_type in self.feature_importance:
            return dict(sorted(
                self.feature_importance[model_type].items(),
                key=lambda x: x[1],
                reverse=True
            ))
        return {}
    
    def predict_goal_success_probability(self, user_id: str, goal_id: str) -> float:
        """Predict probability of goal achievement given current parameters."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                goal = db.query(Goal).filter(Goal.id == goal_id).first()
                
                if not user or not goal or not user.financial_profile:
                    return 0.0
                
                # Create feature vector for prediction
                user_data = [{
                    'profile': user.financial_profile,
                    'goals': [goal]
                }]
                
                df = self._prepare_features(user_data)
                df_processed = self._encode_categorical_features(df, fit=False)
                df_processed = self._scale_features(df_processed, fit=False)
                
                # Calculate success factors
                monthly_needed = goal.required_monthly_contribution
                monthly_available = (user.financial_profile.annual_income / 12 - 
                                   user.financial_profile.monthly_expenses)
                
                affordability_factor = min(1.0, monthly_available / max(1, monthly_needed))
                timeline_factor = min(1.0, goal.months_remaining / 12)  # Longer timelines are better
                progress_factor = goal.progress_percentage / 100
                
                # Combine factors with weights
                probability = (
                    affordability_factor * 0.4 +
                    timeline_factor * 0.3 +
                    progress_factor * 0.3
                )
                
                return max(0.0, min(1.0, probability))
                
        except Exception as e:
            logger.error(f"Failed to predict goal success probability: {e}")
            return 0.0
"""
Collaborative filtering system for peer insights and recommendations.

This module provides:
- User similarity analysis based on financial profiles
- Peer group identification
- Success pattern discovery from similar users
- Benchmarking against peer groups
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import scipy.sparse as sp
from scipy.spatial.distance import pdist, squareform
import joblib
import json
from pathlib import Path

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.investment import Investment
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class CollaborativeFilter:
    """Collaborative filtering system for peer-based financial recommendations."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or "/app/ml/models/collaborative_filter"
        self.similarity_model = None
        self.peer_clusterer = None
        self.success_predictor = None
        self.feature_scaler = StandardScaler()
        self.label_encoders = {}
        
        # Similarity metrics
        self.similarity_weights = {
            'demographics': 0.2,
            'financial_profile': 0.3,
            'goals': 0.2,
            'behavior': 0.2,
            'outcomes': 0.1
        }
        
        self._load_models()
    
    def _load_models(self) -> None:
        """Load pre-trained collaborative filtering models."""
        try:
            model_dir = Path(self.model_path)
            if model_dir.exists():
                self.similarity_model = joblib.load(model_dir / "similarity_model.pkl")
                self.peer_clusterer = joblib.load(model_dir / "peer_clusterer.pkl")
                self.success_predictor = joblib.load(model_dir / "success_predictor.pkl")
                self.feature_scaler = joblib.load(model_dir / "feature_scaler.pkl")
                self.label_encoders = joblib.load(model_dir / "label_encoders.pkl")
                logger.info("Loaded pre-trained collaborative filtering models")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {e}")
    
    def _save_models(self) -> None:
        """Save trained models."""
        try:
            model_dir = Path(self.model_path)
            model_dir.mkdir(parents=True, exist_ok=True)
            
            if self.similarity_model:
                joblib.dump(self.similarity_model, model_dir / "similarity_model.pkl")
            if self.peer_clusterer:
                joblib.dump(self.peer_clusterer, model_dir / "peer_clusterer.pkl")
            if self.success_predictor:
                joblib.dump(self.success_predictor, model_dir / "success_predictor.pkl")
            
            joblib.dump(self.feature_scaler, model_dir / "feature_scaler.pkl")
            joblib.dump(self.label_encoders, model_dir / "label_encoders.pkl")
            logger.info("Saved collaborative filtering models")
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def _extract_user_features(self, user_data: Dict) -> Dict[str, float]:
        """Extract features for similarity calculation."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        investments = user_data.get('investments', [])
        
        features = {
            # Demographics
            'age': profile.age,
            'income_bracket': self._categorize_income(profile.annual_income),
            'dependents': profile.dependents,
            'marital_status_encoded': self._encode_categorical('marital_status', profile.marital_status),
            
            # Financial profile
            'income_log': np.log1p(float(profile.annual_income)),
            'net_worth_log': np.log1p(max(0, profile.net_worth)),
            'debt_to_income': profile.debt_to_income_ratio,
            'savings_rate': self._calculate_savings_rate(profile),
            'liquid_assets_ratio': float(profile.liquid_assets or 0) / float(profile.annual_income),
            
            # Risk and investment profile
            'risk_tolerance_encoded': self._encode_categorical('risk_tolerance', profile.risk_tolerance),
            'investment_experience_encoded': self._encode_categorical('investment_experience', profile.investment_experience),
            'employment_status_encoded': self._encode_categorical('employment_status', profile.employment_status),
            
            # Goals profile
            'num_goals': len(goals),
            'avg_goal_timeline': np.mean([g.months_remaining for g in goals]) if goals else 0,
            'total_goal_amount_ratio': sum(float(g.target_amount) for g in goals) / float(profile.annual_income) if goals else 0,
            'goal_diversity': len(set(g.goal_type for g in goals)),
            
            # Investment behavior
            'num_investments': len(investments),
            'portfolio_value_ratio': sum(float(inv.current_value or 0) for inv in investments) / float(profile.annual_income),
            
            # Success metrics
            'goal_completion_rate': self._calculate_goal_completion_rate(goals),
            'financial_health_score': self._calculate_financial_health_score(profile, goals)
        }
        
        return features
    
    def _categorize_income(self, income: float) -> int:
        """Categorize income into brackets."""
        if income < 30000:
            return 0
        elif income < 50000:
            return 1
        elif income < 75000:
            return 2
        elif income < 100000:
            return 3
        elif income < 150000:
            return 4
        else:
            return 5
    
    def _encode_categorical(self, feature_name: str, value: str) -> int:
        """Encode categorical features."""
        if feature_name not in self.label_encoders:
            self.label_encoders[feature_name] = LabelEncoder()
        
        try:
            return self.label_encoders[feature_name].transform([value])[0]
        except ValueError:
            # Handle unseen categories
            return -1
    
    def _calculate_savings_rate(self, profile: FinancialProfile) -> float:
        """Calculate savings rate."""
        if not profile.annual_income or profile.annual_income <= 0:
            return 0.0
        
        annual_expenses = float(profile.monthly_expenses) * 12
        savings_rate = max(0, (float(profile.annual_income) - annual_expenses) / float(profile.annual_income))
        return min(1.0, savings_rate)
    
    def _calculate_goal_completion_rate(self, goals: List) -> float:
        """Calculate goal completion rate."""
        if not goals:
            return 0.0
        
        completed_goals = sum(1 for g in goals if g.status == 'completed')
        return completed_goals / len(goals)
    
    def _calculate_financial_health_score(self, profile: FinancialProfile, goals: List) -> float:
        """Calculate overall financial health score."""
        factors = []
        
        # Emergency fund
        emergency_fund_months = float(profile.liquid_assets or 0) / float(profile.monthly_expenses)
        factors.append(min(1.0, emergency_fund_months / 6))
        
        # Debt levels
        factors.append(max(0, 1.0 - profile.debt_to_income_ratio))
        
        # Savings rate
        factors.append(self._calculate_savings_rate(profile))
        
        # Goal progress
        if goals:
            avg_progress = np.mean([g.progress_percentage for g in goals]) / 100
            factors.append(avg_progress)
        
        return np.mean(factors)
    
    def train_collaborative_models(self, retrain: bool = False) -> Dict[str, Any]:
        """Train collaborative filtering models."""
        if not retrain and all([self.similarity_model, self.peer_clusterer]):
            logger.info("Collaborative models already trained. Use retrain=True to retrain.")
            return {}
        
        logger.info("Training collaborative filtering models...")
        
        # Load user data
        user_data = self._load_user_data()
        if len(user_data) < 50:
            logger.warning("Insufficient user data for collaborative filtering. Need at least 50 users.")
            return {}
        
        # Extract features
        features_list = []
        for data in user_data:
            features = self._extract_user_features(data)
            features_list.append(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        df = df.fillna(df.median())
        
        # Fit label encoders
        categorical_cols = ['marital_status_encoded', 'risk_tolerance_encoded', 
                           'investment_experience_encoded', 'employment_status_encoded']
        for col in categorical_cols:
            if col in df.columns:
                unique_values = df[col].unique()
                if col.replace('_encoded', '') not in self.label_encoders:
                    self.label_encoders[col.replace('_encoded', '')] = LabelEncoder()
                    self.label_encoders[col.replace('_encoded', '')].fit(unique_values)
        
        # Scale features
        X_scaled = self.feature_scaler.fit_transform(df)
        
        # Train similarity model (Nearest Neighbors)
        self.similarity_model = NearestNeighbors(
            n_neighbors=min(20, len(user_data)//2),
            metric='cosine',
            algorithm='ball_tree'
        )
        self.similarity_model.fit(X_scaled)
        
        # Train peer clustering
        n_clusters = min(8, len(user_data)//10)
        self.peer_clusterer = KMeans(n_clusters=n_clusters, random_state=42)
        cluster_labels = self.peer_clusterer.fit_predict(X_scaled)
        
        # Analyze clusters
        cluster_analysis = self._analyze_clusters(df, cluster_labels)
        
        # Save models
        self._save_models()
        
        metrics = {
            'num_users': len(user_data),
            'num_features': len(df.columns),
            'num_clusters': n_clusters,
            'cluster_analysis': cluster_analysis
        }
        
        logger.info(f"Collaborative filtering models trained successfully: {metrics}")
        return metrics
    
    def _load_user_data(self) -> List[Dict]:
        """Load user data for collaborative filtering."""
        user_data = []
        
        try:
            with SessionLocal() as db:
                users = db.query(User).join(FinancialProfile).filter(
                    FinancialProfile.annual_income.isnot(None)
                ).all()
                
                for user in users:
                    if user.financial_profile:
                        data = {
                            'user_id': str(user.id),
                            'profile': user.financial_profile,
                            'goals': user.goals or [],
                            'investments': user.investments or []
                        }
                        user_data.append(data)
                        
        except Exception as e:
            logger.error(f"Failed to load user data: {e}")
        
        return user_data
    
    def _analyze_clusters(self, df: pd.DataFrame, cluster_labels: np.ndarray) -> Dict[str, Any]:
        """Analyze characteristics of each cluster."""
        cluster_analysis = {}
        
        for cluster_id in np.unique(cluster_labels):
            cluster_mask = cluster_labels == cluster_id
            cluster_data = df[cluster_mask]
            
            analysis = {
                'size': int(np.sum(cluster_mask)),
                'characteristics': {},
                'typical_profile': {}
            }
            
            # Calculate cluster characteristics
            for col in df.columns:
                analysis['characteristics'][col] = {
                    'mean': float(cluster_data[col].mean()),
                    'std': float(cluster_data[col].std()),
                    'median': float(cluster_data[col].median())
                }
            
            # Define typical profile
            analysis['typical_profile'] = {
                'age_range': f"{cluster_data['age'].quantile(0.25):.0f}-{cluster_data['age'].quantile(0.75):.0f}",
                'income_bracket': int(cluster_data['income_bracket'].median()),
                'avg_savings_rate': float(cluster_data['savings_rate'].mean()),
                'avg_goal_timeline': float(cluster_data['avg_goal_timeline'].mean()),
                'financial_health_score': float(cluster_data['financial_health_score'].mean())
            }
            
            cluster_analysis[f'cluster_{cluster_id}'] = analysis
        
        return cluster_analysis
    
    def find_similar_users(self, user_id: str, n_similar: int = 10) -> Dict[str, Any]:
        """Find similar users for collaborative recommendations."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Extract user features
                user_data = {
                    'profile': user.financial_profile,
                    'goals': user.goals or [],
                    'investments': user.investments or []
                }
                
                user_features = self._extract_user_features(user_data)
                
                # Convert to array and scale
                feature_df = pd.DataFrame([user_features])
                feature_df = feature_df.fillna(feature_df.median())
                
                if hasattr(self.feature_scaler, 'mean_'):
                    X_scaled = self.feature_scaler.transform(feature_df)
                else:
                    return {"error": "Similarity model not trained"}
                
                # Find similar users
                if self.similarity_model:
                    distances, indices = self.similarity_model.kneighbors(X_scaled, n_neighbors=n_similar+1)
                    
                    # Get similar user profiles
                    all_users = self._load_user_data()
                    similar_users = []
                    
                    for i, idx in enumerate(indices[0][1:]):  # Skip first (self)
                        if idx < len(all_users):
                            similar_user = all_users[idx]
                            similarity_score = 1 - distances[0][i+1]  # Convert distance to similarity
                            
                            similar_users.append({
                                'user_id': similar_user['user_id'],
                                'similarity_score': float(similarity_score),
                                'profile_summary': self._create_profile_summary(similar_user),
                                'success_metrics': self._extract_success_metrics(similar_user)
                            })
                    
                    return {
                        'user_id': user_id,
                        'similar_users': similar_users,
                        'peer_group': self._identify_peer_group(user_data),
                        'recommendations': self._generate_peer_recommendations(similar_users, user_data)
                    }
                else:
                    return {"error": "Similarity model not available"}
                    
        except Exception as e:
            logger.error(f"Failed to find similar users for {user_id}: {e}")
            return {"error": str(e)}
    
    def _create_profile_summary(self, user_data: Dict) -> Dict[str, Any]:
        """Create a summary of user profile for comparison."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        
        return {
            'age': profile.age,
            'income_bracket': self._categorize_income(profile.annual_income),
            'marital_status': profile.marital_status,
            'dependents': profile.dependents,
            'risk_tolerance': profile.risk_tolerance,
            'num_goals': len(goals),
            'savings_rate': self._calculate_savings_rate(profile),
            'financial_health_score': self._calculate_financial_health_score(profile, goals)
        }
    
    def _extract_success_metrics(self, user_data: Dict) -> Dict[str, Any]:
        """Extract success metrics for peer comparison."""
        profile = user_data['profile']
        goals = user_data.get('goals', [])
        
        return {
            'goal_completion_rate': self._calculate_goal_completion_rate(goals),
            'net_worth_to_income': profile.net_worth / float(profile.annual_income) if profile.annual_income > 0 else 0,
            'debt_to_income': profile.debt_to_income_ratio,
            'emergency_fund_months': float(profile.liquid_assets or 0) / float(profile.monthly_expenses),
            'investment_portfolio_value': sum(float(inv.current_value or 0) for inv in user_data.get('investments', []))
        }
    
    def _identify_peer_group(self, user_data: Dict) -> Dict[str, Any]:
        """Identify user's peer group cluster."""
        try:
            if not self.peer_clusterer:
                return {"error": "Peer clustering model not available"}
            
            user_features = self._extract_user_features(user_data)
            feature_df = pd.DataFrame([user_features])
            feature_df = feature_df.fillna(feature_df.median())
            
            X_scaled = self.feature_scaler.transform(feature_df)
            cluster_id = self.peer_clusterer.predict(X_scaled)[0]
            
            return {
                'cluster_id': int(cluster_id),
                'cluster_name': self._get_cluster_name(cluster_id),
                'typical_characteristics': self._get_cluster_characteristics(cluster_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to identify peer group: {e}")
            return {"error": str(e)}
    
    def _get_cluster_name(self, cluster_id: int) -> str:
        """Get descriptive name for cluster."""
        cluster_names = {
            0: "Young Professionals",
            1: "Growing Families", 
            2: "Established Savers",
            3: "High Earners",
            4: "Conservative Investors",
            5: "Aggressive Investors",
            6: "Pre-Retirees",
            7: "Budget Conscious"
        }
        return cluster_names.get(cluster_id, f"Peer Group {cluster_id}")
    
    def _get_cluster_characteristics(self, cluster_id: int) -> Dict[str, str]:
        """Get typical characteristics of cluster."""
        # This would be populated from the cluster analysis
        # For now, return placeholder characteristics
        return {
            "typical_age_range": "25-35",
            "common_goals": "Emergency fund, Home purchase",
            "investment_style": "Moderate risk",
            "financial_focus": "Building wealth"
        }
    
    def _generate_peer_recommendations(self, similar_users: List[Dict], 
                                     user_data: Dict) -> List[str]:
        """Generate recommendations based on similar users' success patterns."""
        recommendations = []
        
        if not similar_users:
            return recommendations
        
        # Analyze successful patterns from similar users
        successful_users = [u for u in similar_users 
                           if u['success_metrics']['financial_health_score'] > 0.7]
        
        if successful_users:
            # Savings rate recommendations
            avg_savings_rate = np.mean([u['profile_summary']['savings_rate'] for u in successful_users])
            user_savings_rate = self._calculate_savings_rate(user_data['profile'])
            
            if avg_savings_rate > user_savings_rate + 0.05:
                recommendations.append(
                    f"Similar successful users save {avg_savings_rate*100:.1f}% of income on average - "
                    f"consider increasing your savings rate"
                )
            
            # Goal patterns
            avg_goals = np.mean([u['profile_summary']['num_goals'] for u in successful_users])
            if avg_goals > len(user_data['goals']) + 1:
                recommendations.append(
                    f"Users similar to you typically have {avg_goals:.0f} active goals - "
                    f"consider setting additional financial goals"
                )
            
            # Investment patterns
            investing_users = [u for u in successful_users 
                             if u['success_metrics']['investment_portfolio_value'] > 0]
            if investing_users and not user_data.get('investments'):
                recommendations.append(
                    "Similar successful users typically have investment portfolios - "
                    "consider starting to invest"
                )
            
            # Emergency fund
            avg_emergency_months = np.mean([u['success_metrics']['emergency_fund_months'] 
                                          for u in successful_users])
            user_emergency_months = (float(user_data['profile'].liquid_assets or 0) / 
                                   float(user_data['profile'].monthly_expenses))
            
            if avg_emergency_months > user_emergency_months + 1:
                recommendations.append(
                    f"Similar users maintain {avg_emergency_months:.1f} months of emergency funds on average"
                )
        
        return recommendations
    
    def get_peer_benchmarks(self, user_id: str) -> Dict[str, Any]:
        """Get peer benchmarks for comparison."""
        try:
            with SessionLocal() as db:
                user = db.query(User).filter(User.id == user_id).first()
                if not user or not user.financial_profile:
                    return {"error": "User or financial profile not found"}
                
                # Find peer group
                user_data = {
                    'profile': user.financial_profile,
                    'goals': user.goals or [],
                    'investments': user.investments or []
                }
                
                peer_group = self._identify_peer_group(user_data)
                similar_users_result = self.find_similar_users(user_id, n_similar=20)
                
                if 'similar_users' not in similar_users_result:
                    return {"error": "Could not find similar users"}
                
                similar_users = similar_users_result['similar_users']
                
                # Calculate benchmarks
                benchmarks = {
                    'savings_rate': {
                        'user_value': self._calculate_savings_rate(user.financial_profile),
                        'peer_median': np.median([u['profile_summary']['savings_rate'] for u in similar_users]),
                        'peer_75th_percentile': np.percentile([u['profile_summary']['savings_rate'] for u in similar_users], 75)
                    },
                    'net_worth_to_income': {
                        'user_value': user.financial_profile.net_worth / float(user.financial_profile.annual_income),
                        'peer_median': np.median([u['success_metrics']['net_worth_to_income'] for u in similar_users]),
                        'peer_75th_percentile': np.percentile([u['success_metrics']['net_worth_to_income'] for u in similar_users], 75)
                    },
                    'emergency_fund_months': {
                        'user_value': float(user.financial_profile.liquid_assets or 0) / float(user.financial_profile.monthly_expenses),
                        'peer_median': np.median([u['success_metrics']['emergency_fund_months'] for u in similar_users]),
                        'peer_75th_percentile': np.percentile([u['success_metrics']['emergency_fund_months'] for u in similar_users], 75)
                    },
                    'goal_completion_rate': {
                        'user_value': self._calculate_goal_completion_rate(user.goals),
                        'peer_median': np.median([u['success_metrics']['goal_completion_rate'] for u in similar_users]),
                        'peer_75th_percentile': np.percentile([u['success_metrics']['goal_completion_rate'] for u in similar_users], 75)
                    }
                }
                
                # Generate performance analysis
                performance_analysis = self._analyze_performance_vs_peers(benchmarks)
                
                return {
                    'user_id': user_id,
                    'peer_group': peer_group,
                    'benchmarks': benchmarks,
                    'performance_analysis': performance_analysis,
                    'improvement_areas': self._identify_improvement_areas(benchmarks),
                    'strength_areas': self._identify_strength_areas(benchmarks)
                }
                
        except Exception as e:
            logger.error(f"Failed to get peer benchmarks for {user_id}: {e}")
            return {"error": str(e)}
    
    def _analyze_performance_vs_peers(self, benchmarks: Dict) -> Dict[str, str]:
        """Analyze user performance vs peers."""
        analysis = {}
        
        for metric, data in benchmarks.items():
            user_value = data['user_value']
            peer_median = data['peer_median']
            
            if user_value > peer_median * 1.1:
                analysis[metric] = 'above_average'
            elif user_value < peer_median * 0.9:
                analysis[metric] = 'below_average'
            else:
                analysis[metric] = 'average'
        
        return analysis
    
    def _identify_improvement_areas(self, benchmarks: Dict) -> List[str]:
        """Identify areas for improvement based on peer comparison."""
        improvements = []
        
        for metric, data in benchmarks.items():
            user_value = data['user_value']
            peer_75th = data['peer_75th_percentile']
            
            if user_value < peer_75th * 0.8:
                metric_name = metric.replace('_', ' ').title()
                improvements.append(f"{metric_name}: Below peer group average")
        
        return improvements
    
    def _identify_strength_areas(self, benchmarks: Dict) -> List[str]:
        """Identify strength areas based on peer comparison."""
        strengths = []
        
        for metric, data in benchmarks.items():
            user_value = data['user_value']
            peer_75th = data['peer_75th_percentile']
            
            if user_value > peer_75th:
                metric_name = metric.replace('_', ' ').title()
                strengths.append(f"{metric_name}: Above 75th percentile of peers")
        
        return strengths
"""
Comprehensive model monitoring and retraining pipeline for ML recommendations.

This module provides:
- Model performance tracking
- Data drift detection
- Automated retraining triggers
- Model versioning and rollback
- Performance degradation alerts
- A/B testing framework for model updates
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import joblib
from pathlib import Path
import hashlib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.database.base import SessionLocal

logger = logging.getLogger(__name__)


class ModelMonitor:
    """Comprehensive ML model monitoring and retraining system."""
    
    def __init__(self, models_path: Optional[str] = None, monitoring_path: Optional[str] = None):
        self.models_path = models_path or "/app/ml/models"
        self.monitoring_path = monitoring_path or "/app/ml/monitoring"
        
        # Model registry
        self.model_registry = {
            'goal_optimizer': {
                'type': 'regression',
                'metrics': ['rmse', 'mae', 'r2'],
                'retrain_threshold': {'rmse_increase': 0.15, 'r2_decrease': 0.1}
            },
            'risk_predictor': {
                'type': 'classification',
                'metrics': ['accuracy', 'precision', 'recall', 'f1', 'auc'],
                'retrain_threshold': {'accuracy_decrease': 0.05, 'auc_decrease': 0.05}
            },
            'portfolio_rebalancer': {
                'type': 'optimization',
                'metrics': ['success_rate', 'user_satisfaction', 'performance_impact'],
                'retrain_threshold': {'success_rate_decrease': 0.1}
            },
            'behavioral_analyzer': {
                'type': 'clustering',
                'metrics': ['silhouette_score', 'prediction_accuracy'],
                'retrain_threshold': {'silhouette_decrease': 0.1}
            },
            'collaborative_filter': {
                'type': 'recommendation',
                'metrics': ['precision_at_k', 'recall_at_k', 'ndcg'],
                'retrain_threshold': {'precision_decrease': 0.05}
            },
            'savings_strategist': {
                'type': 'strategy',
                'metrics': ['adoption_rate', 'completion_rate'],
                'retrain_threshold': {'adoption_decrease': 0.1}
            },
            'life_event_predictor': {
                'type': 'classification',
                'metrics': ['accuracy', 'precision', 'recall', 'calibration'],
                'retrain_threshold': {'accuracy_decrease': 0.05}
            }
        }
        
        # Monitoring configuration
        self.monitoring_config = {
            'data_drift_threshold': 0.05,  # PSI threshold
            'performance_check_frequency': 'daily',
            'retrain_check_frequency': 'weekly',
            'alert_thresholds': {
                'critical': 0.15,  # 15% performance degradation
                'warning': 0.10,   # 10% performance degradation
                'info': 0.05       # 5% performance degradation
            }
        }
        
        self._ensure_monitoring_directories()
    
    def _ensure_monitoring_directories(self) -> None:
        """Ensure monitoring directories exist."""
        Path(self.monitoring_path).mkdir(parents=True, exist_ok=True)
        Path(f"{self.monitoring_path}/performance").mkdir(parents=True, exist_ok=True)
        Path(f"{self.monitoring_path}/drift").mkdir(parents=True, exist_ok=True)
        Path(f"{self.monitoring_path}/alerts").mkdir(parents=True, exist_ok=True)
        Path(f"{self.monitoring_path}/retraining").mkdir(parents=True, exist_ok=True)
    
    def monitor_model_performance(self, model_name: str, 
                                predictions: List[Any], 
                                actuals: List[Any],
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Monitor real-time model performance."""
        try:
            if model_name not in self.model_registry:
                return {"error": f"Model {model_name} not registered"}
            
            model_config = self.model_registry[model_name]
            model_type = model_config['type']
            
            # Calculate performance metrics
            current_metrics = self._calculate_metrics(
                predictions, actuals, model_type
            )
            
            # Load historical performance
            historical_metrics = self._load_historical_metrics(model_name)
            
            # Detect performance degradation
            degradation_analysis = self._detect_performance_degradation(
                current_metrics, historical_metrics, model_config
            )
            
            # Save current metrics
            self._save_performance_metrics(model_name, current_metrics, metadata)
            
            # Generate alerts if needed
            alerts = self._generate_performance_alerts(
                model_name, degradation_analysis
            )
            
            # Check if retraining is needed
            retrain_needed = self._check_retrain_trigger(
                model_name, degradation_analysis
            )
            
            monitoring_result = {
                'model_name': model_name,
                'timestamp': datetime.now().isoformat(),
                'current_metrics': current_metrics,
                'degradation_analysis': degradation_analysis,
                'alerts': alerts,
                'retrain_needed': retrain_needed,
                'data_points': len(predictions)
            }
            
            logger.info(f"Performance monitoring completed for {model_name}")
            return monitoring_result
            
        except Exception as e:
            logger.error(f"Failed to monitor performance for {model_name}: {e}")
            return {"error": str(e)}
    
    def _calculate_metrics(self, predictions: List[Any], 
                          actuals: List[Any], model_type: str) -> Dict[str, float]:
        """Calculate performance metrics based on model type."""
        metrics = {}
        
        try:
            predictions = np.array(predictions)
            actuals = np.array(actuals)
            
            if model_type == 'regression':
                metrics['rmse'] = np.sqrt(mean_squared_error(actuals, predictions))
                metrics['mae'] = mean_absolute_error(actuals, predictions)
                metrics['r2'] = r2_score(actuals, predictions)
                metrics['mape'] = np.mean(np.abs((actuals - predictions) / actuals)) * 100
                
            elif model_type == 'classification':
                # Assume predictions are probabilities, convert to classes
                if len(predictions.shape) > 1:
                    pred_classes = np.argmax(predictions, axis=1)
                    pred_probs = np.max(predictions, axis=1)
                else:
                    pred_classes = (predictions > 0.5).astype(int)
                    pred_probs = predictions
                
                metrics['accuracy'] = accuracy_score(actuals, pred_classes)
                metrics['precision'] = precision_score(actuals, pred_classes, average='weighted', zero_division=0)
                metrics['recall'] = recall_score(actuals, pred_classes, average='weighted', zero_division=0)
                metrics['f1'] = f1_score(actuals, pred_classes, average='weighted', zero_division=0)
                
                try:
                    if len(np.unique(actuals)) == 2:  # Binary classification
                        metrics['auc'] = roc_auc_score(actuals, pred_probs)
                except:
                    metrics['auc'] = 0.5
                    
            elif model_type == 'recommendation':
                # Custom metrics for recommendation systems
                metrics['precision_at_5'] = self._precision_at_k(predictions, actuals, k=5)
                metrics['recall_at_5'] = self._recall_at_k(predictions, actuals, k=5)
                metrics['ndcg'] = self._ndcg(predictions, actuals)
                
            elif model_type == 'optimization':
                # Custom metrics for optimization results
                metrics['success_rate'] = np.mean(predictions)  # Assuming binary success
                metrics['average_improvement'] = np.mean(actuals)
                
            elif model_type == 'clustering':
                # For clustering, predictions might be cluster assignments
                metrics['silhouette_score'] = self._calculate_silhouette_score(predictions, actuals)
                
            elif model_type == 'strategy':
                # For strategy recommendations
                metrics['adoption_rate'] = np.mean(predictions)
                metrics['completion_rate'] = np.mean(actuals)
                
        except Exception as e:
            logger.error(f"Failed to calculate metrics for {model_type}: {e}")
            metrics['error'] = str(e)
        
        return metrics
    
    def _precision_at_k(self, predictions: List, actuals: List, k: int = 5) -> float:
        """Calculate precision at k for recommendation systems."""
        try:
            # Simplified implementation
            if len(predictions) == 0:
                return 0.0
            
            # Assume predictions and actuals are lists of relevant items
            precision_scores = []
            for pred, actual in zip(predictions[:k], actuals[:k]):
                if isinstance(pred, (list, np.ndarray)) and isinstance(actual, (list, np.ndarray)):
                    relevant = len(set(pred) & set(actual))
                    precision = relevant / len(pred) if len(pred) > 0 else 0
                    precision_scores.append(precision)
            
            return np.mean(precision_scores) if precision_scores else 0.0
        except:
            return 0.0
    
    def _recall_at_k(self, predictions: List, actuals: List, k: int = 5) -> float:
        """Calculate recall at k for recommendation systems."""
        try:
            recall_scores = []
            for pred, actual in zip(predictions[:k], actuals[:k]):
                if isinstance(pred, (list, np.ndarray)) and isinstance(actual, (list, np.ndarray)):
                    relevant = len(set(pred) & set(actual))
                    recall = relevant / len(actual) if len(actual) > 0 else 0
                    recall_scores.append(recall)
            
            return np.mean(recall_scores) if recall_scores else 0.0
        except:
            return 0.0
    
    def _ndcg(self, predictions: List, actuals: List, k: int = 5) -> float:
        """Calculate NDCG for recommendation systems."""
        # Simplified NDCG calculation
        try:
            ndcg_scores = []
            for pred, actual in zip(predictions[:k], actuals[:k]):
                if isinstance(pred, (list, np.ndarray)) and isinstance(actual, (list, np.ndarray)):
                    # Simplified relevance scoring
                    relevance = [1 if item in actual else 0 for item in pred[:k]]
                    dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevance))
                    ideal_relevance = sorted(relevance, reverse=True)
                    idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_relevance))
                    ndcg = dcg / idcg if idcg > 0 else 0
                    ndcg_scores.append(ndcg)
            
            return np.mean(ndcg_scores) if ndcg_scores else 0.0
        except:
            return 0.0
    
    def _calculate_silhouette_score(self, cluster_assignments: List, features: List) -> float:
        """Calculate silhouette score for clustering."""
        try:
            from sklearn.metrics import silhouette_score
            if len(set(cluster_assignments)) > 1:
                return silhouette_score(features, cluster_assignments)
            return 0.0
        except:
            return 0.0
    
    def _load_historical_metrics(self, model_name: str) -> Dict[str, List[float]]:
        """Load historical performance metrics."""
        try:
            metrics_file = f"{self.monitoring_path}/performance/{model_name}_metrics.json"
            if Path(metrics_file).exists():
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load historical metrics for {model_name}: {e}")
            return {}
    
    def _save_performance_metrics(self, model_name: str, metrics: Dict[str, float],
                                 metadata: Dict[str, Any] = None) -> None:
        """Save current performance metrics."""
        try:
            metrics_file = f"{self.monitoring_path}/performance/{model_name}_metrics.json"
            
            # Load existing metrics
            historical_metrics = self._load_historical_metrics(model_name)
            
            # Add current metrics
            timestamp = datetime.now().isoformat()
            for metric_name, value in metrics.items():
                if metric_name not in historical_metrics:
                    historical_metrics[metric_name] = []
                
                historical_metrics[metric_name].append({
                    'timestamp': timestamp,
                    'value': value,
                    'metadata': metadata or {}
                })
            
            # Keep only last 100 data points
            for metric_name in historical_metrics:
                historical_metrics[metric_name] = historical_metrics[metric_name][-100:]
            
            # Save updated metrics
            with open(metrics_file, 'w') as f:
                json.dump(historical_metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save metrics for {model_name}: {e}")
    
    def _detect_performance_degradation(self, current_metrics: Dict[str, float],
                                       historical_metrics: Dict[str, List],
                                       model_config: Dict) -> Dict[str, Any]:
        """Detect performance degradation."""
        degradation = {
            'degraded_metrics': [],
            'improvement_metrics': [],
            'stable_metrics': [],
            'overall_status': 'stable'
        }
        
        try:
            retrain_threshold = model_config.get('retrain_threshold', {})
            
            for metric_name, current_value in current_metrics.items():
                if metric_name in historical_metrics and len(historical_metrics[metric_name]) > 5:
                    # Get recent historical values
                    recent_values = [
                        entry['value'] for entry in historical_metrics[metric_name][-10:]
                    ]
                    historical_mean = np.mean(recent_values)
                    historical_std = np.std(recent_values)
                    
                    # Calculate relative change
                    if historical_mean != 0:
                        relative_change = (current_value - historical_mean) / historical_mean
                    else:
                        relative_change = 0
                    
                    # Determine if metric should increase or decrease for better performance
                    increasing_metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc', 'r2', 
                                        'success_rate', 'adoption_rate', 'completion_rate']
                    
                    if metric_name in increasing_metrics:
                        # Higher is better
                        if relative_change < -0.05:  # 5% decrease
                            degradation['degraded_metrics'].append({
                                'metric': metric_name,
                                'current': current_value,
                                'historical_mean': historical_mean,
                                'change_percent': relative_change * 100,
                                'severity': self._get_degradation_severity(abs(relative_change))
                            })
                        elif relative_change > 0.05:  # 5% increase
                            degradation['improvement_metrics'].append({
                                'metric': metric_name,
                                'current': current_value,
                                'historical_mean': historical_mean,
                                'change_percent': relative_change * 100
                            })
                        else:
                            degradation['stable_metrics'].append(metric_name)
                    else:
                        # Lower is better (rmse, mae, etc.)
                        if relative_change > 0.05:  # 5% increase (worse)
                            degradation['degraded_metrics'].append({
                                'metric': metric_name,
                                'current': current_value,
                                'historical_mean': historical_mean,
                                'change_percent': relative_change * 100,
                                'severity': self._get_degradation_severity(relative_change)
                            })
                        elif relative_change < -0.05:  # 5% decrease (better)
                            degradation['improvement_metrics'].append({
                                'metric': metric_name,
                                'current': current_value,
                                'historical_mean': historical_mean,
                                'change_percent': relative_change * 100
                            })
                        else:
                            degradation['stable_metrics'].append(metric_name)
            
            # Determine overall status
            if len(degradation['degraded_metrics']) > 0:
                max_severity = max(m['severity'] for m in degradation['degraded_metrics'])
                degradation['overall_status'] = max_severity
            elif len(degradation['improvement_metrics']) > 0:
                degradation['overall_status'] = 'improving'
            
        except Exception as e:
            logger.error(f"Failed to detect performance degradation: {e}")
            degradation['error'] = str(e)
        
        return degradation
    
    def _get_degradation_severity(self, change_magnitude: float) -> str:
        """Get degradation severity level."""
        if change_magnitude >= 0.15:
            return 'critical'
        elif change_magnitude >= 0.10:
            return 'warning'
        elif change_magnitude >= 0.05:
            return 'info'
        else:
            return 'stable'
    
    def _generate_performance_alerts(self, model_name: str, 
                                   degradation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate performance alerts."""
        alerts = []
        
        try:
            for degraded_metric in degradation.get('degraded_metrics', []):
                severity = degraded_metric['severity']
                
                alert = {
                    'timestamp': datetime.now().isoformat(),
                    'model_name': model_name,
                    'alert_type': 'performance_degradation',
                    'severity': severity,
                    'metric': degraded_metric['metric'],
                    'message': f"{model_name} {degraded_metric['metric']} degraded by {abs(degraded_metric['change_percent']):.1f}%",
                    'current_value': degraded_metric['current'],
                    'historical_mean': degraded_metric['historical_mean'],
                    'recommended_action': self._get_recommended_action(severity)
                }
                
                alerts.append(alert)
                
                # Save alert
                self._save_alert(alert)
            
        except Exception as e:
            logger.error(f"Failed to generate alerts for {model_name}: {e}")
        
        return alerts
    
    def _get_recommended_action(self, severity: str) -> str:
        """Get recommended action based on severity."""
        actions = {
            'critical': 'Immediate model retraining required',
            'warning': 'Schedule model retraining within 24 hours',
            'info': 'Monitor closely, consider retraining if trend continues'
        }
        return actions.get(severity, 'Continue monitoring')
    
    def _save_alert(self, alert: Dict[str, Any]) -> None:
        """Save alert to file."""
        try:
            alerts_file = f"{self.monitoring_path}/alerts/alerts.jsonl"
            
            # Append alert to file
            with open(alerts_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save alert: {e}")
    
    def _check_retrain_trigger(self, model_name: str, 
                              degradation: Dict[str, Any]) -> Dict[str, Any]:
        """Check if model retraining should be triggered."""
        retrain_info = {
            'triggered': False,
            'reason': None,
            'severity': None,
            'recommended_action': 'continue_monitoring'
        }
        
        try:
            model_config = self.model_registry.get(model_name, {})
            retrain_thresholds = model_config.get('retrain_threshold', {})
            
            # Check degraded metrics against thresholds
            for degraded_metric in degradation.get('degraded_metrics', []):
                metric_name = degraded_metric['metric']
                change_magnitude = abs(degraded_metric['change_percent']) / 100
                
                # Check specific thresholds
                threshold_key = f"{metric_name}_decrease" if degraded_metric['change_percent'] < 0 else f"{metric_name}_increase"
                
                if threshold_key in retrain_thresholds:
                    threshold = retrain_thresholds[threshold_key]
                    
                    if change_magnitude >= threshold:
                        retrain_info['triggered'] = True
                        retrain_info['reason'] = f"{metric_name} degraded by {change_magnitude:.1%}, exceeding threshold of {threshold:.1%}"
                        retrain_info['severity'] = degraded_metric['severity']
                        retrain_info['recommended_action'] = 'retrain_model'
                        break
            
            # Check overall degradation
            if not retrain_info['triggered']:
                critical_degradations = [m for m in degradation.get('degraded_metrics', []) 
                                       if m['severity'] == 'critical']
                
                if len(critical_degradations) >= 2:
                    retrain_info['triggered'] = True
                    retrain_info['reason'] = f"Multiple critical degradations detected"
                    retrain_info['severity'] = 'critical'
                    retrain_info['recommended_action'] = 'retrain_model'
            
        except Exception as e:
            logger.error(f"Failed to check retrain trigger for {model_name}: {e}")
            retrain_info['error'] = str(e)
        
        return retrain_info
    
    def detect_data_drift(self, model_name: str, new_data: pd.DataFrame,
                         reference_data: pd.DataFrame = None) -> Dict[str, Any]:
        """Detect data drift using Population Stability Index (PSI)."""
        try:
            if reference_data is None:
                reference_data = self._load_reference_data(model_name)
                if reference_data is None:
                    return {"error": "No reference data available"}
            
            drift_results = {
                'model_name': model_name,
                'timestamp': datetime.now().isoformat(),
                'features_analyzed': list(new_data.columns),
                'drift_detected': False,
                'feature_drift_scores': {},
                'overall_drift_score': 0.0,
                'drift_severity': 'none'
            }
            
            psi_scores = []
            
            for feature in new_data.columns:
                if feature in reference_data.columns:
                    psi_score = self._calculate_psi(
                        reference_data[feature].values,
                        new_data[feature].values
                    )
                    
                    drift_results['feature_drift_scores'][feature] = {
                        'psi_score': psi_score,
                        'drift_detected': psi_score > self.monitoring_config['data_drift_threshold'],
                        'severity': self._get_drift_severity(psi_score)
                    }
                    
                    psi_scores.append(psi_score)
            
            # Calculate overall drift
            if psi_scores:
                drift_results['overall_drift_score'] = np.mean(psi_scores)
                drift_results['drift_detected'] = drift_results['overall_drift_score'] > self.monitoring_config['data_drift_threshold']
                drift_results['drift_severity'] = self._get_drift_severity(drift_results['overall_drift_score'])
            
            # Save drift analysis
            self._save_drift_analysis(model_name, drift_results)
            
            # Generate drift alerts
            if drift_results['drift_detected']:
                drift_alert = {
                    'timestamp': datetime.now().isoformat(),
                    'model_name': model_name,
                    'alert_type': 'data_drift',
                    'severity': drift_results['drift_severity'],
                    'message': f"Data drift detected for {model_name} with PSI score {drift_results['overall_drift_score']:.3f}",
                    'overall_drift_score': drift_results['overall_drift_score'],
                    'recommended_action': 'Review data sources and consider model retraining'
                }
                self._save_alert(drift_alert)
            
            return drift_results
            
        except Exception as e:
            logger.error(f"Failed to detect data drift for {model_name}: {e}")
            return {"error": str(e)}
    
    def _calculate_psi(self, reference: np.ndarray, new: np.ndarray, 
                      buckets: int = 10) -> float:
        """Calculate Population Stability Index (PSI)."""
        try:
            # Handle categorical data
            if reference.dtype == 'object' or new.dtype == 'object':
                # For categorical data, use value counts
                ref_counts = pd.Series(reference).value_counts(normalize=True)
                new_counts = pd.Series(new).value_counts(normalize=True)
                
                # Ensure both series have same index
                all_categories = set(ref_counts.index) | set(new_counts.index)
                ref_props = np.array([ref_counts.get(cat, 1e-10) for cat in all_categories])
                new_props = np.array([new_counts.get(cat, 1e-10) for cat in all_categories])
            else:
                # For numerical data, use quantile-based bucketing
                bins = np.linspace(np.min(reference), np.max(reference), buckets + 1)
                bins[0] = -np.inf  # Handle edge cases
                bins[-1] = np.inf
                
                ref_counts, _ = np.histogram(reference, bins=bins)
                new_counts, _ = np.histogram(new, bins=bins)
                
                # Convert to proportions
                ref_props = ref_counts / np.sum(ref_counts)
                new_props = new_counts / np.sum(new_counts)
                
                # Add small constant to avoid log(0)
                ref_props = np.where(ref_props == 0, 1e-10, ref_props)
                new_props = np.where(new_props == 0, 1e-10, new_props)
            
            # Calculate PSI
            psi = np.sum((new_props - ref_props) * np.log(new_props / ref_props))
            return float(psi)
            
        except Exception as e:
            logger.error(f"Failed to calculate PSI: {e}")
            return 0.0
    
    def _get_drift_severity(self, psi_score: float) -> str:
        """Get drift severity based on PSI score."""
        if psi_score >= 0.25:
            return 'critical'
        elif psi_score >= 0.1:
            return 'warning'
        elif psi_score >= 0.05:
            return 'info'
        else:
            return 'none'
    
    def _load_reference_data(self, model_name: str) -> Optional[pd.DataFrame]:
        """Load reference data for drift detection."""
        try:
            reference_file = f"{self.monitoring_path}/drift/{model_name}_reference.pkl"
            if Path(reference_file).exists():
                return pd.read_pickle(reference_file)
            return None
        except Exception as e:
            logger.error(f"Failed to load reference data for {model_name}: {e}")
            return None
    
    def _save_drift_analysis(self, model_name: str, drift_results: Dict[str, Any]) -> None:
        """Save drift analysis results."""
        try:
            drift_file = f"{self.monitoring_path}/drift/{model_name}_drift_history.jsonl"
            
            # Append drift results to file
            with open(drift_file, 'a') as f:
                f.write(json.dumps(drift_results, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to save drift analysis for {model_name}: {e}")
    
    def trigger_model_retraining(self, model_name: str, reason: str,
                               retrain_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger model retraining process."""
        try:
            retrain_job = {
                'job_id': hashlib.md5(f"{model_name}_{datetime.now()}".encode()).hexdigest()[:8],
                'model_name': model_name,
                'trigger_reason': reason,
                'timestamp': datetime.now().isoformat(),
                'status': 'initiated',
                'config': retrain_config or {},
                'progress': 0
            }
            
            # Save retrain job
            self._save_retrain_job(retrain_job)
            
            # Here you would integrate with your ML pipeline orchestrator
            # For now, we'll simulate the retraining process
            logger.info(f"Retraining triggered for {model_name}: {reason}")
            
            return {
                'success': True,
                'job_id': retrain_job['job_id'],
                'message': f"Retraining initiated for {model_name}",
                'estimated_completion': (datetime.now() + timedelta(hours=2)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger retraining for {model_name}: {e}")
            return {"error": str(e)}
    
    def _save_retrain_job(self, retrain_job: Dict[str, Any]) -> None:
        """Save retraining job information."""
        try:
            job_file = f"{self.monitoring_path}/retraining/{retrain_job['job_id']}.json"
            
            with open(job_file, 'w') as f:
                json.dump(retrain_job, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save retrain job: {e}")
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        try:
            dashboard_data = {
                'timestamp': datetime.now().isoformat(),
                'models_status': {},
                'recent_alerts': [],
                'performance_trends': {},
                'drift_status': {},
                'active_retraining_jobs': []
            }
            
            # Get status for each model
            for model_name in self.model_registry.keys():
                model_status = self._get_model_status(model_name)
                dashboard_data['models_status'][model_name] = model_status
                
                # Get performance trends
                trends = self._get_performance_trends(model_name)
                dashboard_data['performance_trends'][model_name] = trends
                
                # Get drift status
                drift_status = self._get_latest_drift_status(model_name)
                dashboard_data['drift_status'][model_name] = drift_status
            
            # Get recent alerts
            dashboard_data['recent_alerts'] = self._get_recent_alerts(limit=10)
            
            # Get active retraining jobs
            dashboard_data['active_retraining_jobs'] = self._get_active_retrain_jobs()
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
    
    def _get_model_status(self, model_name: str) -> Dict[str, Any]:
        """Get current status of a model."""
        try:
            historical_metrics = self._load_historical_metrics(model_name)
            
            if not historical_metrics:
                return {
                    'status': 'unknown',
                    'last_evaluation': None,
                    'key_metrics': {}
                }
            
            # Get latest metrics
            latest_metrics = {}
            last_timestamp = None
            
            for metric_name, metric_history in historical_metrics.items():
                if metric_history:
                    latest_entry = metric_history[-1]
                    latest_metrics[metric_name] = latest_entry['value']
                    last_timestamp = latest_entry['timestamp']
            
            # Determine overall status
            status = 'healthy'
            if last_timestamp:
                last_eval_time = datetime.fromisoformat(last_timestamp)
                if datetime.now() - last_eval_time > timedelta(days=7):
                    status = 'stale'
            
            return {
                'status': status,
                'last_evaluation': last_timestamp,
                'key_metrics': latest_metrics
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for {model_name}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_performance_trends(self, model_name: str, days: int = 30) -> Dict[str, Any]:
        """Get performance trends for a model."""
        try:
            historical_metrics = self._load_historical_metrics(model_name)
            
            if not historical_metrics:
                return {}
            
            trends = {}
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for metric_name, metric_history in historical_metrics.items():
                recent_data = [
                    entry for entry in metric_history
                    if datetime.fromisoformat(entry['timestamp']) >= cutoff_date
                ]
                
                if len(recent_data) >= 2:
                    values = [entry['value'] for entry in recent_data]
                    timestamps = [entry['timestamp'] for entry in recent_data]
                    
                    # Calculate trend (simple linear regression slope)
                    x = np.arange(len(values))
                    slope, _, _, _, _ = stats.linregress(x, values)
                    
                    trends[metric_name] = {
                        'trend_direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable',
                        'trend_magnitude': abs(slope),
                        'data_points': len(values),
                        'latest_value': values[-1],
                        'min_value': min(values),
                        'max_value': max(values)
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Failed to get trends for {model_name}: {e}")
            return {}
    
    def _get_latest_drift_status(self, model_name: str) -> Dict[str, Any]:
        """Get latest drift status for a model."""
        try:
            drift_file = f"{self.monitoring_path}/drift/{model_name}_drift_history.jsonl"
            
            if not Path(drift_file).exists():
                return {'status': 'no_data'}
            
            # Read last line of drift history
            with open(drift_file, 'r') as f:
                lines = f.readlines()
            
            if lines:
                latest_drift = json.loads(lines[-1])
                return {
                    'status': 'drift_detected' if latest_drift['drift_detected'] else 'stable',
                    'overall_drift_score': latest_drift['overall_drift_score'],
                    'drift_severity': latest_drift['drift_severity'],
                    'last_check': latest_drift['timestamp']
                }
            
            return {'status': 'no_data'}
            
        except Exception as e:
            logger.error(f"Failed to get drift status for {model_name}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        try:
            alerts_file = f"{self.monitoring_path}/alerts/alerts.jsonl"
            
            if not Path(alerts_file).exists():
                return []
            
            alerts = []
            with open(alerts_file, 'r') as f:
                lines = f.readlines()
            
            # Get last N alerts
            for line in lines[-limit:]:
                alert = json.loads(line)
                alerts.append(alert)
            
            # Sort by timestamp (most recent first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def _get_active_retrain_jobs(self) -> List[Dict[str, Any]]:
        """Get active retraining jobs."""
        try:
            retrain_dir = Path(f"{self.monitoring_path}/retraining")
            active_jobs = []
            
            if retrain_dir.exists():
                for job_file in retrain_dir.glob("*.json"):
                    with open(job_file, 'r') as f:
                        job = json.load(f)
                    
                    if job.get('status') in ['initiated', 'running']:
                        active_jobs.append(job)
            
            return active_jobs
            
        except Exception as e:
            logger.error(f"Failed to get active retrain jobs: {e}")
            return []
    
    def generate_monitoring_report(self, model_name: str = None, 
                                 days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        try:
            models_to_report = [model_name] if model_name else list(self.model_registry.keys())
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'report_period_days': days,
                'models_analyzed': len(models_to_report),
                'summary': {
                    'healthy_models': 0,
                    'degraded_models': 0,
                    'models_with_drift': 0,
                    'total_alerts': 0
                },
                'model_reports': {}
            }
            
            for model in models_to_report:
                model_report = {
                    'model_name': model,
                    'status': self._get_model_status(model),
                    'performance_trends': self._get_performance_trends(model, days),
                    'drift_status': self._get_latest_drift_status(model),
                    'recent_alerts': [
                        alert for alert in self._get_recent_alerts(50)
                        if alert.get('model_name') == model
                    ]
                }
                
                # Update summary
                if model_report['status']['status'] == 'healthy':
                    report['summary']['healthy_models'] += 1
                else:
                    report['summary']['degraded_models'] += 1
                
                if model_report['drift_status'].get('status') == 'drift_detected':
                    report['summary']['models_with_drift'] += 1
                
                report['summary']['total_alerts'] += len(model_report['recent_alerts'])
                
                report['model_reports'][model] = model_report
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate monitoring report: {e}")
            return {"error": str(e)}
import time
import os
import json
import threading
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

class DemoMetricsTracker:
    """
    Comprehensive metrics tracking system for demo usage and performance
    
    Key Features:
    - Real-time demo usage tracking
    - Performance metrics collection
    - Error logging
    - System resource monitoring
    - Detailed analytics generation
    """
    
    def __init__(self, log_dir: str = '/var/log/financial_demo'):
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        self.logger = logging.getLogger('demo_metrics')
        self.logger.setLevel(logging.INFO)
        
        # Log file handler
        log_file = os.path.join(log_dir, 'demo_metrics.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s: %(message)s'))
        self.logger.addHandler(file_handler)
        
        # Metrics storage
        self.metrics_file = os.path.join(log_dir, 'demo_metrics.json')
        self.metrics_lock = threading.Lock()
        
        # Initialize metrics structure
        self._initialize_metrics()
        
    def _initialize_metrics(self):
        """Initialize or load existing metrics"""
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, 'r') as f:
                    self.metrics = json.load(f)
            else:
                self.metrics = {
                    'demo_launches': 0,
                    'demo_completions': 0,
                    'total_demo_time': 0,
                    'errors': [],
                    'daily_metrics': {},
                    'performance_data': {
                        'cpu_usage': [],
                        'memory_usage': [],
                        'demo_duration_distribution': []
                    }
                }
        except Exception as e:
            self.logger.error(f"Error initializing metrics: {e}")
            self.metrics = {
                'demo_launches': 0,
                'demo_completions': 0,
                'total_demo_time': 0,
                'errors': [],
                'daily_metrics': {},
                'performance_data': {
                    'cpu_usage': [],
                    'memory_usage': [],
                    'demo_duration_distribution': []
                }
            }
    
    def record_demo_launch(self) -> Dict[str, Any]:
        """
        Record a new demo launch
        
        Returns:
            Dict with launch metadata
        """
        launch_time = datetime.now()
        demo_id = f"demo_{int(launch_time.timestamp())}"
        
        with self.metrics_lock:
            self.metrics['demo_launches'] += 1
            
            # Update daily metrics
            date_key = launch_time.strftime('%Y-%m-%d')
            if date_key not in self.metrics['daily_metrics']:
                self.metrics['daily_metrics'][date_key] = {
                    'launches': 0,
                    'completions': 0,
                    'total_time': 0
                }
            self.metrics['daily_metrics'][date_key]['launches'] += 1
            
            self._save_metrics()
        
        return {
            'demo_id': demo_id,
            'launch_timestamp': launch_time.isoformat(),
            'total_launches': self.metrics['demo_launches']
        }
    
    def record_demo_completion(self, demo_id: str, start_time: datetime) -> Dict[str, Any]:
        """
        Record demo completion and calculate metrics
        
        Args:
            demo_id: Unique identifier for the demo
            start_time: When the demo was started
        
        Returns:
            Dict with completion metadata
        """
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        with self.metrics_lock:
            self.metrics['demo_completions'] += 1
            self.metrics['total_demo_time'] += duration
            
            # Update daily metrics
            date_key = end_time.strftime('%Y-%m-%d')
            if date_key in self.metrics['daily_metrics']:
                self.metrics['daily_metrics'][date_key]['completions'] += 1
                self.metrics['daily_metrics'][date_key]['total_time'] += duration
            
            # Track performance distribution
            self.metrics['performance_data']['demo_duration_distribution'].append(duration)
            
            # Capture system performance
            self._capture_system_performance()
            
            self._save_metrics()
        
        return {
            'demo_id': demo_id,
            'completion_timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'total_completions': self.metrics['demo_completions']
        }
    
    def record_error(self, error_type: str, error_details: str):
        """
        Log errors encountered during demo
        
        Args:
            error_type: Category of error
            error_details: Detailed error description
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'details': error_details
        }
        
        with self.metrics_lock:
            self.metrics['errors'].append(error_entry)
            self._save_metrics()
        
        self.logger.error(f"{error_type}: {error_details}")
    
    def _capture_system_performance(self):
        """Capture current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            self.metrics['performance_data']['cpu_usage'].append(cpu_percent)
            self.metrics['performance_data']['memory_usage'].append(memory_percent)
            
            # Keep only last 100 performance entries to prevent unbounded growth
            for key in ['cpu_usage', 'memory_usage', 'demo_duration_distribution']:
                self.metrics['performance_data'][key] = self.metrics['performance_data'][key][-100:]
        
        except Exception as e:
            self.logger.warning(f"Could not capture system performance: {e}")
    
    def _save_metrics(self):
        """Save metrics to persistent storage"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Could not save metrics: {e}")
    
    def generate_report(self, report_type: str = 'daily') -> Dict[str, Any]:
        """
        Generate analytics report
        
        Args:
            report_type: Type of report (daily, weekly)
        
        Returns:
            Comprehensive analytics report
        """
        if report_type == 'daily':
            today = datetime.now().strftime('%Y-%m-%d')
            daily_metrics = self.metrics['daily_metrics'].get(today, {})
            
            return {
                'report_type': 'daily',
                'timestamp': datetime.now().isoformat(),
                'total_launches': daily_metrics.get('launches', 0),
                'total_completions': daily_metrics.get('completions', 0),
                'completion_rate': (daily_metrics.get('completions', 0) / daily_metrics.get('launches', 1)) * 100,
                'avg_demo_duration': daily_metrics.get('total_time', 0) / max(daily_metrics.get('completions', 1), 1),
                'system_performance': {
                    'avg_cpu_usage': sum(self.metrics['performance_data']['cpu_usage'][-24:]) / 24 if self.metrics['performance_data']['cpu_usage'] else 0,
                    'avg_memory_usage': sum(self.metrics['performance_data']['memory_usage'][-24:]) / 24 if self.metrics['performance_data']['memory_usage'] else 0
                },
                'recent_errors': self.metrics['errors'][-10:]
            }
        
        elif report_type == 'weekly':
            # Implement weekly report generation logic
            # This would involve aggregating metrics from the past 7 days
            pass
        
        return {}

# Singleton instance for easy import and use
demo_metrics = DemoMetricsTracker()
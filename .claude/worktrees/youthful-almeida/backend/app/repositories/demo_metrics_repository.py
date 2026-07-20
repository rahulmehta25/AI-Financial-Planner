from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database.models.demo_metrics import DemoMetric
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

class DemoMetricsRepository:
    """
    Database repository for managing and analyzing demo metrics
    
    Provides advanced querying and analytics capabilities for demo performance
    """
    
    def __init__(self, session: Session):
        """
        Initialize repository with database session
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
    
    def create_demo_metric(self, demo_data: Dict[str, Any]) -> DemoMetric:
        """
        Create and persist a new demo metric record
        
        Args:
            demo_data: Dictionary of demo metric data
        
        Returns:
            Persisted DemoMetric instance
        """
        demo_metric = DemoMetric(**demo_data)
        self.session.add(demo_metric)
        self.session.commit()
        return demo_metric
    
    def update_demo_metric(
        self, 
        demo_id: str, 
        update_data: Dict[str, Any]
    ) -> Optional[DemoMetric]:
        """
        Update an existing demo metric record
        
        Args:
            demo_id: Unique identifier for the demo
            update_data: Dictionary of fields to update
        
        Returns:
            Updated DemoMetric instance or None
        """
        demo_metric = self.session.query(DemoMetric).filter_by(demo_id=demo_id).first()
        
        if demo_metric:
            for key, value in update_data.items():
                setattr(demo_metric, key, value)
            
            self.session.commit()
            return demo_metric
        
        return None
    
    def get_demo_metrics(
        self, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        demo_type: Optional[str] = None
    ) -> List[DemoMetric]:
        """
        Retrieve demo metrics with optional filtering
        
        Args:
            start_date: Filter metrics from this date
            end_date: Filter metrics up to this date
            demo_type: Filter by specific demo type
        
        Returns:
            List of DemoMetric instances
        """
        query = self.session.query(DemoMetric)
        
        if start_date:
            query = query.filter(DemoMetric.start_time >= start_date)
        
        if end_date:
            query = query.filter(DemoMetric.start_time <= end_date)
        
        if demo_type:
            query = query.filter(DemoMetric.demo_type == demo_type)
        
        return query.all()
    
    def get_performance_summary(
        self, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive performance summary for recent demos
        
        Args:
            days: Number of days to look back
        
        Returns:
            Dictionary with performance metrics
        """
        # Calculate the start date
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Total demos
        total_demos = self.session.query(func.count(DemoMetric.id)).filter(
            DemoMetric.start_time >= start_date
        ).scalar()
        
        # Completed demos
        completed_demos = self.session.query(func.count(DemoMetric.id)).filter(
            DemoMetric.start_time >= start_date,
            DemoMetric.completed == True
        ).scalar()
        
        # Average duration
        avg_duration = self.session.query(func.avg(DemoMetric.duration)).filter(
            DemoMetric.start_time >= start_date
        ).scalar()
        
        # Performance statistics
        avg_cpu_usage = self.session.query(func.avg(DemoMetric.cpu_usage_avg)).filter(
            DemoMetric.start_time >= start_date
        ).scalar()
        
        avg_memory_usage = self.session.query(func.avg(DemoMetric.memory_usage_avg)).filter(
            DemoMetric.start_time >= start_date
        ).scalar()
        
        # Most common demo types
        demo_type_counts = self.session.query(
            DemoMetric.demo_type, 
            func.count(DemoMetric.id)
        ).filter(
            DemoMetric.start_time >= start_date
        ).group_by(
            DemoMetric.demo_type
        ).order_by(
            desc(func.count(DemoMetric.id))
        ).limit(5).all()
        
        return {
            "total_demos": total_demos,
            "completed_demos": completed_demos,
            "completion_rate": (completed_demos / total_demos) * 100 if total_demos > 0 else 0,
            "avg_duration_seconds": avg_duration or 0,
            "avg_cpu_usage": avg_cpu_usage or 0,
            "avg_memory_usage": avg_memory_usage or 0,
            "top_demo_types": dict(demo_type_counts)
        }
    
    def close(self):
        """Close the database session"""
        self.session.close()
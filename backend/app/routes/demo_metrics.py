from fastapi import APIRouter, Depends
from app.sdk.demo_metrics import demo_metrics
from typing import Dict, Any

router = APIRouter(prefix="/demo/metrics", tags=["Demo Metrics"])

@router.get("/", response_model=Dict[str, Any])
async def get_demo_metrics(report_type: str = 'daily'):
    """
    Retrieve demo metrics report
    
    Args:
        report_type: Type of report to generate (daily/weekly)
    
    Returns:
        Comprehensive metrics report
    """
    report = demo_metrics.generate_report(report_type)
    
    # Fetch historical performance data
    performance_history = [
        {
            'timestamp': data[0],
            'cpu_usage': data[1],
            'memory_usage': data[2],
            'demo_duration': data[3]
        } 
        for data in zip(
            report.get('timestamps', []), 
            report.get('cpu_usage', []), 
            report.get('memory_usage', []), 
            report.get('demo_durations', [])
        )
    ]
    
    return {
        'daily_metrics': report,
        'performance_history': performance_history
    }

@router.post("/record-launch")
async def record_demo_launch():
    """
    Record a new demo launch
    
    Returns:
        Metadata about the demo launch
    """
    return demo_metrics.record_demo_launch()

@router.post("/record-completion")
async def record_demo_completion(
    demo_id: str, 
    start_timestamp: str
):
    """
    Record demo completion
    
    Args:
        demo_id: Unique identifier for the demo
        start_timestamp: When the demo was started
    
    Returns:
        Metadata about the demo completion
    """
    from datetime import datetime
    start_time = datetime.fromisoformat(start_timestamp)
    return demo_metrics.record_demo_completion(demo_id, start_time)

@router.post("/record-error")
async def record_demo_error(
    error_type: str,
    error_details: str
):
    """
    Record an error during demo
    
    Args:
        error_type: Category of error
        error_details: Detailed error description
    """
    demo_metrics.record_error(error_type, error_details)
    return {"status": "error recorded"}
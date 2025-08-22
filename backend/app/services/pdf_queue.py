"""
Celery-based async PDF generation queue
"""

import os
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from celery import Celery
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.pdf_generator import PDFGeneratorService, FinancialPlanData
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal

logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    "financial_planning_pdf",
    broker=settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://localhost:6379/0",
    backend=settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://localhost:6379/0",
    include=['app.services.pdf_queue']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Database model for PDF job tracking
Base = declarative_base()

class PDFJobModel(Base):
    """Database model for PDF generation jobs"""
    __tablename__ = "pdf_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    plan_id = Column(UUID(as_uuid=True), nullable=True)
    format_type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    celery_task_id = Column(String(100), nullable=True)


class PDFJobManager:
    """Manager for PDF generation jobs"""
    
    def __init__(self):
        self.engine = create_engine(settings.DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=self.engine)
    
    def create_job(
        self,
        user_id: uuid.UUID,
        plan_id: Optional[uuid.UUID],
        format_type: str,
        celery_task_id: str
    ) -> uuid.UUID:
        """Create new PDF generation job"""
        with self.SessionLocal() as db:
            job = PDFJobModel(
                user_id=user_id,
                plan_id=plan_id,
                format_type=format_type,
                celery_task_id=celery_task_id,
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return job.id
    
    def update_job_status(
        self,
        job_id: uuid.UUID,
        status: str,
        **kwargs
    ) -> bool:
        """Update job status and additional fields"""
        with self.SessionLocal() as db:
            job = db.query(PDFJobModel).filter(PDFJobModel.id == job_id).first()
            if not job:
                return False
            
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            
            db.commit()
            return True
    
    def get_job(self, job_id: uuid.UUID) -> Optional[PDFJobModel]:
        """Get job by ID"""
        with self.SessionLocal() as db:
            return db.query(PDFJobModel).filter(PDFJobModel.id == job_id).first()
    
    def get_user_jobs(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50
    ) -> list:
        """Get jobs for user"""
        with self.SessionLocal() as db:
            query = db.query(PDFJobModel).filter(PDFJobModel.user_id == user_id)
            
            if status:
                query = query.filter(PDFJobModel.status == status)
            
            return query.order_by(PDFJobModel.created_at.desc()).limit(limit).all()
    
    def cleanup_expired_jobs(self):
        """Clean up expired jobs and files"""
        with self.SessionLocal() as db:
            expired_jobs = db.query(PDFJobModel).filter(
                PDFJobModel.expires_at < datetime.utcnow(),
                PDFJobModel.status == "completed"
            ).all()
            
            for job in expired_jobs:
                # Delete file if it exists
                if job.file_path and os.path.exists(job.file_path):
                    try:
                        os.remove(job.file_path)
                        logger.info(f"Deleted expired PDF file: {job.file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete file {job.file_path}: {e}")
                
                # Delete job record
                db.delete(job)
            
            db.commit()
            logger.info(f"Cleaned up {len(expired_jobs)} expired PDF jobs")


# Global job manager instance
job_manager = PDFJobManager()


@celery_app.task(bind=True, max_retries=3)
def generate_pdf_task(
    self,
    job_id: str,
    user_data: Dict[str, Any],
    financial_profile_data: Dict[str, Any],
    goals_data: list,
    request_data: Dict[str, Any]
):
    """
    Celery task to generate PDF in background
    
    Args:
        job_id: UUID of the PDF job
        user_data: User information
        financial_profile_data: Financial profile data
        goals_data: List of financial goals
        request_data: PDF generation request parameters
    """
    job_uuid = uuid.UUID(job_id)
    
    try:
        # Update job status to processing
        job_manager.update_job_status(
            job_uuid,
            "processing",
            started_at=datetime.utcnow(),
            celery_task_id=self.request.id
        )
        
        logger.info(f"Starting PDF generation for job {job_id}")
        
        # Reconstruct objects from data
        user = _reconstruct_user(user_data)
        financial_profile = _reconstruct_financial_profile(financial_profile_data)
        goals = _reconstruct_goals(goals_data)
        
        # Create simulation results (simplified for this example)
        simulation_results = _generate_simulation_results(financial_profile)
        
        # Create AI narrative and recommendations
        ai_narrative = _generate_ai_narrative(financial_profile, request_data)
        recommendations = _generate_recommendations(financial_profile, goals)
        
        # Create plan data
        plan_data = FinancialPlanData(
            user=user,
            financial_profile=financial_profile,
            goals=goals,
            simulation_results=simulation_results,
            ai_narrative=ai_narrative,
            recommendations=recommendations
        )
        
        # Generate PDF
        pdf_service = PDFGeneratorService()
        pdf_bytes = pdf_service.generate_comprehensive_plan_pdf(
            plan_data,
            format_type=request_data['format_type']
        )
        
        # Save PDF to file
        file_path = _save_pdf_file(job_uuid, user_data['id'], pdf_bytes)
        
        # Update job with completion info
        job_manager.update_job_status(
            job_uuid,
            "completed",
            completed_at=datetime.utcnow(),
            file_path=file_path,
            file_size=len(pdf_bytes),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        logger.info(f"PDF generation completed for job {job_id}, file saved to {file_path}")
        
        return {
            "status": "completed",
            "file_path": file_path,
            "file_size": len(pdf_bytes)
        }
        
    except Exception as e:
        logger.error(f"PDF generation failed for job {job_id}: {e}")
        
        # Update job with error
        job_manager.update_job_status(
            job_uuid,
            "failed",
            completed_at=datetime.utcnow(),
            error_message=str(e)
        )
        
        # Retry if possible
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying PDF generation for job {job_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)
        
        raise e


def _reconstruct_user(user_data: Dict[str, Any]) -> User:
    """Reconstruct User object from data"""
    user = User()
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    return user


def _reconstruct_financial_profile(profile_data: Dict[str, Any]) -> FinancialProfile:
    """Reconstruct FinancialProfile object from data"""
    profile = FinancialProfile()
    for key, value in profile_data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    return profile


def _reconstruct_goals(goals_data: list) -> list:
    """Reconstruct Goal objects from data"""
    goals = []
    for goal_data in goals_data:
        goal = Goal()
        for key, value in goal_data.items():
            if hasattr(goal, key):
                setattr(goal, key, value)
        goals.append(goal)
    return goals


def _generate_simulation_results(financial_profile: FinancialProfile) -> Dict[str, Any]:
    """Generate basic simulation results"""
    current_net_worth = financial_profile.net_worth
    growth_rate = 0.07  # 7% annual growth
    
    return {
        'net_worth_projection': [
            {
                'year': 2024 + i,
                'net_worth': current_net_worth * ((1 + growth_rate) ** i)
            }
            for i in range(10)
        ],
        'monte_carlo': {
            'years': list(range(2024, 2034)),
            'percentile_10': [current_net_worth * ((1 + 0.04) ** i) for i in range(10)],
            'percentile_50': [current_net_worth * ((1 + 0.07) ** i) for i in range(10)],
            'percentile_90': [current_net_worth * ((1 + 0.10) ** i) for i in range(10)]
        }
    }


def _generate_ai_narrative(financial_profile: FinancialProfile, request_data: Dict) -> str:
    """Generate AI narrative based on profile"""
    risk_level = financial_profile.risk_tolerance
    income = float(financial_profile.annual_income)
    net_worth = financial_profile.net_worth
    debt_ratio = financial_profile.debt_to_income_ratio
    
    narrative = f"""Based on your {risk_level} risk profile and current financial position, here's our analysis:
    
    Your current net worth of ${net_worth:,.0f} combined with an annual income of ${income:,.0f} puts you in a 
    solid financial position. Your debt-to-income ratio of {debt_ratio:.1%} is {"within healthy ranges" if debt_ratio < 0.36 else "above recommended levels"}.
    
    {"Given your conservative approach, focus on capital preservation while building long-term wealth through steady, low-risk investments." if risk_level == "conservative" else ""}
    {"With your moderate risk tolerance, you have good opportunities for balanced growth through diversified investments." if risk_level == "moderate" else ""}
    {"Your aggressive risk profile allows for higher growth potential through equity-focused investments over the long term." if risk_level == "aggressive" else ""}
    
    Key priorities should include {"building your emergency fund, " if net_worth < income * 0.5 else ""}optimizing your investment allocation, 
    and {"reducing high-interest debt" if debt_ratio > 0.36 else "maintaining your current debt management"}.
    """
    
    return narrative.strip()


def _generate_recommendations(financial_profile: FinancialProfile, goals: list) -> list:
    """Generate recommendations based on profile and goals"""
    recommendations = []
    
    # Emergency fund recommendation
    if financial_profile.net_worth < float(financial_profile.annual_income) * 0.5:
        recommendations.append({
            "title": "Build Emergency Fund",
            "description": "Establish 6 months of expenses in liquid savings for financial security",
            "priority": "high",
            "action_items": [
                "Open high-yield savings account",
                "Set up automatic monthly transfers",
                "Target $30,000-50,000 emergency fund"
            ]
        })
    
    # Investment allocation recommendation
    recommendations.append({
        "title": "Optimize Investment Allocation",
        "description": f"Adjust portfolio based on your {financial_profile.risk_tolerance} risk profile",
        "priority": "medium",
        "action_items": [
            "Review current asset allocation",
            "Consider low-cost index funds",
            "Rebalance quarterly"
        ]
    })
    
    # Debt management if needed
    if financial_profile.debt_to_income_ratio > 0.36:
        recommendations.append({
            "title": "Debt Reduction Strategy",
            "description": "Reduce debt-to-income ratio to below 36%",
            "priority": "high",
            "action_items": [
                "List all debts by interest rate",
                "Consider debt consolidation",
                "Focus on highest-rate debts first"
            ]
        })
    
    # Goal-specific recommendations
    if goals:
        recommendations.append({
            "title": "Goal Progress Acceleration",
            "description": f"Optimize progress toward your {len(goals)} financial goals",
            "priority": "medium",
            "action_items": [
                "Review monthly contributions",
                "Consider automatic investing",
                "Set quarterly progress reviews"
            ]
        })
    
    return recommendations


def _save_pdf_file(job_id: uuid.UUID, user_id: str, pdf_bytes: bytes) -> str:
    """Save PDF to file system"""
    import tempfile
    
    # Create directory if it doesn't exist
    pdf_dir = os.path.join(tempfile.gettempdir(), "financial_plans")
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Generate file path
    filename = f"financial_plan_{user_id}_{job_id}.pdf"
    file_path = os.path.join(pdf_dir, filename)
    
    # Write PDF to file
    with open(file_path, 'wb') as f:
        f.write(pdf_bytes)
    
    return file_path


# Periodic task to clean up expired jobs
@celery_app.task
def cleanup_expired_pdfs():
    """Periodic task to clean up expired PDF files"""
    job_manager.cleanup_expired_jobs()


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'cleanup-expired-pdfs': {
        'task': 'app.services.pdf_queue.cleanup_expired_pdfs',
        'schedule': 3600.0,  # Every hour
    },
}


class AsyncPDFService:
    """Service for managing async PDF generation"""
    
    def __init__(self):
        self.job_manager = job_manager
    
    def queue_pdf_generation(
        self,
        user: User,
        financial_profile: FinancialProfile,
        goals: list,
        request_data: Dict[str, Any],
        plan_id: Optional[uuid.UUID] = None
    ) -> uuid.UUID:
        """Queue PDF generation task"""
        
        # Serialize data for Celery
        user_data = {
            'id': str(user.id),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
        
        profile_data = {
            'annual_income': str(financial_profile.annual_income),
            'net_worth': financial_profile.net_worth,
            'risk_tolerance': financial_profile.risk_tolerance,
            'investment_experience': financial_profile.investment_experience,
            'debt_to_income_ratio': financial_profile.debt_to_income_ratio,
            'monthly_expenses': str(financial_profile.monthly_expenses or 0),
            'date_of_birth': financial_profile.date_of_birth.isoformat() if financial_profile.date_of_birth else None,
            'liquid_assets': str(financial_profile.liquid_assets or 0),
            'retirement_accounts': str(financial_profile.retirement_accounts or 0),
            'real_estate_value': str(financial_profile.real_estate_value or 0),
            'other_investments': str(financial_profile.other_investments or 0),
            'mortgage_balance': str(financial_profile.mortgage_balance or 0),
            'credit_card_debt': str(financial_profile.credit_card_debt or 0),
            'student_loans': str(financial_profile.student_loans or 0),
            'auto_loans': str(financial_profile.auto_loans or 0),
            'other_debts': str(financial_profile.other_debts or 0)
        }
        
        goals_data = []
        for goal in goals:
            goals_data.append({
                'id': str(goal.id),
                'name': goal.name,
                'target_amount': str(goal.target_amount),
                'current_amount': str(goal.current_amount or 0),
                'progress_percentage': float(goal.progress_percentage or 0),
                'target_date': goal.target_date.isoformat(),
                'monthly_contribution': str(goal.monthly_contribution or 0),
                'status': goal.status
            })
        
        # Queue Celery task
        task = generate_pdf_task.delay(
            str(uuid.uuid4()),  # This will be replaced with actual job_id
            user_data,
            profile_data,
            goals_data,
            request_data
        )
        
        # Create job record
        job_id = self.job_manager.create_job(
            user_id=user.id,
            plan_id=plan_id,
            format_type=request_data['format_type'],
            celery_task_id=task.id
        )
        
        return job_id
    
    def get_job_status(self, job_id: uuid.UUID) -> Optional[PDFJobModel]:
        """Get job status"""
        return self.job_manager.get_job(job_id)
    
    def get_user_jobs(self, user_id: uuid.UUID, **kwargs) -> list:
        """Get user's PDF jobs"""
        return self.job_manager.get_user_jobs(user_id, **kwargs)
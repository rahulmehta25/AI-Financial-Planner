"""
PDF Export API endpoints for financial planning reports
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.api import deps
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.schemas.pdf_export import (
    PDFExportRequest, PDFExportResponse, PDFExportJob, PDFDownloadResponse,
    PDFJobListResponse, PDFFormatType, PDFExportStatus, FinancialPlanPDFData
)
from app.services.pdf_generator import PDFGeneratorService, FinancialPlanData
from app.core.config import settings
from app.database.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory job storage (replace with Redis/database in production)
pdf_jobs: dict = {}


@router.post("/plan/{plan_id}/export/pdf", response_model=PDFExportResponse)
async def export_financial_plan_pdf(
    plan_id: uuid.UUID,
    request: PDFExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export financial plan as PDF
    
    Creates an async job to generate a professional PDF report containing:
    - Financial profile overview
    - Goals progress and analysis
    - Investment projections
    - AI-generated recommendations
    - Compliance disclaimers
    """
    try:
        # Verify user has access to the plan
        financial_profile = await _get_user_financial_profile(db, current_user.id)
        if not financial_profile:
            raise HTTPException(
                status_code=404,
                detail="Financial profile not found"
            )
        
        # Generate unique job ID
        job_id = uuid.uuid4()
        
        # Create job record
        job = PDFExportJob(
            id=job_id,
            user_id=current_user.id,
            plan_id=plan_id,
            format_type=request.format_type,
            status=PDFExportStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        # Store job (in production, use Redis or database)
        pdf_jobs[str(job_id)] = job
        
        # Start background task
        background_tasks.add_task(
            _generate_pdf_background,
            job_id=job_id,
            request=request,
            user=current_user,
            db=db
        )
        
        # Estimate completion time based on format
        estimated_time = {
            PDFFormatType.EXECUTIVE_SUMMARY: 15,
            PDFFormatType.PROFESSIONAL: 30,
            PDFFormatType.DETAILED: 60
        }.get(request.format_type, 30)
        
        return PDFExportResponse(
            job_id=job_id,
            status=PDFExportStatus.PENDING,
            message="PDF generation job has been queued successfully",
            estimated_completion_time=estimated_time
        )
        
    except Exception as e:
        logger.error(f"Error creating PDF export job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create PDF export job"
        )


@router.get("/pdf/jobs", response_model=PDFJobListResponse)
async def list_pdf_jobs(
    page: int = 1,
    per_page: int = 10,
    status: Optional[PDFExportStatus] = None,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    List PDF export jobs for the current user
    """
    try:
        # Filter jobs for current user
        user_jobs = [
            job for job in pdf_jobs.values() 
            if job.user_id == current_user.id
        ]
        
        # Apply status filter if provided
        if status:
            user_jobs = [job for job in user_jobs if job.status == status]
        
        # Sort by creation date (newest first)
        user_jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = user_jobs[start_idx:end_idx]
        
        return PDFJobListResponse(
            jobs=paginated_jobs,
            total=len(user_jobs),
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing PDF jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve PDF jobs"
        )


@router.get("/pdf/jobs/{job_id}", response_model=PDFExportJob)
async def get_pdf_job_status(
    job_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get status of a specific PDF export job
    """
    try:
        job = pdf_jobs.get(str(job_id))
        if not job:
            raise HTTPException(
                status_code=404,
                detail="PDF job not found"
            )
        
        # Verify job belongs to current user
        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this PDF job"
            )
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF job status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve PDF job status"
        )


@router.get("/pdf/download/{job_id}")
async def download_pdf(
    job_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Download completed PDF report
    """
    try:
        job = pdf_jobs.get(str(job_id))
        if not job:
            raise HTTPException(
                status_code=404,
                detail="PDF job not found"
            )
        
        # Verify job belongs to current user
        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this PDF job"
            )
        
        # Check if job is completed
        if job.status != PDFExportStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"PDF is not ready. Current status: {job.status}"
            )
        
        # Check if file exists and hasn't expired
        if not job.file_path or (job.expires_at and datetime.utcnow() > job.expires_at):
            raise HTTPException(
                status_code=410,
                detail="PDF file has expired or is no longer available"
            )
        
        # Generate filename
        filename = f"financial_plan_{current_user.first_name.lower()}_{current_user.last_name.lower()}_{job.created_at.strftime('%Y%m%d')}.pdf"
        
        # Return file response
        return FileResponse(
            path=job.file_path,
            filename=filename,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download PDF file"
        )


@router.delete("/pdf/jobs/{job_id}")
async def delete_pdf_job(
    job_id: uuid.UUID,
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Delete a PDF export job and associated files
    """
    try:
        job = pdf_jobs.get(str(job_id))
        if not job:
            raise HTTPException(
                status_code=404,
                detail="PDF job not found"
            )
        
        # Verify job belongs to current user
        if job.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied to this PDF job"
            )
        
        # Clean up file if it exists
        if job.file_path:
            try:
                import os
                if os.path.exists(job.file_path):
                    os.remove(job.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete PDF file {job.file_path}: {e}")
        
        # Remove job from storage
        del pdf_jobs[str(job_id)]
        
        return {"message": "PDF job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF job: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete PDF job"
        )


@router.post("/plan/export/pdf/immediate")
async def export_pdf_immediate(
    request: PDFExportRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate and return PDF immediately (for smaller reports)
    
    Use this endpoint for executive summaries or when immediate response is needed.
    For larger reports, use the async endpoint instead.
    """
    try:
        # Only allow immediate generation for executive summaries
        if request.format_type != PDFFormatType.EXECUTIVE_SUMMARY:
            raise HTTPException(
                status_code=400,
                detail="Immediate PDF generation only available for executive summaries"
            )
        
        # Get user financial data
        plan_data = await _prepare_plan_data(db, current_user, request)
        
        # Generate PDF
        pdf_service = PDFGeneratorService()
        pdf_bytes = await pdf_service.generate_comprehensive_plan_pdf(
            plan_data, 
            format_type=request.format_type
        )
        
        # Generate filename
        filename = f"financial_summary_{current_user.first_name.lower()}_{current_user.last_name.lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Return PDF as streaming response
        def generate():
            yield pdf_bytes
        
        return StreamingResponse(
            generate(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(pdf_bytes))
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating immediate PDF: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate PDF report"
        )


# Background task functions

async def _generate_pdf_background(
    job_id: uuid.UUID,
    request: PDFExportRequest,
    user: User,
    db: AsyncSession
):
    """Background task to generate PDF"""
    try:
        # Update job status
        job = pdf_jobs[str(job_id)]
        job.status = PDFExportStatus.PROCESSING
        job.started_at = datetime.utcnow()
        
        # Prepare plan data
        plan_data = await _prepare_plan_data(db, user, request)
        
        # Generate PDF
        pdf_service = PDFGeneratorService()
        pdf_bytes = await pdf_service.generate_comprehensive_plan_pdf(
            plan_data,
            format_type=request.format_type
        )
        
        # Save PDF to temporary file
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(
            temp_dir, 
            f"financial_plan_{user.id}_{job_id}.pdf"
        )
        
        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Update job with completion info
        job.status = PDFExportStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.file_path = file_path
        job.file_size = len(pdf_bytes)
        job.expires_at = datetime.utcnow() + timedelta(days=7)  # 7 day expiry
        job.download_url = f"/api/v1/pdf/download/{job_id}"
        
        logger.info(f"PDF generation completed for job {job_id}")
        
    except Exception as e:
        # Update job with error
        job = pdf_jobs.get(str(job_id))
        if job:
            job.status = PDFExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        
        logger.error(f"PDF generation failed for job {job_id}: {e}")


async def _prepare_plan_data(
    db: AsyncSession, 
    user: User, 
    request: PDFExportRequest
) -> FinancialPlanData:
    """Prepare financial plan data for PDF generation"""
    
    # Get financial profile
    financial_profile = await _get_user_financial_profile(db, user.id)
    if not financial_profile:
        raise HTTPException(
            status_code=404,
            detail="Financial profile not found"
        )
    
    # Get user goals
    goals = await _get_user_goals(db, user.id)
    
    # Simulate getting AI narrative and recommendations
    # In production, these would come from your AI services
    ai_narrative = None
    recommendations = []
    
    if request.include_ai_narrative:
        ai_narrative = f"""Based on your {financial_profile.risk_tolerance} risk profile and current financial position, 
        you are well-positioned to achieve your financial goals. Your debt-to-income ratio of {financial_profile.debt_to_income_ratio:.1%} 
        is within healthy ranges. Consider increasing your emergency fund and optimizing your investment allocation for long-term growth."""
    
    if request.include_recommendations:
        recommendations = [
            {
                "title": "Emergency Fund Optimization",
                "description": "Build emergency fund to 6 months of expenses for financial security",
                "priority": "high"
            },
            {
                "title": "Investment Diversification", 
                "description": "Consider diversifying portfolio based on your risk tolerance",
                "priority": "medium"
            },
            {
                "title": "Tax Optimization",
                "description": "Review tax-advantaged accounts to maximize savings",
                "priority": "medium"
            }
        ]
    
    # Simulate basic projection data
    simulation_results = {}
    if request.include_projections:
        current_net_worth = financial_profile.net_worth
        growth_rate = 0.07  # 7% annual growth assumption
        
        simulation_results = {
            'net_worth_projection': [
                {
                    'year': 2024 + i,
                    'net_worth': current_net_worth * ((1 + growth_rate) ** i)
                }
                for i in range(10)
            ]
        }
    
    return FinancialPlanData(
        user=user,
        financial_profile=financial_profile,
        goals=goals,
        simulation_results=simulation_results,
        ai_narrative=ai_narrative,
        recommendations=recommendations
    )


async def _get_user_financial_profile(db: AsyncSession, user_id: uuid.UUID) -> Optional[FinancialProfile]:
    """Get user's financial profile"""
    result = await db.execute(
        select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_user_goals(db: AsyncSession, user_id: uuid.UUID) -> List[Goal]:
    """Get user's financial goals"""
    result = await db.execute(
        select(Goal).where(
            and_(
                Goal.user_id == user_id,
                Goal.status == "active"
            )
        ).order_by(Goal.priority, Goal.target_date)
    )
    return result.scalars().all()
"""
Pydantic schemas for PDF export functionality
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID


class PDFFormatType(str, Enum):
    """PDF format types available for export"""
    PROFESSIONAL = "professional"
    EXECUTIVE_SUMMARY = "executive_summary" 
    DETAILED = "detailed"


class PDFExportRequest(BaseModel):
    """Request model for PDF export"""
    
    format_type: PDFFormatType = PDFFormatType.PROFESSIONAL
    include_charts: bool = True
    include_projections: bool = True
    include_ai_narrative: bool = True
    include_recommendations: bool = True
    custom_title: Optional[str] = None
    custom_subtitle: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "format_type": "professional",
                "include_charts": True,
                "include_projections": True,
                "include_ai_narrative": True,
                "include_recommendations": True,
                "custom_title": "My Financial Plan 2024",
                "custom_subtitle": "Strategic Investment Planning"
            }
        }


class PDFExportStatus(str, Enum):
    """PDF export job status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFExportJob(BaseModel):
    """PDF export job tracking"""
    
    id: UUID
    user_id: UUID
    plan_id: Optional[UUID] = None
    format_type: PDFFormatType
    status: PDFExportStatus = PDFExportStatus.PENDING
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "id": "12345678-1234-5678-9012-123456789012",
                "user_id": "87654321-4321-8765-2109-876543210987",
                "plan_id": "11111111-2222-3333-4444-555555555555",
                "format_type": "professional",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:32:15Z",
                "file_size": 2048576,
                "download_url": "/api/v1/pdf/download/12345678-1234-5678-9012-123456789012"
            }
        }


class PDFExportResponse(BaseModel):
    """Response for PDF export request"""
    
    job_id: UUID
    status: PDFExportStatus
    message: str
    estimated_completion_time: Optional[int] = None  # seconds
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "12345678-1234-5678-9012-123456789012",
                "status": "pending",
                "message": "PDF generation job has been queued",
                "estimated_completion_time": 30
            }
        }


class ChartData(BaseModel):
    """Chart data for PDF generation"""
    
    chart_type: str
    title: str
    data: Dict[str, Any]
    chart_base64: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "chart_type": "net_worth_projection",
                "title": "Net Worth Projection",
                "data": {
                    "years": [2024, 2025, 2026, 2027, 2028],
                    "values": [100000, 115000, 132250, 151988, 174286]
                }
            }
        }


class FinancialPlanPDFData(BaseModel):
    """Complete financial plan data for PDF generation"""
    
    user_info: Dict[str, Any]
    financial_profile: Dict[str, Any] 
    goals: List[Dict[str, Any]]
    simulation_results: Optional[Dict[str, Any]] = None
    ai_narrative: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    charts: Optional[List[ChartData]] = None
    generated_at: datetime = Field(default_factory=datetime.now)
    plan_id: Optional[UUID] = None
    
    @validator('charts', pre=True)
    def validate_charts(cls, v):
        """Validate charts data"""
        if v is None:
            return []
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "user_info": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 35
                },
                "financial_profile": {
                    "annual_income": 75000,
                    "net_worth": 150000,
                    "risk_tolerance": "moderate"
                },
                "goals": [
                    {
                        "name": "Emergency Fund",
                        "target_amount": 30000,
                        "current_amount": 15000,
                        "progress_percentage": 50.0
                    }
                ],
                "ai_narrative": "Based on your financial profile, you're on track to meet your retirement goals...",
                "generated_at": "2024-01-15T10:30:00Z"
            }
        }


class PDFDownloadResponse(BaseModel):
    """Response for PDF download"""
    
    job_id: UUID
    filename: str
    content_type: str = "application/pdf"
    file_size: int
    generated_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "12345678-1234-5678-9012-123456789012",
                "filename": "financial_plan_john_doe_2024.pdf",
                "content_type": "application/pdf",
                "file_size": 2048576,
                "generated_at": "2024-01-15T10:30:00Z",
                "expires_at": "2024-01-22T10:30:00Z"
            }
        }


class PDFJobListResponse(BaseModel):
    """Response for listing PDF jobs"""
    
    jobs: List[PDFExportJob]
    total: int
    page: int = 1
    per_page: int = 10
    
    class Config:
        schema_extra = {
            "example": {
                "jobs": [
                    {
                        "id": "12345678-1234-5678-9012-123456789012",
                        "user_id": "87654321-4321-8765-2109-876543210987",
                        "format_type": "professional",
                        "status": "completed",
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "total": 1,
                "page": 1,
                "per_page": 10
            }
        }


class ErrorDetail(BaseModel):
    """Error detail for failed PDF generation"""
    
    error_code: str
    error_message: str
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "error_code": "PDF_GENERATION_FAILED",
                "error_message": "Unable to generate charts due to missing data",
                "timestamp": "2024-01-15T10:30:00Z",
                "context": {"missing_fields": ["simulation_results"]}
            }
        }


class PDFJobError(BaseModel):
    """PDF job error response"""
    
    job_id: UUID
    status: PDFExportStatus = PDFExportStatus.FAILED
    error: ErrorDetail
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "12345678-1234-5678-9012-123456789012", 
                "status": "failed",
                "error": {
                    "error_code": "PDF_GENERATION_FAILED",
                    "error_message": "Chart generation failed",
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }


# Additional validation models

class PDFGenerationConfig(BaseModel):
    """Configuration for PDF generation"""
    
    page_size: str = "A4"
    orientation: str = "portrait"
    margin_top: float = 0.75
    margin_bottom: float = 0.75
    margin_left: float = 0.75
    margin_right: float = 0.75
    font_family: str = "Arial"
    font_size: int = 11
    include_page_numbers: bool = True
    include_header: bool = True
    include_footer: bool = True
    watermark: Optional[str] = None
    
    @validator('page_size')
    def validate_page_size(cls, v):
        """Validate page size"""
        allowed_sizes = ['A4', 'Letter', 'Legal']
        if v not in allowed_sizes:
            raise ValueError(f'Page size must be one of {allowed_sizes}')
        return v
    
    @validator('orientation')
    def validate_orientation(cls, v):
        """Validate page orientation"""
        allowed_orientations = ['portrait', 'landscape']
        if v not in allowed_orientations:
            raise ValueError(f'Orientation must be one of {allowed_orientations}')
        return v


class PDFQualitySettings(BaseModel):
    """PDF quality and optimization settings"""
    
    image_quality: int = Field(default=95, ge=1, le=100)
    image_compression: bool = True
    optimize_file_size: bool = True
    embed_fonts: bool = True
    pdf_version: str = "1.4"
    
    @validator('pdf_version')
    def validate_pdf_version(cls, v):
        """Validate PDF version"""
        allowed_versions = ['1.3', '1.4', '1.5', '1.6', '1.7']
        if v not in allowed_versions:
            raise ValueError(f'PDF version must be one of {allowed_versions}')
        return v


class ComplianceSettings(BaseModel):
    """Compliance and legal disclaimer settings"""
    
    include_disclaimer: bool = True
    custom_disclaimer: Optional[str] = None
    include_audit_trail: bool = True
    include_generation_metadata: bool = True
    advisor_information: Optional[Dict[str, str]] = None
    regulatory_notices: Optional[List[str]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "include_disclaimer": True,
                "include_audit_trail": True,
                "advisor_information": {
                    "name": "Jane Smith, CFP",
                    "license_number": "12345",
                    "firm": "ABC Financial Planning"
                },
                "regulatory_notices": [
                    "Securities offered through XYZ Broker-Dealer",
                    "Investment advice offered through ABC Investment Advisors"
                ]
            }
        }
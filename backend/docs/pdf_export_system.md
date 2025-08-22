# PDF Export System Documentation

## Overview

The PDF export system provides comprehensive financial planning report generation capabilities. It supports multiple formats, async processing, and professional-grade PDF output with charts, tables, and compliance information.

## Architecture

### Core Components

1. **PDF Generator Service** (`app/services/pdf_generator.py`)
   - WeasyPrint for HTML-to-PDF conversion
   - ReportLab for programmatic PDF generation
   - Professional template rendering with Jinja2

2. **Chart Generator Service** (`app/services/chart_generator.py`)
   - Plotly-based chart generation
   - High-DPI charts optimized for PDF inclusion
   - Multiple chart types (line, bar, pie, scatter, Monte Carlo)

3. **Async Queue System** (`app/services/pdf_queue.py`)
   - Celery-based background processing
   - Redis backend for job storage
   - Database tracking for job persistence

4. **API Endpoints** (`app/api/v1/endpoints/pdf_export.py`)
   - RESTful API for PDF generation
   - Job management and status tracking
   - Secure file download with expiration

## Features

### PDF Format Types

1. **Professional** (Default)
   - One-page comprehensive overview
   - Key metrics and charts
   - Executive summary format
   - Professional styling

2. **Executive Summary**
   - Concise 1-2 page report
   - Key highlights only
   - Quick generation (< 30 seconds)
   - Immediate download available

3. **Detailed**
   - Multi-page comprehensive analysis
   - Full asset/liability breakdown
   - Detailed goal analysis
   - Complete recommendation set

### Chart Types

- **Net Worth Projection**: Future net worth growth based on current savings
- **Goal Progress**: Visual progress tracking for financial goals
- **Asset Allocation**: Pie chart of current asset distribution
- **Cash Flow Analysis**: Monthly income vs expenses with trend
- **Monte Carlo Simulation**: Portfolio performance scenarios with confidence bands
- **Risk vs Return**: Portfolio optimization scatter plots

### Compliance Features

- Regulatory disclaimers
- Generation audit trail
- Plan ID and user ID tracking
- Advisor information inclusion
- Timestamp and versioning

## API Endpoints

### Main Export Endpoint

```http
POST /api/v1/plan/{plan_id}/export/pdf
```

**Request Body:**
```json
{
  "format_type": "professional",
  "include_charts": true,
  "include_projections": true,
  "include_ai_narrative": true,
  "include_recommendations": true,
  "custom_title": "My Financial Plan 2024",
  "custom_subtitle": "Strategic Investment Planning"
}
```

**Response:**
```json
{
  "job_id": "12345678-1234-5678-9012-123456789012",
  "status": "pending",
  "message": "PDF generation job has been queued successfully",
  "estimated_completion_time": 30
}
```

### Job Management

- `GET /api/v1/pdf/jobs` - List user's PDF jobs
- `GET /api/v1/pdf/jobs/{job_id}` - Get specific job status
- `GET /api/v1/pdf/download/{job_id}` - Download completed PDF
- `DELETE /api/v1/pdf/jobs/{job_id}` - Delete job and file

### Immediate Generation

```http
POST /api/v1/plan/export/pdf/immediate
```

For executive summaries only - returns PDF directly without queue.

## Security & Compliance

### Data Protection

- User data isolation (users can only access their own PDFs)
- Secure file storage with auto-expiration (7 days)
- No sensitive data in logs or error messages

### Compliance Disclaimers

All PDFs include:
- Investment disclaimer language
- Data source and generation method
- Plan ID for audit tracking
- Generation timestamp
- Risk warnings and limitations

### File Security

- Temporary file storage with automatic cleanup
- Secure download URLs with user verification
- File expiration and automatic deletion
- No permanent storage of sensitive data

## Configuration

### Environment Variables

```bash
# Redis for Celery (required for async processing)
REDIS_URL=redis://localhost:6379/0

# Database for job tracking
DATABASE_URL=postgresql://user:pass@localhost/financial_planning

# PDF Generation Settings
PDF_STORAGE_PATH=/tmp/financial_plans
PDF_EXPIRATION_DAYS=7
PDF_MAX_FILE_SIZE=50MB
```

### Celery Configuration

```python
# Start Celery worker
celery -A app.services.pdf_queue worker --loglevel=info

# Start Celery beat (for cleanup tasks)
celery -A app.services.pdf_queue beat --loglevel=info
```

## Technical Implementation

### Chart Generation Process

1. **Data Preparation**: Extract financial data from user profile and goals
2. **Chart Creation**: Generate Plotly charts with high-DPI settings
3. **Base64 Encoding**: Convert charts to base64 for HTML embedding
4. **Template Injection**: Insert charts into HTML templates

### PDF Generation Pipeline

1. **Data Collection**: Gather user profile, goals, and simulation data
2. **Template Rendering**: Process Jinja2 templates with financial data
3. **Chart Integration**: Embed generated charts as base64 images
4. **PDF Conversion**: Use WeasyPrint to convert HTML to PDF
5. **File Storage**: Save to temporary location with secure naming
6. **Job Update**: Update database with completion status and file path

### Template System

Templates located in `app/templates/pdf/`:
- `professional_plan.html` - Main professional format
- `detailed_plan.html` - Comprehensive detailed report
- CSS embedded with responsive design for PDF

## Performance Considerations

### Optimization Strategies

1. **Async Processing**: Long-running PDF generation doesn't block API
2. **Chart Caching**: Generated charts cached for reuse
3. **Template Compilation**: Jinja2 templates pre-compiled
4. **File Cleanup**: Automatic removal of expired files

### Scaling

- **Horizontal Scaling**: Multiple Celery workers for concurrent generation
- **Resource Management**: Memory limits and timeouts for PDF tasks
- **Queue Management**: Priority queues for different PDF types

### Performance Metrics

- Executive Summary: ~15 seconds
- Professional Report: ~30 seconds  
- Detailed Report: ~60 seconds
- Chart Generation: ~5-10 seconds per chart

## Error Handling

### Common Errors

1. **Missing Data**: Graceful degradation when financial data incomplete
2. **Chart Failures**: Fallback to placeholder charts
3. **Template Errors**: Fallback to basic HTML template
4. **File System Issues**: Error reporting with retry logic

### Error Recovery

- Automatic retry for transient failures
- Detailed error logging for debugging
- User-friendly error messages
- Fallback templates for missing data

## Monitoring & Logging

### Metrics Tracked

- PDF generation success/failure rates
- Generation time by format type
- Queue depth and processing times
- File storage usage and cleanup rates

### Logging

- Structured logging with correlation IDs
- Performance metrics logging
- Error tracking with context
- Audit trail for compliance

## Deployment

### Dependencies Installation

```bash
# Install system dependencies for WeasyPrint
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0

# Install Python dependencies
pip install -r requirements.txt
```

### Production Configuration

- Use Redis Cluster for high availability
- Configure file storage on shared filesystem
- Set up monitoring for queue health
- Configure backup for PDF jobs database

## Usage Examples

### Generate Professional Report

```python
import httpx

# Queue PDF generation
response = httpx.post("/api/v1/plan/123/export/pdf", json={
    "format_type": "professional",
    "include_charts": True,
    "include_projections": True
})

job_id = response.json()["job_id"]

# Check status
status_response = httpx.get(f"/api/v1/pdf/jobs/{job_id}")
if status_response.json()["status"] == "completed":
    # Download PDF
    pdf_response = httpx.get(f"/api/v1/pdf/download/{job_id}")
    with open("financial_plan.pdf", "wb") as f:
        f.write(pdf_response.content)
```

### Generate Immediate Executive Summary

```python
# Get PDF immediately (executive summary only)
response = httpx.post("/api/v1/plan/export/pdf/immediate", json={
    "format_type": "executive_summary"
})

with open("executive_summary.pdf", "wb") as f:
    f.write(response.content)
```

## Future Enhancements

### Planned Features

1. **Custom Branding**: White-label PDF generation with custom logos
2. **Multi-language Support**: International compliance and translations
3. **Advanced Charts**: Interactive charts with drill-down capabilities
4. **Email Integration**: Automatic PDF delivery via email
5. **Template Editor**: Admin interface for template customization

### Performance Improvements

1. **PDF Caching**: Cache generated PDFs for identical data
2. **Incremental Generation**: Update only changed sections
3. **Parallel Processing**: Generate charts in parallel
4. **CDN Integration**: Serve static assets from CDN

### Integration Opportunities

1. **CRM Integration**: Direct export to client management systems
2. **Document Management**: Integration with document storage systems
3. **E-signature**: Integrate with DocuSign or similar services
4. **Portfolio Management**: Real-time data from portfolio systems

## Troubleshooting

### Common Issues

1. **WeasyPrint Installation**: Ensure system dependencies installed
2. **Font Issues**: Configure font paths for consistent rendering
3. **Memory Usage**: Monitor memory for large PDFs with many charts
4. **Redis Connection**: Verify Redis connectivity for async processing

### Debug Mode

Enable debug mode for detailed error information:

```python
# Add to configuration
PDF_DEBUG_MODE = True
WEASYPRINT_DEBUG = True
```

This enables:
- Detailed error messages
- Intermediate file preservation
- Performance timing logs
- Template rendering debug info
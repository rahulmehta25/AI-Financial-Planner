"""
PDF Generator Service for Financial Planning Reports
Supports WeasyPrint and ReportLab for professional document generation
"""

import io
import os
import uuid
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor

import weasyprint
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from jinja2 import Environment, FileSystemLoader, Template
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chart_generator import ChartGeneratorService
from app.models.user import User
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal

logger = logging.getLogger(__name__)


class FinancialPlanData:
    """Data structure for financial plan PDF generation"""
    
    def __init__(
        self,
        user: User,
        financial_profile: FinancialProfile,
        goals: List[Goal],
        simulation_results: Optional[Dict] = None,
        ai_narrative: Optional[str] = None,
        recommendations: Optional[List[Dict]] = None
    ):
        self.user = user
        self.financial_profile = financial_profile
        self.goals = goals
        self.simulation_results = simulation_results or {}
        self.ai_narrative = ai_narrative or ""
        self.recommendations = recommendations or []
        self.generated_at = datetime.now()


class PDFGeneratorService:
    """Service for generating professional financial planning PDFs"""
    
    def __init__(self):
        self.chart_service = ChartGeneratorService()
        self.template_dir = Path(__file__).parent.parent / "templates" / "pdf"
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # Compliance and legal disclaimers
        self.compliance_disclaimer = """
        IMPORTANT DISCLAIMERS:
        
        This financial plan is for informational purposes only and does not constitute financial, 
        investment, or legal advice. The projections and analyses contained herein are based on 
        current information and assumptions that may change. Past performance does not guarantee 
        future results.
        
        All investments carry risk of loss. You should consult with qualified financial, tax, and 
        legal advisors before making any investment decisions. This document was generated using 
        automated analysis tools and artificial intelligence assistance.
        
        Generated on: {generation_date}
        Plan ID: {plan_id}
        User ID: {user_id}
        """
        
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def generate_comprehensive_plan_pdf(
        self,
        plan_data: FinancialPlanData,
        format_type: str = "professional"
    ) -> bytes:
        """Generate comprehensive financial plan PDF"""
        try:
            if format_type == "executive_summary":
                return await self._generate_executive_summary(plan_data)
            elif format_type == "detailed":
                return await self._generate_detailed_report(plan_data)
            else:  # professional (default)
                return await self._generate_professional_report(plan_data)
                
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            raise
    
    async def _generate_professional_report(self, plan_data: FinancialPlanData) -> bytes:
        """Generate professional one-page financial plan using WeasyPrint"""
        try:
            # Prepare chart data
            charts = await self._generate_all_charts(plan_data)
            
            # Prepare template context
            context = self._prepare_template_context(plan_data, charts)
            
            # Render HTML template
            html_content = await self._render_html_template("professional_plan.html", context)
            
            # Generate PDF using WeasyPrint
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                self.executor,
                self._weasyprint_to_pdf,
                html_content
            )
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating professional report: {e}")
            raise
    
    async def _generate_executive_summary(self, plan_data: FinancialPlanData) -> bytes:
        """Generate executive summary PDF using ReportLab"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build document content
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#2E86AB')
            )
            
            # Title
            story.append(Paragraph("Financial Plan Executive Summary", title_style))
            story.append(Spacer(1, 12))
            
            # Client information
            client_info = self._build_client_info_section(plan_data, styles)
            story.extend(client_info)
            
            # Key metrics table
            metrics_table = self._build_key_metrics_table(plan_data)
            story.append(metrics_table)
            story.append(Spacer(1, 12))
            
            # Goals summary
            goals_section = self._build_goals_summary(plan_data, styles)
            story.extend(goals_section)
            
            # Recommendations
            recommendations_section = self._build_recommendations_section(plan_data, styles)
            story.extend(recommendations_section)
            
            # Compliance disclaimer
            story.append(PageBreak())
            disclaimer = self._build_compliance_section(plan_data, styles)
            story.extend(disclaimer)
            
            # Build PDF
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                doc.build,
                story
            )
            
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            raise
    
    async def _generate_detailed_report(self, plan_data: FinancialPlanData) -> bytes:
        """Generate detailed multi-page report with charts"""
        try:
            # Generate charts
            charts = await self._generate_all_charts(plan_data)
            
            # Prepare comprehensive context
            context = self._prepare_detailed_context(plan_data, charts)
            
            # Render HTML template
            html_content = await self._render_html_template("detailed_plan.html", context)
            
            # Generate PDF
            loop = asyncio.get_event_loop()
            pdf_bytes = await loop.run_in_executor(
                self.executor,
                self._weasyprint_to_pdf,
                html_content
            )
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
            raise
    
    async def _generate_all_charts(self, plan_data: FinancialPlanData) -> Dict[str, str]:
        """Generate all charts needed for the PDF"""
        charts = {}
        
        try:
            # Net worth projection
            if plan_data.simulation_results.get('net_worth_projection'):
                charts['net_worth'] = self.chart_service.generate_net_worth_projection(
                    plan_data.simulation_results['net_worth_projection'],
                    plan_data.financial_profile.net_worth
                )
            
            # Goals progress
            if plan_data.goals:
                goals_data = [
                    {
                        'name': goal.name,
                        'progress_percentage': float(goal.progress_percentage or 0)
                    }
                    for goal in plan_data.goals
                ]
                charts['goals_progress'] = self.chart_service.generate_goal_progress_chart(goals_data)
            
            # Asset allocation
            allocation_data = self._calculate_asset_allocation(plan_data.financial_profile)
            if allocation_data:
                charts['asset_allocation'] = self.chart_service.generate_asset_allocation_pie(allocation_data)
            
            # Monte Carlo results
            if plan_data.simulation_results.get('monte_carlo'):
                charts['monte_carlo'] = self.chart_service.generate_monte_carlo_results(
                    plan_data.simulation_results['monte_carlo']
                )
            
            # Cash flow projection
            if plan_data.simulation_results.get('cash_flow'):
                charts['cash_flow'] = self.chart_service.generate_cash_flow_chart(
                    plan_data.simulation_results['cash_flow']
                )
            
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        return charts
    
    def _prepare_template_context(self, plan_data: FinancialPlanData, charts: Dict) -> Dict:
        """Prepare context for HTML template rendering"""
        fp = plan_data.financial_profile
        
        context = {
            'user': {
                'name': f"{plan_data.user.first_name} {plan_data.user.last_name}",
                'email': plan_data.user.email
            },
            'profile': {
                'age': fp.age,
                'annual_income': float(fp.annual_income),
                'net_worth': fp.net_worth,
                'risk_tolerance': fp.risk_tolerance.replace('_', ' ').title(),
                'investment_experience': fp.investment_experience.replace('_', ' ').title(),
                'employment_status': fp.employment_status.replace('_', ' ').title(),
                'debt_to_income_ratio': fp.debt_to_income_ratio
            },
            'goals': [
                {
                    'name': goal.name,
                    'target_amount': float(goal.target_amount),
                    'current_amount': float(goal.current_amount or 0),
                    'progress_percentage': float(goal.progress_percentage or 0),
                    'target_date': goal.target_date.strftime('%B %Y'),
                    'monthly_contribution': float(goal.monthly_contribution or 0),
                    'status': goal.progress_status
                }
                for goal in plan_data.goals
            ],
            'simulation': plan_data.simulation_results,
            'ai_narrative': plan_data.ai_narrative,
            'recommendations': plan_data.recommendations,
            'charts': charts,
            'generated_at': plan_data.generated_at.strftime('%B %d, %Y at %I:%M %p'),
            'plan_id': str(uuid.uuid4()),
            'compliance_disclaimer': self.compliance_disclaimer.format(
                generation_date=plan_data.generated_at.strftime('%B %d, %Y'),
                plan_id=str(uuid.uuid4()),
                user_id=str(plan_data.user.id)
            )
        }
        
        return context
    
    def _prepare_detailed_context(self, plan_data: FinancialPlanData, charts: Dict) -> Dict:
        """Prepare detailed context with additional analysis"""
        context = self._prepare_template_context(plan_data, charts)
        
        # Add detailed financial analysis
        fp = plan_data.financial_profile
        
        context['detailed_analysis'] = {
            'assets_breakdown': {
                'liquid_assets': float(fp.liquid_assets or 0),
                'retirement_accounts': float(fp.retirement_accounts or 0),
                'real_estate': float(fp.real_estate_value or 0),
                'other_investments': float(fp.other_investments or 0),
                'personal_property': float(fp.personal_property_value or 0)
            },
            'liabilities_breakdown': {
                'mortgage': float(fp.mortgage_balance or 0),
                'credit_cards': float(fp.credit_card_debt or 0),
                'student_loans': float(fp.student_loans or 0),
                'auto_loans': float(fp.auto_loans or 0),
                'other_debts': float(fp.other_debts or 0)
            },
            'monthly_cash_flow': {
                'income': float(fp.annual_income / 12),
                'expenses': float(fp.monthly_expenses or 0),
                'surplus': float(fp.annual_income / 12) - float(fp.monthly_expenses or 0)
            }
        }
        
        return context
    
    async def _render_html_template(self, template_name: str, context: Dict) -> str:
        """Render HTML template with context"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            # Fallback to basic template
            return self._generate_fallback_html(context)
    
    def _weasyprint_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF using WeasyPrint"""
        try:
            css_content = self._get_pdf_css()
            html = weasyprint.HTML(string=html_content)
            css = weasyprint.CSS(string=css_content)
            
            return html.write_pdf(stylesheets=[css])
            
        except Exception as e:
            logger.error(f"Error converting HTML to PDF: {e}")
            raise
    
    def _calculate_asset_allocation(self, fp: FinancialProfile) -> Dict[str, float]:
        """Calculate asset allocation percentages"""
        try:
            total_assets = (
                float(fp.liquid_assets or 0) +
                float(fp.retirement_accounts or 0) +
                float(fp.real_estate_value or 0) +
                float(fp.other_investments or 0)
            )
            
            if total_assets == 0:
                return {}
            
            return {
                'Cash & Savings': float(fp.liquid_assets or 0),
                'Retirement Accounts': float(fp.retirement_accounts or 0),
                'Real Estate': float(fp.real_estate_value or 0),
                'Other Investments': float(fp.other_investments or 0)
            }
            
        except Exception as e:
            logger.error(f"Error calculating asset allocation: {e}")
            return {}
    
    def _build_client_info_section(self, plan_data: FinancialPlanData, styles) -> List:
        """Build client information section for ReportLab"""
        story = []
        
        client_style = ParagraphStyle(
            'ClientInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6
        )
        
        story.append(Paragraph(f"<b>Client:</b> {plan_data.user.first_name} {plan_data.user.last_name}", client_style))
        story.append(Paragraph(f"<b>Age:</b> {plan_data.financial_profile.age}", client_style))
        story.append(Paragraph(f"<b>Risk Tolerance:</b> {plan_data.financial_profile.risk_tolerance.title()}", client_style))
        story.append(Paragraph(f"<b>Generated:</b> {plan_data.generated_at.strftime('%B %d, %Y')}", client_style))
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_key_metrics_table(self, plan_data: FinancialPlanData) -> Table:
        """Build key financial metrics table"""
        fp = plan_data.financial_profile
        
        data = [
            ['Metric', 'Value'],
            ['Annual Income', f"${float(fp.annual_income):,.0f}"],
            ['Net Worth', f"${fp.net_worth:,.0f}"],
            ['Monthly Expenses', f"${float(fp.monthly_expenses or 0):,.0f}"],
            ['Debt-to-Income Ratio', f"{fp.debt_to_income_ratio:.1%}"]
        ]
        
        table = Table(data, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E86AB')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        return table
    
    def _build_goals_summary(self, plan_data: FinancialPlanData, styles) -> List:
        """Build goals summary section"""
        story = []
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2E86AB')
        )
        
        story.append(Paragraph("Financial Goals Summary", heading_style))
        
        for goal in plan_data.goals[:3]:  # Show top 3 goals
            goal_text = f"<b>{goal.name}:</b> ${float(goal.target_amount):,.0f} target by {goal.target_date.strftime('%B %Y')} ({float(goal.progress_percentage or 0):.1f}% complete)"
            story.append(Paragraph(goal_text, styles['Normal']))
        
        story.append(Spacer(1, 12))
        return story
    
    def _build_recommendations_section(self, plan_data: FinancialPlanData, styles) -> List:
        """Build recommendations section"""
        story = []
        
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2E86AB')
        )
        
        story.append(Paragraph("Key Recommendations", heading_style))
        
        # Add AI narrative if available
        if plan_data.ai_narrative:
            story.append(Paragraph(plan_data.ai_narrative, styles['Normal']))
        
        # Add structured recommendations
        for i, rec in enumerate(plan_data.recommendations[:5], 1):
            rec_text = f"{i}. <b>{rec.get('title', 'Recommendation')}:</b> {rec.get('description', '')}"
            story.append(Paragraph(rec_text, styles['Normal']))
        
        story.append(Spacer(1, 12))
        return story
    
    def _build_compliance_section(self, plan_data: FinancialPlanData, styles) -> List:
        """Build compliance and disclaimer section"""
        story = []
        
        disclaimer_style = ParagraphStyle(
            'Disclaimer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_JUSTIFY
        )
        
        disclaimer_text = self.compliance_disclaimer.format(
            generation_date=plan_data.generated_at.strftime('%B %d, %Y'),
            plan_id=str(uuid.uuid4()),
            user_id=str(plan_data.user.id)
        )
        
        story.append(Paragraph("COMPLIANCE DISCLAIMER", styles['Heading3']))
        story.append(Paragraph(disclaimer_text, disclaimer_style))
        
        return story
    
    def _get_pdf_css(self) -> str:
        """Get CSS styles for PDF generation"""
        return """
        @page {
            size: A4;
            margin: 1in;
            @bottom-right {
                content: "Page " counter(page);
                font-size: 10px;
                color: #666;
            }
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #2E86AB;
            padding-bottom: 20px;
        }
        
        .title {
            font-size: 24px;
            font-weight: bold;
            color: #2E86AB;
            margin-bottom: 10px;
        }
        
        .subtitle {
            font-size: 14px;
            color: #666;
        }
        
        .section {
            margin-bottom: 25px;
        }
        
        .section-title {
            font-size: 16px;
            font-weight: bold;
            color: #2E86AB;
            margin-bottom: 10px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric-box {
            border: 1px solid #ddd;
            padding: 15px;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        
        .metric-label {
            font-weight: bold;
            color: #666;
            font-size: 11px;
            text-transform: uppercase;
        }
        
        .metric-value {
            font-size: 18px;
            font-weight: bold;
            color: #2E86AB;
            margin-top: 5px;
        }
        
        .chart-container {
            text-align: center;
            margin: 20px 0;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
        }
        
        .goals-list {
            margin: 15px 0;
        }
        
        .goal-item {
            border-left: 3px solid #2E86AB;
            padding-left: 15px;
            margin-bottom: 10px;
        }
        
        .progress-bar {
            background-color: #f0f0f0;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 5px;
        }
        
        .progress-fill {
            background-color: #2E86AB;
            height: 100%;
            border-radius: 10px;
        }
        
        .disclaimer {
            font-size: 8px;
            color: #666;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #2E86AB;
            color: white;
            font-weight: bold;
        }
        
        .recommendations {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        
        .recommendation-item {
            margin-bottom: 15px;
            padding-left: 20px;
            position: relative;
        }
        
        .recommendation-item::before {
            content: "→";
            position: absolute;
            left: 0;
            color: #2E86AB;
            font-weight: bold;
        }
        """
    
    def _generate_fallback_html(self, context: Dict) -> str:
        """Generate fallback HTML when templates fail"""
        user_name = context.get('user', {}).get('name', 'Client')
        generated_at = context.get('generated_at', datetime.now().strftime('%B %d, %Y'))
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Financial Plan - {user_name}</title>
        </head>
        <body>
            <div class="header">
                <h1 class="title">Financial Planning Report</h1>
                <p class="subtitle">Prepared for {user_name} on {generated_at}</p>
            </div>
            
            <div class="section">
                <h2 class="section-title">Executive Summary</h2>
                <p>This is a fallback financial plan report. Please ensure templates are properly configured.</p>
            </div>
            
            <div class="disclaimer">
                {context.get('compliance_disclaimer', '')}
            </div>
        </body>
        </html>
        """
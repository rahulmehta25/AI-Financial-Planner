"""
PDF Generation and Download Integration Tests

This module tests comprehensive PDF generation and delivery functionality:
- Financial plan PDF generation
- Report customization and templating
- PDF queue processing and management
- Download delivery and security
- Multi-format export capabilities
- Performance and scalability testing
- Error handling and recovery
"""
import asyncio
import io
import json
import time
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from httpx import AsyncClient
from PyPDF2 import PdfReader
import base64

from tests.integration.base import FullStackIntegrationTest, integration_test_context
from tests.factories import UserFactory, create_complete_user_scenario


class TestPDFGenerationIntegration(FullStackIntegrationTest):
    """Test comprehensive PDF generation and delivery system."""
    
    def __init__(self):
        super().__init__()
        self.pdf_generation_tracking = []
        self.download_tracking = []
    
    async def setup_test_environment(self) -> Dict[str, Any]:
        """Set up PDF generation testing environment."""
        config = await super().setup_test_environment()
        
        config.update({
            'pdf_testing': True,
            'pdf_storage_path': '/tmp/test_pdfs',
            'pdf_queue_testing': True
        })
        
        return config
    
    async def test_complete_financial_plan_pdf_generation(self):
        """Test complete financial plan PDF generation from simulation to download."""
        async with integration_test_context(self) as config:
            
            # Create user with complete financial scenario
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            
            # Step 1: Generate simulation data
            simulation_result = await self.measure_operation(
                lambda: self._generate_simulation_for_pdf(user_data),
                "simulation_generation"
            )
            
            # Step 2: Generate professional PDF report
            await self.measure_operation(
                lambda: self._test_professional_pdf_generation(user_data, simulation_result),
                "professional_pdf_generation"
            )
            
            # Step 3: Generate detailed analysis PDF
            await self.measure_operation(
                lambda: self._test_detailed_analysis_pdf(user_data, simulation_result),
                "detailed_analysis_pdf"
            )
            
            # Step 4: Test PDF customization options
            await self.measure_operation(
                lambda: self._test_pdf_customization_options(user_data, simulation_result),
                "pdf_customization"
            )
            
            # Step 5: Test PDF download and delivery
            await self.measure_operation(
                lambda: self._test_pdf_download_delivery(user_data),
                "pdf_download_delivery"
            )
            
            # Verify complete PDF generation workflow
            await self._verify_complete_pdf_workflow(user_data)
    
    async def test_pdf_queue_processing(self):
        """Test PDF queue processing for high-volume generation."""
        async with integration_test_context(self) as config:
            
            # Create multiple users with simulation data
            users_with_simulations = []
            for i in range(10):
                scenario = await self._create_complete_financial_scenario()
                simulation = await self._generate_simulation_for_pdf(scenario['user'])
                users_with_simulations.append({
                    'user': scenario['user'],
                    'simulation': simulation
                })
            
            # Queue multiple PDF generation requests
            await self.measure_operation(
                lambda: self._test_bulk_pdf_queue_processing(users_with_simulations),
                "bulk_pdf_queue_processing"
            )
            
            # Test queue management and prioritization
            await self.measure_operation(
                lambda: self._test_pdf_queue_management(),
                "pdf_queue_management"
            )
            
            # Test queue monitoring and status tracking
            await self.measure_operation(
                lambda: self._test_pdf_queue_monitoring(),
                "pdf_queue_monitoring"
            )
    
    async def test_pdf_template_customization(self):
        """Test PDF template customization and branding."""
        async with integration_test_context(self) as config:
            
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            simulation = await self._generate_simulation_for_pdf(user_data)
            
            # Test custom branding
            await self.measure_operation(
                lambda: self._test_custom_branding_pdf(user_data, simulation),
                "custom_branding_pdf"
            )
            
            # Test template variations
            await self.measure_operation(
                lambda: self._test_template_variations(user_data, simulation),
                "template_variations"
            )
            
            # Test dynamic content insertion
            await self.measure_operation(
                lambda: self._test_dynamic_content_insertion(user_data, simulation),
                "dynamic_content_insertion"
            )
            
            # Test multi-language PDF generation
            await self.measure_operation(
                lambda: self._test_multilingual_pdf_generation(user_data, simulation),
                "multilingual_pdf_generation"
            )
    
    async def test_pdf_security_and_permissions(self):
        """Test PDF security features and access permissions."""
        async with integration_test_context(self) as config:
            
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            simulation = await self._generate_simulation_for_pdf(user_data)
            
            # Test password protection
            await self.measure_operation(
                lambda: self._test_password_protected_pdf(user_data, simulation),
                "password_protected_pdf"
            )
            
            # Test watermarking
            await self.measure_operation(
                lambda: self._test_pdf_watermarking(user_data, simulation),
                "pdf_watermarking"
            )
            
            # Test access control
            await self.measure_operation(
                lambda: self._test_pdf_access_control(user_data),
                "pdf_access_control"
            )
            
            # Test audit trail for PDF access
            await self.measure_operation(
                lambda: self._test_pdf_access_audit_trail(user_data),
                "pdf_access_audit_trail"
            )
    
    async def test_multi_format_export(self):
        """Test multi-format export capabilities."""
        async with integration_test_context(self) as config:
            
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            simulation = await self._generate_simulation_for_pdf(user_data)
            
            # Test Excel export
            await self.measure_operation(
                lambda: self._test_excel_export(user_data, simulation),
                "excel_export"
            )
            
            # Test CSV export
            await self.measure_operation(
                lambda: self._test_csv_export(user_data, simulation),
                "csv_export"
            )
            
            # Test PowerPoint export
            await self.measure_operation(
                lambda: self._test_powerpoint_export(user_data, simulation),
                "powerpoint_export"
            )
            
            # Test interactive HTML report
            await self.measure_operation(
                lambda: self._test_interactive_html_report(user_data, simulation),
                "interactive_html_report"
            )
    
    async def test_pdf_delivery_channels(self):
        """Test PDF delivery through various channels."""
        async with integration_test_context(self) as config:
            
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            
            # Generate PDF first
            pdf_result = await self._test_professional_pdf_generation(user_data, {})
            
            # Test email delivery
            await self.measure_operation(
                lambda: self._test_pdf_email_delivery(user_data, pdf_result),
                "pdf_email_delivery"
            )
            
            # Test cloud storage delivery
            await self.measure_operation(
                lambda: self._test_pdf_cloud_storage_delivery(user_data, pdf_result),
                "pdf_cloud_storage_delivery"
            )
            
            # Test API download
            await self.measure_operation(
                lambda: self._test_pdf_api_download(user_data, pdf_result),
                "pdf_api_download"
            )
            
            # Test mobile app integration
            await self.measure_operation(
                lambda: self._test_pdf_mobile_app_delivery(user_data, pdf_result),
                "pdf_mobile_app_delivery"
            )
    
    async def test_pdf_error_handling_and_recovery(self):
        """Test PDF generation error handling and recovery."""
        async with integration_test_context(self) as config:
            
            scenario = await self._create_complete_financial_scenario()
            user_data = scenario['user']
            
            # Test template rendering errors
            await self.measure_operation(
                lambda: self._test_template_rendering_error_handling(user_data),
                "template_rendering_error_handling"
            )
            
            # Test data validation errors
            await self.measure_operation(
                lambda: self._test_pdf_data_validation_errors(user_data),
                "pdf_data_validation_errors"
            )
            
            # Test storage failures
            await self.measure_operation(
                lambda: self._test_pdf_storage_failure_handling(user_data),
                "pdf_storage_failure_handling"
            )
            
            # Test recovery mechanisms
            await self.measure_operation(
                lambda: self._test_pdf_generation_recovery(user_data),
                "pdf_generation_recovery"
            )
    
    # Helper methods for PDF generation testing
    
    async def _create_complete_financial_scenario(self) -> Dict[str, Any]:
        """Create a complete financial scenario for PDF testing."""
        # Create user
        user_data = {
            "email": "pdf_test@example.com",
            "password": "PDFTest123!",
            "first_name": "PDF",
            "last_name": "Tester"
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        # Authenticate
        login_data = {"username": user_data["email"], "password": user_data["password"]}
        response = await self.client.post("/api/v1/auth/login", data=login_data)
        token_data = response.json()
        
        user_data['id'] = response.json()['id']
        user_data['auth_token'] = token_data["access_token"]
        
        # Create financial profile
        profile_data = {
            "annual_income": 85000.0,
            "monthly_expenses": 5500.0,
            "current_savings": 45000.0,
            "current_debt": 25000.0,
            "risk_tolerance": "moderate",
            "investment_timeline": 25
        }
        
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        response = await self.client.post(
            "/api/v1/financial-profiles/",
            json=profile_data,
            headers=headers
        )
        assert response.status_code == 201
        profile = response.json()
        
        # Create goals
        goals_data = [
            {
                "name": "Retirement Planning",
                "goal_type": "retirement",
                "target_amount": 1200000.0,
                "target_date": "2050-01-01",
                "priority": "high"
            },
            {
                "name": "House Down Payment",
                "goal_type": "major_purchase",
                "target_amount": 80000.0,
                "target_date": "2030-01-01",
                "priority": "medium"
            }
        ]
        
        goals = []
        for goal_data in goals_data:
            response = await self.client.post(
                "/api/v1/goals/",
                json=goal_data,
                headers=headers
            )
            assert response.status_code == 201
            goals.append(response.json())
        
        return {
            'user': user_data,
            'profile': profile,
            'goals': goals
        }
    
    async def _generate_simulation_for_pdf(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate simulation data for PDF testing."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        simulation_data = {
            "simulation_type": "comprehensive_planning",
            "time_horizon": 25,
            "monte_carlo_runs": 1000,
            "include_goals": True,
            "include_tax_optimization": True,
            "scenario_analysis": True
        }
        
        response = await self.client.post(
            "/api/v1/simulations/run",
            json=simulation_data,
            headers=headers
        )
        assert response.status_code == 202
        
        simulation_id = response.json()["simulation_id"]
        
        # Wait for completion (simplified for testing)
        await asyncio.sleep(2)
        
        response = await self.client.get(
            f"/api/v1/simulations/{simulation_id}",
            headers=headers
        )
        assert response.status_code == 200
        
        return response.json()
    
    async def _test_professional_pdf_generation(self, user_data: Dict[str, Any], simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test professional PDF report generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        pdf_request = {
            "template": "professional_plan",
            "simulation_id": simulation_result.get('id'),
            "include_sections": [
                "executive_summary",
                "current_situation",
                "recommendations",
                "projections",
                "appendix"
            ],
            "customization": {
                "include_charts": True,
                "include_assumptions": True,
                "include_disclaimers": True
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=pdf_request,
            headers=headers
        )
        assert response.status_code == 202  # Async generation
        
        pdf_job = response.json()
        assert 'job_id' in pdf_job
        assert 'estimated_completion' in pdf_job
        
        # Wait for PDF generation
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        # Verify PDF was generated
        assert pdf_result['status'] == 'completed'
        assert 'download_url' in pdf_result
        assert 'file_size' in pdf_result
        
        self.pdf_generation_tracking.append({
            'user_id': user_data['id'],
            'template': 'professional_plan',
            'job_id': pdf_job['job_id'],
            'file_size': pdf_result['file_size'],
            'generation_time': pdf_result.get('generation_time', 0)
        })
        
        return pdf_result
    
    async def _test_detailed_analysis_pdf(self, user_data: Dict[str, Any], simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test detailed analysis PDF generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        pdf_request = {
            "template": "detailed_analysis",
            "simulation_id": simulation_result.get('id'),
            "include_sections": [
                "methodology",
                "detailed_projections",
                "sensitivity_analysis",
                "risk_analysis",
                "optimization_suggestions",
                "technical_appendix"
            ],
            "customization": {
                "include_raw_data": True,
                "include_calculations": True,
                "include_monte_carlo_details": True,
                "chart_style": "detailed"
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=pdf_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        # Detailed PDF should be larger
        assert pdf_result['file_size'] > 500000  # At least 500KB
        
        return pdf_result
    
    async def _test_pdf_customization_options(self, user_data: Dict[str, Any], simulation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test PDF customization options."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test custom styling
        customization_request = {
            "template": "professional_plan",
            "simulation_id": simulation_result.get('id'),
            "customization": {
                "color_scheme": "blue_corporate",
                "logo_url": "https://example.com/logo.png",
                "footer_text": "Custom Financial Planning Report",
                "font_family": "Arial",
                "include_cover_page": True,
                "cover_page_title": "Custom Financial Plan",
                "include_table_of_contents": True,
                "page_numbering": True,
                "watermark": "CONFIDENTIAL"
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=customization_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        # Verify customization was applied
        assert pdf_result['status'] == 'completed'
        assert 'customization_applied' in pdf_result
        
        return pdf_result
    
    async def _test_pdf_download_delivery(self, user_data: Dict[str, Any]) -> bool:
        """Test PDF download and delivery mechanisms."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Get list of generated PDFs
        response = await self.client.get(
            "/api/v1/pdf/list",
            headers=headers
        )
        assert response.status_code == 200
        
        pdf_list = response.json()
        assert len(pdf_list) > 0
        
        # Test direct download
        pdf_id = pdf_list[0]['id']
        response = await self.client.get(
            f"/api/v1/pdf/{pdf_id}/download",
            headers=headers
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        
        # Verify PDF content is valid
        pdf_content = response.content
        assert len(pdf_content) > 1000  # Should be substantial content
        assert pdf_content.startswith(b'%PDF')  # PDF magic number
        
        # Test PDF validation
        try:
            pdf_reader = PdfReader(io.BytesIO(pdf_content))
            assert len(pdf_reader.pages) > 0
        except Exception as e:
            pytest.fail(f"Invalid PDF generated: {e}")
        
        self.download_tracking.append({
            'user_id': user_data['id'],
            'pdf_id': pdf_id,
            'download_size': len(pdf_content),
            'download_timestamp': time.time()
        })
        
        return True
    
    async def _test_bulk_pdf_queue_processing(self, users_with_simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test bulk PDF queue processing."""
        # Queue multiple PDF generation requests
        job_ids = []
        
        for user_sim in users_with_simulations:
            user_data = user_sim['user']
            headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
            
            pdf_request = {
                "template": "professional_plan",
                "simulation_id": user_sim['simulation'].get('id'),
                "priority": "normal"
            }
            
            response = await self.client.post(
                "/api/v1/pdf/generate",
                json=pdf_request,
                headers=headers
            )
            assert response.status_code == 202
            
            job_ids.append(response.json()['job_id'])
        
        # Monitor queue processing
        start_time = time.time()
        completed_jobs = 0
        
        while completed_jobs < len(job_ids) and (time.time() - start_time) < 120:  # 2 minute timeout
            # Check queue status
            response = await self.client.get("/api/v1/pdf/queue/status")
            assert response.status_code == 200
            
            queue_status = response.json()
            completed_jobs = queue_status.get('completed_jobs', 0)
            
            await asyncio.sleep(2)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # All jobs should complete within reasonable time
        assert completed_jobs == len(job_ids), f"Only {completed_jobs}/{len(job_ids)} jobs completed"
        assert processing_time < 120, f"Queue processing took {processing_time:.2f}s, expected < 120s"
        
        return {
            'jobs_processed': completed_jobs,
            'processing_time': processing_time,
            'jobs_per_second': completed_jobs / processing_time
        }
    
    async def _test_pdf_queue_management(self) -> Dict[str, Any]:
        """Test PDF queue management and prioritization."""
        # Test queue statistics
        response = await self.client.get("/api/v1/pdf/queue/stats")
        assert response.status_code == 200
        
        queue_stats = response.json()
        assert 'pending_jobs' in queue_stats
        assert 'processing_jobs' in queue_stats
        assert 'completed_jobs' in queue_stats
        assert 'failed_jobs' in queue_stats
        
        # Test queue priority management
        priority_request = {
            "action": "set_priority",
            "job_ids": ["job_123", "job_456"],
            "priority": "high"
        }
        
        response = await self.client.post(
            "/api/v1/pdf/queue/manage",
            json=priority_request
        )
        assert response.status_code == 200
        
        return queue_stats
    
    async def _test_pdf_queue_monitoring(self) -> Dict[str, Any]:
        """Test PDF queue monitoring capabilities."""
        # Test real-time queue monitoring
        response = await self.client.get("/api/v1/pdf/queue/monitor")
        assert response.status_code == 200
        
        monitor_data = response.json()
        assert 'queue_length' in monitor_data
        assert 'processing_rate' in monitor_data
        assert 'average_processing_time' in monitor_data
        assert 'worker_status' in monitor_data
        
        # Test queue health check
        response = await self.client.get("/api/v1/pdf/queue/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert 'status' in health_data
        assert health_data['status'] in ['healthy', 'degraded', 'unhealthy']
        
        return monitor_data
    
    async def _test_custom_branding_pdf(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test custom branding in PDF generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        branding_request = {
            "template": "professional_plan",
            "simulation_id": simulation.get('id'),
            "branding": {
                "company_name": "Custom Financial Advisors",
                "company_logo": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                "color_primary": "#1f4e79",
                "color_secondary": "#71a5d4",
                "footer_contact": "contact@customfinancial.com | (555) 123-4567",
                "disclaimer": "Custom disclaimer text for this financial plan."
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=branding_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        # Verify branding was applied
        assert pdf_result['status'] == 'completed'
        assert 'branding_applied' in pdf_result
        
        return pdf_result
    
    async def _test_template_variations(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Test different PDF template variations."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        templates = [
            {
                "name": "executive_summary",
                "description": "High-level executive summary"
            },
            {
                "name": "detailed_technical",
                "description": "Technical analysis with detailed calculations"
            },
            {
                "name": "client_presentation",
                "description": "Client-friendly presentation format"
            }
        ]
        
        template_results = []
        
        for template in templates:
            pdf_request = {
                "template": template["name"],
                "simulation_id": simulation.get('id'),
                "description": template["description"]
            }
            
            response = await self.client.post(
                "/api/v1/pdf/generate",
                json=pdf_request,
                headers=headers
            )
            assert response.status_code == 202
            
            pdf_job = response.json()
            pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
            
            template_results.append({
                'template': template["name"],
                'result': pdf_result
            })
        
        # Verify all templates generated successfully
        for result in template_results:
            assert result['result']['status'] == 'completed'
        
        return template_results
    
    async def _test_dynamic_content_insertion(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test dynamic content insertion in PDFs."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        dynamic_content_request = {
            "template": "professional_plan",
            "simulation_id": simulation.get('id'),
            "dynamic_content": {
                "custom_sections": [
                    {
                        "title": "Market Commentary",
                        "content": "Current market conditions suggest...",
                        "position": "after_executive_summary"
                    },
                    {
                        "title": "Special Considerations",
                        "content": "Based on your unique situation...",
                        "position": "before_recommendations"
                    }
                ],
                "custom_charts": [
                    {
                        "type": "custom_projection",
                        "data": {"years": [2024, 2025, 2026], "values": [100000, 110000, 125000]},
                        "title": "Custom Investment Projection"
                    }
                ]
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=dynamic_content_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        assert pdf_result['status'] == 'completed'
        assert 'dynamic_content_inserted' in pdf_result
        
        return pdf_result
    
    async def _test_multilingual_pdf_generation(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test multi-language PDF generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        languages = ['en', 'es', 'fr']
        language_results = []
        
        for language in languages:
            pdf_request = {
                "template": "professional_plan",
                "simulation_id": simulation.get('id'),
                "language": language,
                "localization": {
                    "currency": "USD" if language == 'en' else "EUR",
                    "date_format": "MM/DD/YYYY" if language == 'en' else "DD/MM/YYYY",
                    "number_format": "US" if language == 'en' else "EU"
                }
            }
            
            response = await self.client.post(
                "/api/v1/pdf/generate",
                json=pdf_request,
                headers=headers
            )
            assert response.status_code == 202
            
            pdf_job = response.json()
            pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
            
            language_results.append({
                'language': language,
                'result': pdf_result
            })
        
        # Verify all languages generated successfully
        for result in language_results:
            assert result['result']['status'] == 'completed'
        
        return language_results[0]['result']  # Return first result for consistency
    
    async def _test_password_protected_pdf(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test password-protected PDF generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        protected_pdf_request = {
            "template": "professional_plan",
            "simulation_id": simulation.get('id'),
            "security": {
                "password_protection": True,
                "user_password": "client123",
                "owner_password": "admin456",
                "permissions": {
                    "allow_printing": True,
                    "allow_copying": False,
                    "allow_modification": False,
                    "allow_annotation": False
                }
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=protected_pdf_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        assert pdf_result['status'] == 'completed'
        assert 'password_protected' in pdf_result
        assert pdf_result['password_protected'] == True
        
        return pdf_result
    
    async def _test_pdf_watermarking(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test PDF watermarking functionality."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        watermark_request = {
            "template": "professional_plan",
            "simulation_id": simulation.get('id'),
            "watermark": {
                "text": "CONFIDENTIAL - DRAFT",
                "opacity": 0.3,
                "position": "diagonal",
                "color": "#FF0000",
                "font_size": 48
            }
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=watermark_request,
            headers=headers
        )
        assert response.status_code == 202
        
        pdf_job = response.json()
        pdf_result = await self._wait_for_pdf_completion(pdf_job['job_id'], headers)
        
        assert pdf_result['status'] == 'completed'
        assert 'watermark_applied' in pdf_result
        
        return pdf_result
    
    async def _test_pdf_access_control(self, user_data: Dict[str, Any]) -> bool:
        """Test PDF access control mechanisms."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Get PDF list
        response = await self.client.get(
            "/api/v1/pdf/list",
            headers=headers
        )
        assert response.status_code == 200
        
        pdf_list = response.json()
        if not pdf_list:
            return True  # No PDFs to test access control
        
        pdf_id = pdf_list[0]['id']
        
        # Test access with valid user
        response = await self.client.get(
            f"/api/v1/pdf/{pdf_id}/download",
            headers=headers
        )
        assert response.status_code == 200
        
        # Test access without authentication
        response = await self.client.get(f"/api/v1/pdf/{pdf_id}/download")
        assert response.status_code == 401
        
        # Test access with different user (should fail)
        other_user_headers = {"Authorization": "Bearer invalid_token"}
        response = await self.client.get(
            f"/api/v1/pdf/{pdf_id}/download",
            headers=other_user_headers
        )
        assert response.status_code == 401
        
        return True
    
    async def _test_pdf_access_audit_trail(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test PDF access audit trail."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Access a PDF to generate audit trail
        response = await self.client.get(
            "/api/v1/pdf/list",
            headers=headers
        )
        pdf_list = response.json()
        
        if pdf_list:
            pdf_id = pdf_list[0]['id']
            
            # Download PDF (should be audited)
            response = await self.client.get(
                f"/api/v1/pdf/{pdf_id}/download",
                headers=headers
            )
            assert response.status_code == 200
        
        # Check audit trail
        response = await self.client.get(
            "/api/v1/pdf/audit/access-logs",
            headers=headers
        )
        assert response.status_code == 200
        
        audit_logs = response.json()
        assert 'logs' in audit_logs
        
        if pdf_list:
            # Should have audit entry for download
            download_logs = [log for log in audit_logs['logs'] if log.get('action') == 'download']
            assert len(download_logs) > 0
        
        return audit_logs
    
    async def _test_excel_export(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test Excel export functionality."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        excel_request = {
            "format": "excel",
            "simulation_id": simulation.get('id'),
            "include_sheets": [
                "summary",
                "projections",
                "cash_flow",
                "assumptions"
            ]
        }
        
        response = await self.client.post(
            "/api/v1/export/excel",
            json=excel_request,
            headers=headers
        )
        assert response.status_code == 202
        
        export_job = response.json()
        export_result = await self._wait_for_export_completion(export_job['job_id'], headers)
        
        assert export_result['status'] == 'completed'
        assert export_result['format'] == 'excel'
        
        return export_result
    
    async def _test_csv_export(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test CSV export functionality."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        csv_request = {
            "format": "csv",
            "simulation_id": simulation.get('id'),
            "data_sets": [
                "monthly_projections",
                "goal_progress",
                "transactions_summary"
            ]
        }
        
        response = await self.client.post(
            "/api/v1/export/csv",
            json=csv_request,
            headers=headers
        )
        assert response.status_code == 202
        
        export_job = response.json()
        export_result = await self._wait_for_export_completion(export_job['job_id'], headers)
        
        assert export_result['status'] == 'completed'
        assert export_result['format'] == 'csv'
        
        return export_result
    
    async def _test_powerpoint_export(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test PowerPoint export functionality."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        ppt_request = {
            "format": "powerpoint",
            "simulation_id": simulation.get('id'),
            "presentation_type": "client_summary",
            "slide_count": 15
        }
        
        response = await self.client.post(
            "/api/v1/export/powerpoint",
            json=ppt_request,
            headers=headers
        )
        assert response.status_code == 202
        
        export_job = response.json()
        export_result = await self._wait_for_export_completion(export_job['job_id'], headers)
        
        assert export_result['status'] == 'completed'
        assert export_result['format'] == 'powerpoint'
        
        return export_result
    
    async def _test_interactive_html_report(self, user_data: Dict[str, Any], simulation: Dict[str, Any]) -> Dict[str, Any]:
        """Test interactive HTML report generation."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        html_request = {
            "format": "interactive_html",
            "simulation_id": simulation.get('id'),
            "features": [
                "interactive_charts",
                "scenario_sliders",
                "goal_tracking",
                "responsive_design"
            ]
        }
        
        response = await self.client.post(
            "/api/v1/export/html",
            json=html_request,
            headers=headers
        )
        assert response.status_code == 202
        
        export_job = response.json()
        export_result = await self._wait_for_export_completion(export_job['job_id'], headers)
        
        assert export_result['status'] == 'completed'
        assert export_result['format'] == 'interactive_html'
        assert 'view_url' in export_result
        
        return export_result
    
    async def _wait_for_pdf_completion(self, job_id: str, headers: Dict[str, str], timeout: int = 60) -> Dict[str, Any]:
        """Wait for PDF generation to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self.client.get(
                f"/api/v1/pdf/status/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') in ['completed', 'failed']:
                    return result
            
            await asyncio.sleep(1)
        
        raise TimeoutError(f"PDF generation {job_id} did not complete within {timeout} seconds")
    
    async def _wait_for_export_completion(self, job_id: str, headers: Dict[str, str], timeout: int = 60) -> Dict[str, Any]:
        """Wait for export to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self.client.get(
                f"/api/v1/export/status/{job_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') in ['completed', 'failed']:
                    return result
            
            await asyncio.sleep(1)
        
        raise TimeoutError(f"Export {job_id} did not complete within {timeout} seconds")
    
    async def _verify_complete_pdf_workflow(self, user_data: Dict[str, Any]):
        """Verify complete PDF generation workflow."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Verify PDFs were generated
        response = await self.client.get(
            "/api/v1/pdf/list",
            headers=headers
        )
        assert response.status_code == 200
        
        pdf_list = response.json()
        assert len(pdf_list) > 0
        
        # Verify tracking data
        assert len(self.pdf_generation_tracking) > 0
        assert len(self.download_tracking) > 0
        
        # Verify at least one successful download
        successful_downloads = [d for d in self.download_tracking if d['download_size'] > 0]
        assert len(successful_downloads) > 0
        
        return True
    
    # Additional helper methods for delivery and error testing...
    
    async def _test_pdf_email_delivery(self, user_data: Dict[str, Any], pdf_result: Dict[str, Any]) -> bool:
        """Test PDF delivery via email."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        email_delivery_request = {
            "pdf_id": pdf_result.get('id', 'test_pdf_id'),
            "delivery_method": "email",
            "recipient": user_data['email'],
            "subject": "Your Financial Plan is Ready",
            "message": "Please find your personalized financial plan attached."
        }
        
        with patch('app.services.notifications.email_service.EmailService.send_with_attachment') as mock_send:
            mock_send.return_value = {'status': 'sent', 'message_id': 'email_123'}
            
            response = await self.client.post(
                "/api/v1/pdf/deliver",
                json=email_delivery_request,
                headers=headers
            )
            assert response.status_code == 200
            
            # Verify email was sent
            mock_send.assert_called_once()
        
        return True
    
    async def _test_pdf_cloud_storage_delivery(self, user_data: Dict[str, Any], pdf_result: Dict[str, Any]) -> bool:
        """Test PDF delivery to cloud storage."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        cloud_delivery_request = {
            "pdf_id": pdf_result.get('id', 'test_pdf_id'),
            "delivery_method": "cloud_storage",
            "storage_provider": "s3",
            "bucket": "user-documents",
            "folder": f"user_{user_data['id']}/financial_plans"
        }
        
        response = await self.client.post(
            "/api/v1/pdf/deliver",
            json=cloud_delivery_request,
            headers=headers
        )
        assert response.status_code == 200
        
        delivery_result = response.json()
        assert 'cloud_url' in delivery_result
        assert delivery_result['status'] == 'uploaded'
        
        return True
    
    async def _test_pdf_api_download(self, user_data: Dict[str, Any], pdf_result: Dict[str, Any]) -> bool:
        """Test PDF download via API."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        pdf_id = pdf_result.get('id', 'test_pdf_id')
        
        # Test direct download
        response = await self.client.get(
            f"/api/v1/pdf/{pdf_id}/download",
            headers=headers
        )
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        
        # Test streaming download
        response = await self.client.get(
            f"/api/v1/pdf/{pdf_id}/stream",
            headers=headers
        )
        assert response.status_code == 200
        
        return True
    
    async def _test_pdf_mobile_app_delivery(self, user_data: Dict[str, Any], pdf_result: Dict[str, Any]) -> bool:
        """Test PDF delivery for mobile app integration."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        mobile_delivery_request = {
            "pdf_id": pdf_result.get('id', 'test_pdf_id'),
            "delivery_method": "mobile_app",
            "app_platform": "ios",
            "push_notification": True,
            "notification_message": "Your financial plan is ready for review"
        }
        
        response = await self.client.post(
            "/api/v1/pdf/deliver",
            json=mobile_delivery_request,
            headers=headers
        )
        assert response.status_code == 200
        
        delivery_result = response.json()
        assert 'mobile_url' in delivery_result
        assert 'push_notification_sent' in delivery_result
        
        return True
    
    async def _test_template_rendering_error_handling(self, user_data: Dict[str, Any]) -> bool:
        """Test template rendering error handling."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test with invalid template
        invalid_template_request = {
            "template": "non_existent_template",
            "simulation_id": "invalid_simulation_id"
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=invalid_template_request,
            headers=headers
        )
        
        # Should handle gracefully
        assert response.status_code in [400, 404]
        
        error_response = response.json()
        assert 'error' in error_response
        
        return True
    
    async def _test_pdf_data_validation_errors(self, user_data: Dict[str, Any]) -> bool:
        """Test PDF generation with invalid data."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test with missing required data
        invalid_data_request = {
            "template": "professional_plan",
            # Missing simulation_id
        }
        
        response = await self.client.post(
            "/api/v1/pdf/generate",
            json=invalid_data_request,
            headers=headers
        )
        
        assert response.status_code == 400
        
        error_response = response.json()
        assert 'validation_error' in error_response or 'error' in error_response
        
        return True
    
    async def _test_pdf_storage_failure_handling(self, user_data: Dict[str, Any]) -> bool:
        """Test PDF storage failure handling."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        with patch('app.services.pdf_generator.PDFStorage.store') as mock_store:
            # Simulate storage failure
            mock_store.side_effect = Exception("Storage service unavailable")
            
            pdf_request = {
                "template": "professional_plan",
                "simulation_id": "test_simulation_id"
            }
            
            response = await self.client.post(
                "/api/v1/pdf/generate",
                json=pdf_request,
                headers=headers
            )
            
            # Should handle storage failure gracefully
            if response.status_code == 202:
                # Check job status should show failure
                pdf_job = response.json()
                await asyncio.sleep(2)
                
                response = await self.client.get(
                    f"/api/v1/pdf/status/{pdf_job['job_id']}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assert result.get('status') == 'failed'
                    assert 'storage' in result.get('error_message', '').lower()
        
        return True
    
    async def _test_pdf_generation_recovery(self, user_data: Dict[str, Any]) -> bool:
        """Test PDF generation recovery mechanisms."""
        headers = {"Authorization": f"Bearer {user_data['auth_token']}"}
        
        # Test retry mechanism
        retry_request = {
            "action": "retry_failed_jobs",
            "max_retries": 3
        }
        
        response = await self.client.post(
            "/api/v1/pdf/recovery",
            json=retry_request,
            headers=headers
        )
        assert response.status_code == 200
        
        recovery_result = response.json()
        assert 'jobs_retried' in recovery_result
        assert 'recovery_status' in recovery_result
        
        return True


@pytest.mark.asyncio
@pytest.mark.integration
class TestPDFGenerationPerformance:
    """Test PDF generation performance and scalability."""
    
    async def test_pdf_generation_performance(self):
        """Test PDF generation performance with various sizes."""
        test = TestPDFGenerationIntegration()
        
        async with integration_test_context(test) as config:
            scenario = await test._create_complete_financial_scenario()
            user_data = scenario['user']
            simulation = await test._generate_simulation_for_pdf(user_data)
            
            # Test different PDF sizes
            templates = [
                {"name": "executive_summary", "expected_max_time": 10},
                {"name": "professional_plan", "expected_max_time": 20},
                {"name": "detailed_analysis", "expected_max_time": 30}
            ]
            
            for template in templates:
                start_time = time.time()
                
                pdf_result = await test._test_professional_pdf_generation(
                    user_data, simulation
                )
                
                end_time = time.time()
                generation_time = end_time - start_time
                
                assert generation_time < template["expected_max_time"], \
                    f"{template['name']} took {generation_time:.2f}s, expected < {template['expected_max_time']}s"
    
    async def test_concurrent_pdf_generation(self):
        """Test concurrent PDF generation performance."""
        test = TestPDFGenerationIntegration()
        
        async with integration_test_context(test) as config:
            
            # Create multiple scenarios
            scenarios = []
            for i in range(5):
                scenario = await test._create_complete_financial_scenario()
                simulation = await test._generate_simulation_for_pdf(scenario['user'])
                scenarios.append({'user': scenario['user'], 'simulation': simulation})
            
            # Generate PDFs concurrently
            start_time = time.time()
            
            tasks = []
            for scenario in scenarios:
                task = asyncio.create_task(
                    test._test_professional_pdf_generation(
                        scenario['user'], scenario['simulation']
                    )
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # All should succeed
            successful_results = [r for r in results if not isinstance(r, Exception)]
            assert len(successful_results) == len(scenarios)
            
            # Should complete within reasonable time
            assert total_time < 60, f"Concurrent generation took {total_time:.2f}s, expected < 60s"
            
            # Calculate throughput
            pdfs_per_second = len(successful_results) / total_time
            assert pdfs_per_second > 0.1, f"Throughput too low: {pdfs_per_second:.2f} PDFs/sec"
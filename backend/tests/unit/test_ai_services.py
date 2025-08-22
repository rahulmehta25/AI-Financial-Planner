"""
Unit tests for AI services including LLM integration and narrative generation.

Tests OpenAI/Anthropic integration, prompt engineering, and AI safety controls.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from decimal import Decimal
import json

from app.ai.llm_client import LLMClient
from app.ai.narrative_generator import NarrativeGenerator
from app.ai.safety_controller import SafetyController
from app.ai.template_manager import TemplateManager
from tests.factories import UserFactory, FinancialProfileFactory, GoalFactory


class TestLLMClient:
    """Test cases for LLM client integration."""
    
    @pytest.fixture
    def llm_client(self, mock_openai_client, mock_anthropic_client):
        """Create LLM client with mocked providers."""
        client = LLMClient()
        client.openai_client = mock_openai_client
        client.anthropic_client = mock_anthropic_client
        return client
    
    @pytest.mark.asyncio
    async def test_openai_completion(self, llm_client):
        """Test OpenAI completion generation."""
        # Arrange
        prompt = "Explain the importance of emergency funds"
        expected_response = "An emergency fund is crucial for financial stability..."
        
        llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=expected_response))
        ]
        
        # Act
        response = await llm_client.generate_completion(
            prompt=prompt,
            provider="openai",
            model="gpt-4"
        )
        
        # Assert
        assert response == expected_response
        llm_client.openai_client.chat.completions.create.assert_called_once()
        call_args = llm_client.openai_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4'
        assert any('emergency funds' in msg['content'] for msg in call_args[1]['messages'])
    
    @pytest.mark.asyncio
    async def test_anthropic_completion(self, llm_client):
        """Test Anthropic completion generation."""
        # Arrange
        prompt = "Analyze portfolio risk allocation"
        expected_response = "Your portfolio shows a balanced risk allocation..."
        
        llm_client.anthropic_client.messages.create.return_value.content = [
            MagicMock(text=expected_response)
        ]
        
        # Act
        response = await llm_client.generate_completion(
            prompt=prompt,
            provider="anthropic",
            model="claude-3-sonnet"
        )
        
        # Assert
        assert response == expected_response
        llm_client.anthropic_client.messages.create.assert_called_once()
        call_args = llm_client.anthropic_client.messages.create.call_args
        assert call_args[1]['model'] == 'claude-3-sonnet'
    
    @pytest.mark.asyncio
    async def test_structured_output(self, llm_client):
        """Test generation of structured JSON output."""
        # Arrange
        prompt = "Generate financial advice in JSON format"
        structured_response = {
            "recommendations": [
                {"category": "savings", "priority": "high", "action": "Increase emergency fund"},
                {"category": "investment", "priority": "medium", "action": "Diversify portfolio"}
            ],
            "risk_assessment": "moderate"
        }
        
        llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps(structured_response)))
        ]
        
        # Act
        response = await llm_client.generate_structured_output(
            prompt=prompt,
            schema={
                "type": "object",
                "properties": {
                    "recommendations": {"type": "array"},
                    "risk_assessment": {"type": "string"}
                }
            }
        )
        
        # Assert
        assert response == structured_response
        assert isinstance(response["recommendations"], list)
        assert len(response["recommendations"]) == 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, llm_client):
        """Test error handling for API failures."""
        # Arrange
        llm_client.openai_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Act & Assert
        with pytest.raises(Exception, match="API Error"):
            await llm_client.generate_completion("test prompt", provider="openai")
    
    @pytest.mark.asyncio
    async def test_retry_logic(self, llm_client):
        """Test retry logic for transient failures."""
        # Arrange
        llm_client.openai_client.chat.completions.create.side_effect = [
            Exception("Rate limit exceeded"),
            Exception("Service unavailable"),
            MagicMock(choices=[MagicMock(message=MagicMock(content="Success!"))])
        ]
        
        # Act
        response = await llm_client.generate_completion(
            "test prompt",
            provider="openai",
            max_retries=3
        )
        
        # Assert
        assert response == "Success!"
        assert llm_client.openai_client.chat.completions.create.call_count == 3
    
    @pytest.mark.asyncio
    async def test_token_counting(self, llm_client):
        """Test token counting functionality."""
        # Arrange
        prompt = "This is a test prompt for token counting"
        
        # Act
        token_count = await llm_client.count_tokens(prompt, model="gpt-4")
        
        # Assert
        assert isinstance(token_count, int)
        assert token_count > 0
    
    @pytest.mark.asyncio
    async def test_cost_estimation(self, llm_client):
        """Test cost estimation for API calls."""
        # Arrange
        prompt = "Calculate portfolio performance"
        token_count = 100
        
        # Act
        cost = await llm_client.estimate_cost(
            input_tokens=token_count,
            output_tokens=50,
            model="gpt-4"
        )
        
        # Assert
        assert isinstance(cost, float)
        assert cost > 0


class TestNarrativeGenerator:
    """Test cases for AI narrative generation."""
    
    @pytest.fixture
    def narrative_generator(self, mock_openai_client):
        """Create narrative generator with mocked LLM."""
        generator = NarrativeGenerator()
        generator.llm_client.openai_client = mock_openai_client
        return generator
    
    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for narrative generation."""
        return {
            'user_profile': {
                'age': 35,
                'annual_income': 75000,
                'risk_tolerance': 'moderate',
                'investment_timeline': 30
            },
            'portfolio': {
                'total_value': 125000,
                'allocation': {
                    'stocks': 0.7,
                    'bonds': 0.2,
                    'cash': 0.1
                },
                'performance': {
                    'annual_return': 0.08,
                    'volatility': 0.15
                }
            },
            'goals': [
                {
                    'name': 'Retirement',
                    'target_amount': 1000000,
                    'current_progress': 0.125,
                    'target_date': '2054-01-01'
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_generate_portfolio_summary(self, narrative_generator, sample_financial_data):
        """Test portfolio summary narrative generation."""
        # Arrange
        expected_narrative = """
        Your investment portfolio shows strong performance with a balanced allocation.
        At $125,000, your portfolio is well-diversified across stocks (70%), bonds (20%), and cash (10%).
        The 8% annual return demonstrates solid growth while maintaining moderate risk levels.
        """
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=expected_narrative))
        ]
        
        # Act
        narrative = await narrative_generator.generate_portfolio_summary(sample_financial_data)
        
        # Assert
        assert narrative is not None
        assert len(narrative) > 0
        assert "portfolio" in narrative.lower()
        assert "diversified" in narrative.lower()
    
    @pytest.mark.asyncio
    async def test_generate_goal_progress_narrative(self, narrative_generator, sample_financial_data):
        """Test goal progress narrative generation."""
        # Arrange
        expected_narrative = """
        You're making excellent progress toward your retirement goal. With $125,000 saved,
        you've achieved 12.5% of your $1,000,000 target. At your current pace, you're
        on track to reach your goal by the target date of 2054.
        """
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=expected_narrative))
        ]
        
        # Act
        narrative = await narrative_generator.generate_goal_progress_narrative(
            sample_financial_data['goals'][0],
            sample_financial_data['user_profile']
        )
        
        # Assert
        assert narrative is not None
        assert "progress" in narrative.lower()
        assert "retirement" in narrative.lower()
        assert "12.5%" in narrative
    
    @pytest.mark.asyncio
    async def test_generate_risk_analysis_narrative(self, narrative_generator, sample_financial_data):
        """Test risk analysis narrative generation."""
        # Arrange
        expected_narrative = """
        Your portfolio's risk profile aligns well with your moderate risk tolerance.
        The 15% volatility is appropriate for your 30-year investment timeline,
        providing growth potential while maintaining reasonable stability.
        """
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=expected_narrative))
        ]
        
        # Act
        narrative = await narrative_generator.generate_risk_analysis_narrative(sample_financial_data)
        
        # Assert
        assert narrative is not None
        assert "risk" in narrative.lower()
        assert "volatility" in narrative.lower()
        assert "moderate" in narrative.lower()
    
    @pytest.mark.asyncio
    async def test_generate_recommendations(self, narrative_generator, sample_financial_data):
        """Test recommendation generation."""
        # Arrange
        expected_recommendations = """
        Based on your profile, consider these recommendations:
        1. Continue your current investment strategy as it aligns with your goals
        2. Consider increasing your bond allocation as you approach retirement
        3. Maintain your emergency fund at 3-6 months of expenses
        """
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=expected_recommendations))
        ]
        
        # Act
        recommendations = await narrative_generator.generate_recommendations(sample_financial_data)
        
        # Assert
        assert recommendations is not None
        assert "recommendations" in recommendations.lower()
        assert "consider" in recommendations.lower()
    
    @pytest.mark.asyncio
    async def test_personalization(self, narrative_generator, sample_financial_data):
        """Test narrative personalization based on user attributes."""
        # Modify for young aggressive investor
        young_aggressive_data = sample_financial_data.copy()
        young_aggressive_data['user_profile']['age'] = 25
        young_aggressive_data['user_profile']['risk_tolerance'] = 'aggressive'
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="As a young aggressive investor..."))
        ]
        
        # Act
        narrative = await narrative_generator.generate_portfolio_summary(young_aggressive_data)
        
        # Assert
        assert "young" in narrative.lower() or "aggressive" in narrative.lower()
    
    @pytest.mark.asyncio
    async def test_multilingual_support(self, narrative_generator, sample_financial_data):
        """Test multilingual narrative generation."""
        # Arrange
        spanish_narrative = "Su cartera de inversiones muestra un rendimiento sólido..."
        
        narrative_generator.llm_client.openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=spanish_narrative))
        ]
        
        # Act
        narrative = await narrative_generator.generate_portfolio_summary(
            sample_financial_data,
            language="spanish"
        )
        
        # Assert
        assert narrative == spanish_narrative


class TestSafetyController:
    """Test cases for AI safety and content filtering."""
    
    @pytest.fixture
    def safety_controller(self):
        """Create safety controller."""
        return SafetyController()
    
    def test_detect_financial_advice_disclaimer(self, safety_controller):
        """Test detection of required disclaimers in financial advice."""
        # Test content without disclaimer
        content_without_disclaimer = "You should invest all your money in this stock."
        
        result = safety_controller.validate_content(content_without_disclaimer)
        assert result['requires_disclaimer'] is True
        assert 'financial advice' in result['issues'][0].lower()
        
        # Test content with proper disclaimer
        content_with_disclaimer = """
        This is general information only and not financial advice.
        You should invest all your money in this stock.
        Please consult a financial advisor.
        """
        
        result = safety_controller.validate_content(content_with_disclaimer)
        assert result['requires_disclaimer'] is False
    
    def test_detect_inappropriate_guarantees(self, safety_controller):
        """Test detection of inappropriate financial guarantees."""
        inappropriate_content = [
            "This investment guarantees 20% returns",
            "You will definitely make money",
            "Zero risk, maximum profit guaranteed"
        ]
        
        for content in inappropriate_content:
            result = safety_controller.validate_content(content)
            assert result['safe'] is False
            assert any('guarantee' in issue.lower() for issue in result['issues'])
    
    def test_detect_regulatory_violations(self, safety_controller):
        """Test detection of potential regulatory violations."""
        violating_content = [
            "Buy this penny stock for guaranteed profits",
            "This insider information will make you rich",
            "Skip due diligence, trust me on this investment"
        ]
        
        for content in violating_content:
            result = safety_controller.validate_content(content)
            assert result['safe'] is False
            assert len(result['issues']) > 0
    
    def test_validate_safe_content(self, safety_controller):
        """Test validation of appropriate financial content."""
        safe_content = """
        This is general information only and not personalized financial advice.
        Diversification is an important investment principle that may help reduce risk.
        Past performance does not guarantee future results.
        Please consult with a qualified financial advisor before making investment decisions.
        """
        
        result = safety_controller.validate_content(safe_content)
        assert result['safe'] is True
        assert len(result['issues']) == 0
    
    def test_content_filtering(self, safety_controller):
        """Test content filtering and sanitization."""
        problematic_content = "GUARANTEED profits! Call now for insider tips!"
        
        filtered_content = safety_controller.filter_content(problematic_content)
        
        assert "guaranteed" not in filtered_content.lower()
        assert "insider" not in filtered_content.lower()
        assert len(filtered_content) > 0
    
    def test_risk_level_assessment(self, safety_controller):
        """Test risk level assessment of content."""
        high_risk_content = "Put everything in cryptocurrency for maximum gains!"
        medium_risk_content = "Consider allocating some funds to growth stocks"
        low_risk_content = "Diversification can help manage investment risk"
        
        assert safety_controller.assess_risk_level(high_risk_content) == "high"
        assert safety_controller.assess_risk_level(medium_risk_content) == "medium"
        assert safety_controller.assess_risk_level(low_risk_content) == "low"


class TestTemplateManager:
    """Test cases for AI prompt template management."""
    
    @pytest.fixture
    def template_manager(self):
        """Create template manager."""
        return TemplateManager()
    
    def test_load_template(self, template_manager):
        """Test loading and retrieving templates."""
        # Template should exist for portfolio analysis
        template = template_manager.get_template("portfolio_analysis")
        assert template is not None
        assert "portfolio" in template.lower()
        assert "{" in template  # Should contain placeholder variables
    
    def test_template_variables(self, template_manager):
        """Test template variable substitution."""
        template = template_manager.get_template("goal_progress")
        
        variables = {
            "goal_name": "Retirement Fund",
            "current_amount": "$125,000",
            "target_amount": "$1,000,000",
            "progress_percentage": "12.5%"
        }
        
        rendered = template_manager.render_template("goal_progress", variables)
        
        assert "Retirement Fund" in rendered
        assert "$125,000" in rendered
        assert "12.5%" in rendered
    
    def test_template_validation(self, template_manager):
        """Test template validation for required variables."""
        # Should raise error for missing required variables
        with pytest.raises(ValueError, match="Missing required variables"):
            template_manager.render_template(
                "portfolio_analysis",
                {"incomplete": "data"}  # Missing required variables
            )
    
    def test_custom_template_registration(self, template_manager):
        """Test registration of custom templates."""
        custom_template = "Hello {name}, your balance is {balance}"
        
        template_manager.register_template("custom_greeting", custom_template)
        
        rendered = template_manager.render_template(
            "custom_greeting",
            {"name": "John", "balance": "$1,000"}
        )
        
        assert rendered == "Hello John, your balance is $1,000"
    
    def test_template_localization(self, template_manager):
        """Test template localization for different languages."""
        # Register localized templates
        template_manager.register_template(
            "greeting_en",
            "Hello {name}, welcome to financial planning"
        )
        template_manager.register_template(
            "greeting_es",
            "Hola {name}, bienvenido a la planificación financiera"
        )
        
        # Test English
        en_result = template_manager.render_template(
            "greeting_en",
            {"name": "John"}
        )
        assert "Hello John" in en_result
        
        # Test Spanish
        es_result = template_manager.render_template(
            "greeting_es", 
            {"name": "Juan"}
        )
        assert "Hola Juan" in es_result
    
    @pytest.mark.asyncio
    async def test_dynamic_template_loading(self, template_manager):
        """Test dynamic template loading from external sources."""
        # Mock external template source
        with patch.object(template_manager, '_load_external_template') as mock_load:
            mock_load.return_value = "Dynamic template with {variable}"
            
            template = await template_manager.get_template_async("dynamic_template")
            
            assert template == "Dynamic template with {variable}"
            mock_load.assert_called_once_with("dynamic_template")
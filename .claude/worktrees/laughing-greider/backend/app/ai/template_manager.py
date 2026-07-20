"""Template management system for controlled narrative generation."""

from typing import Dict, Any, Optional, List
from enum import Enum
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
import json
import hashlib
from datetime import datetime
from pathlib import Path


class TemplateType(str, Enum):
    """Types of narrative templates."""
    BASELINE_SUMMARY = "baseline_summary"
    SCENARIO_COMPARISON = "scenario_comparison"
    RISK_ASSESSMENT = "risk_assessment"
    ACTION_RECOMMENDATION = "action_recommendation"
    GOAL_PROGRESS = "goal_progress"
    PORTFOLIO_REVIEW = "portfolio_review"
    MARKET_OUTLOOK = "market_outlook"
    TAX_IMPLICATIONS = "tax_implications"


class TemplateManager:
    """Manages pre-defined templates for narrative generation."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template manager.
        
        Args:
            template_dir: Directory containing template files
        """
        self.template_dir = template_dir or str(Path(__file__).parent / "templates")
        self._ensure_template_dir()
        
        # Initialize Jinja2 environment with security settings
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Template version tracking
        self.template_versions: Dict[str, str] = {}
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _ensure_template_dir(self):
        """Ensure template directory exists."""
        Path(self.template_dir).mkdir(parents=True, exist_ok=True)
    
    def _initialize_default_templates(self):
        """Initialize default narrative templates."""
        self.default_templates = {
            TemplateType.BASELINE_SUMMARY: """
Based on your financial profile, here's your baseline projection:

Starting with ${initial_portfolio:,.0f} at age {current_age}, your portfolio is projected to grow to ${final_portfolio:,.0f} by age {retirement_age}.

Key Metrics:
- Average Annual Return: {avg_return:.1f}%
- Success Rate: {success_rate:.0f}% probability of meeting goals
- Monthly Savings Required: ${monthly_savings:,.0f}
- Time to Retirement: {years_to_retirement} years

{risk_level} risk tolerance suggests a portfolio allocation of:
- Stocks: {stock_allocation:.0f}%
- Bonds: {bond_allocation:.0f}%
- Cash: {cash_allocation:.0f}%

This projection assumes {inflation_rate:.1f}% annual inflation and considers your {num_goals} financial goals.
""",
            
            TemplateType.SCENARIO_COMPARISON: """
Comparing your scenarios reveals important trade-offs:

Scenario A: {scenario_a_name}
- Final Portfolio: ${scenario_a_final:,.0f}
- Success Rate: {scenario_a_success:.0f}%
- Monthly Investment: ${scenario_a_monthly:,.0f}
- Risk Level: {scenario_a_risk}

Scenario B: {scenario_b_name}
- Final Portfolio: ${scenario_b_final:,.0f}
- Success Rate: {scenario_b_success:.0f}%
- Monthly Investment: ${scenario_b_monthly:,.0f}
- Risk Level: {scenario_b_risk}

Key Differences:
- Portfolio Difference: ${portfolio_difference:,.0f} ({portfolio_diff_pct:.1f}%)
- Success Rate Change: {success_diff:.0f} percentage points
- Monthly Investment Change: ${monthly_diff:,.0f}

Recommendation: {recommendation_text}
""",
            
            TemplateType.RISK_ASSESSMENT: """
Risk Analysis for Your Portfolio:

Current Risk Profile: {risk_profile}
- Volatility: {volatility:.1f}% annual standard deviation
- Maximum Drawdown: {max_drawdown:.1f}%
- Value at Risk (95%): ${var_95:,.0f}

Stress Test Results:
- Market Crash (-30%): Portfolio value would be ${crash_value:,.0f}
- Recession Scenario: {recession_impact:.1f}% portfolio decline
- Recovery Time: Approximately {recovery_months} months

Risk Mitigation Strategies:
1. {strategy_1}
2. {strategy_2}
3. {strategy_3}

Your current allocation is {risk_alignment} with your stated risk tolerance.
""",
            
            TemplateType.ACTION_RECOMMENDATION: """
Recommended Actions (Priority Order):

1. {action_1_title}
   - Impact: {action_1_impact}
   - Timeline: {action_1_timeline}
   - Estimated Benefit: ${action_1_benefit:,.0f}

2. {action_2_title}
   - Impact: {action_2_impact}
   - Timeline: {action_2_timeline}
   - Estimated Benefit: ${action_2_benefit:,.0f}

3. {action_3_title}
   - Impact: {action_3_impact}
   - Timeline: {action_3_timeline}
   - Estimated Benefit: ${action_3_benefit:,.0f}

Next Steps:
- {next_step_1}
- {next_step_2}
- Review progress in {review_timeline}

These actions could improve your success rate by {total_improvement:.0f} percentage points.
""",
            
            TemplateType.GOAL_PROGRESS: """
Progress Toward Your Goals:

{goal_name}:
- Target Amount: ${goal_target:,.0f}
- Current Progress: ${current_progress:,.0f} ({progress_pct:.0f}%)
- Time Remaining: {time_remaining} years
- On Track: {on_track_status}

Required Monthly Contribution: ${required_monthly:,.0f}
Current Monthly Contribution: ${current_monthly:,.0f}
Gap: ${contribution_gap:,.0f}

Projection:
- Best Case (75th percentile): ${best_case:,.0f}
- Expected Case (50th percentile): ${expected_case:,.0f}
- Worst Case (25th percentile): ${worst_case:,.0f}

{adjustment_message}
""",
            
            TemplateType.PORTFOLIO_REVIEW: """
Portfolio Performance Review:

Period: {review_period}
Starting Value: ${start_value:,.0f}
Ending Value: ${end_value:,.0f}
Net Change: ${net_change:,.0f} ({change_pct:.1f}%)

Performance Metrics:
- Total Return: {total_return:.1f}%
- Annualized Return: {annualized_return:.1f}%
- Sharpe Ratio: {sharpe_ratio:.2f}
- Alpha: {alpha:.2f}%

Asset Performance:
{asset_performance_list}

Rebalancing Recommendation: {rebalancing_needed}
{rebalancing_details}
""",
            
            TemplateType.MARKET_OUTLOOK: """
Market Assumptions Impact:

Your plan uses {assumption_type} market assumptions:
- Expected Stock Returns: {stock_return:.1f}% annually
- Expected Bond Returns: {bond_return:.1f}% annually
- Inflation Rate: {inflation:.1f}%

Sensitivity Analysis:
- If returns are 1% lower: Final portfolio ${lower_return_impact:,.0f}
- If returns are 1% higher: Final portfolio ${higher_return_impact:,.0f}
- If inflation is 1% higher: Real value ${inflation_impact:,.0f}

Historical Context:
These assumptions are {assumption_comparison} historical averages.
""",
            
            TemplateType.TAX_IMPLICATIONS: """
Tax Considerations:

Estimated Annual Tax Impact:
- Capital Gains Tax: ${cap_gains_tax:,.0f}
- Dividend Tax: ${dividend_tax:,.0f}
- Interest Income Tax: ${interest_tax:,.0f}
- Total Tax Burden: ${total_tax:,.0f}

Tax-Efficient Strategies:
1. {tax_strategy_1}
2. {tax_strategy_2}
3. {tax_strategy_3}

After-Tax Returns:
- Pre-Tax Return: {pretax_return:.1f}%
- After-Tax Return: {aftertax_return:.1f}%
- Tax Drag: {tax_drag:.1f} percentage points

Recommended Account Types:
{account_recommendations}
"""
        }
    
    def get_template(self, 
                     template_type: TemplateType,
                     language: str = "en",
                     version: Optional[str] = None) -> Template:
        """Get a specific template.
        
        Args:
            template_type: Type of template to retrieve
            language: Language code
            version: Specific version (optional)
            
        Returns:
            Jinja2 template object
        """
        # Try to load from file first
        template_file = f"{template_type.value}_{language}.j2"
        template_path = Path(self.template_dir) / template_file
        
        if template_path.exists():
            return self.env.get_template(template_file)
        
        # Fall back to default templates
        if template_type in self.default_templates:
            return Template(self.default_templates[template_type])
        
        raise ValueError(f"Template {template_type} not found")
    
    def render_template(self,
                       template_type: TemplateType,
                       data: Dict[str, Any],
                       language: str = "en",
                       validate: bool = True) -> str:
        """Render a template with provided data.
        
        Args:
            template_type: Type of template to render
            data: Data dictionary for template variables
            language: Language code
            validate: Whether to validate data before rendering
            
        Returns:
            Rendered narrative text
        """
        if validate:
            self._validate_template_data(template_type, data)
        
        template = self.get_template(template_type, language)
        
        # Add default values for missing optional fields
        data = self._add_default_values(template_type, data)
        
        # Render template
        rendered = template.render(**data)
        
        # Clean up extra whitespace
        rendered = "\n".join(line for line in rendered.splitlines() if line.strip())
        
        return rendered
    
    def _validate_template_data(self, 
                                template_type: TemplateType,
                                data: Dict[str, Any]):
        """Validate template data has required fields.
        
        Args:
            template_type: Template type
            data: Data dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = self._get_required_fields(template_type)
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            raise ValueError(f"Missing required fields for {template_type}: {missing_fields}")
    
    def _get_required_fields(self, template_type: TemplateType) -> List[str]:
        """Get required fields for a template type.
        
        Args:
            template_type: Template type
            
        Returns:
            List of required field names
        """
        # Define required fields for each template type
        required_fields_map = {
            TemplateType.BASELINE_SUMMARY: [
                "initial_portfolio", "current_age", "final_portfolio",
                "retirement_age", "avg_return", "success_rate"
            ],
            TemplateType.SCENARIO_COMPARISON: [
                "scenario_a_name", "scenario_a_final", "scenario_b_name",
                "scenario_b_final"
            ],
            TemplateType.RISK_ASSESSMENT: [
                "risk_profile", "volatility", "max_drawdown"
            ],
            TemplateType.ACTION_RECOMMENDATION: [
                "action_1_title", "action_1_impact"
            ],
            TemplateType.GOAL_PROGRESS: [
                "goal_name", "goal_target", "current_progress"
            ],
            TemplateType.PORTFOLIO_REVIEW: [
                "review_period", "start_value", "end_value"
            ],
            TemplateType.MARKET_OUTLOOK: [
                "stock_return", "bond_return", "inflation"
            ],
            TemplateType.TAX_IMPLICATIONS: [
                "cap_gains_tax", "total_tax", "pretax_return"
            ]
        }
        
        return required_fields_map.get(template_type, [])
    
    def _add_default_values(self,
                           template_type: TemplateType,
                           data: Dict[str, Any]) -> Dict[str, Any]:
        """Add default values for optional fields.
        
        Args:
            template_type: Template type
            data: Original data dictionary
            
        Returns:
            Data dictionary with defaults added
        """
        defaults = {
            "risk_level": "Moderate",
            "inflation_rate": 2.5,
            "num_goals": 1,
            "stock_allocation": 60,
            "bond_allocation": 30,
            "cash_allocation": 10,
            "recommendation_text": "Consider your options carefully",
            "risk_alignment": "aligned",
            "on_track_status": "Yes",
            "rebalancing_needed": "No rebalancing needed",
            "assumption_type": "conservative",
            "assumption_comparison": "below"
        }
        
        # Merge defaults with provided data (data takes precedence)
        return {**defaults, **data}
    
    def get_template_hash(self, template_type: TemplateType) -> str:
        """Get hash of template for version tracking.
        
        Args:
            template_type: Template type
            
        Returns:
            SHA256 hash of template content
        """
        template = self.get_template(template_type)
        content = template.source if hasattr(template, 'source') else str(template)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with metadata.
        
        Returns:
            List of template information dictionaries
        """
        templates = []
        for template_type in TemplateType:
            templates.append({
                "type": template_type.value,
                "name": template_type.name,
                "hash": self.get_template_hash(template_type),
                "required_fields": self._get_required_fields(template_type)
            })
        return templates
"""Enhanced template management system with multi-language support and numerical validation."""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

from jinja2 import Environment, FileSystemLoader, Template, select_autoescape
from pydantic import BaseModel, Field, validator

from .config import Language

logger = logging.getLogger(__name__)


class TemplateCategory(str, Enum):
    """Categories of templates."""
    SIMULATION = "simulation"
    TRADE_OFF = "trade_off"
    RECOMMENDATION = "recommendation"
    RISK = "risk"
    GOAL = "goal"
    PORTFOLIO = "portfolio"
    COMPLIANCE = "compliance"


class TemplateVariable(BaseModel):
    """Definition of a template variable."""
    name: str
    type: str  # "number", "percentage", "currency", "text", "date"
    required: bool = True
    format: Optional[str] = None  # e.g., "{:.2f}", "{:,.0f}", "{:%Y-%m-%d}"
    validation: Optional[Dict[str, Any]] = None  # min, max, regex, etc.
    description: Optional[str] = None


class NarrativeTemplate(BaseModel):
    """Structured narrative template."""
    id: str
    category: TemplateCategory
    name: str
    description: str
    language: Language
    version: str = "v1.0.0"
    template_text: str
    variables: List[TemplateVariable]
    compliance_required: bool = False
    max_length: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('template_text')
    def validate_placeholders(cls, v, values):
        """Validate that all placeholders in template match defined variables."""
        if 'variables' in values:
            var_names = {var.name for var in values['variables']}
            # Find all placeholders in template
            placeholders = set(re.findall(r'\{\{(\w+)\}\}', v))
            
            # Check for undefined placeholders
            undefined = placeholders - var_names
            if undefined:
                raise ValueError(f"Undefined placeholders in template: {undefined}")
        
        return v


class EnhancedTemplateManager:
    """Manages narrative templates with strict numerical validation and multi-language support."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize template manager."""
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
        # Initialize Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Template cache
        self.templates: Dict[str, NarrativeTemplate] = {}
        
        # Load default templates
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default templates for each category and language."""
        default_templates = [
            # English Templates
            NarrativeTemplate(
                id="sim_summary_en_v1",
                category=TemplateCategory.SIMULATION,
                name="Simulation Summary",
                description="Summary of Monte Carlo simulation results",
                language=Language.ENGLISH,
                template_text="""Based on {{num_simulations}} Monte Carlo simulations, your financial plan shows a {{success_rate}}% probability of achieving your goals.

Key Findings:
- Median portfolio value at retirement: ${{median_value:,.0f}}
- Best case scenario (95th percentile): ${{best_case:,.0f}}
- Worst case scenario (5th percentile): ${{worst_case:,.0f}}
- Required monthly savings: ${{monthly_savings:,.0f}}

Your current allocation of {{equity_pct}}% equities and {{bond_pct}}% bonds provides an expected annual return of {{expected_return:.1f}}% with a standard deviation of {{std_dev:.1f}}%.

The simulation accounts for an average inflation rate of {{inflation_rate:.1f}}% and market volatility based on historical data from the past {{historical_years}} years.""",
                variables=[
                    TemplateVariable(name="num_simulations", type="number"),
                    TemplateVariable(name="success_rate", type="percentage"),
                    TemplateVariable(name="median_value", type="currency"),
                    TemplateVariable(name="best_case", type="currency"),
                    TemplateVariable(name="worst_case", type="currency"),
                    TemplateVariable(name="monthly_savings", type="currency"),
                    TemplateVariable(name="equity_pct", type="percentage"),
                    TemplateVariable(name="bond_pct", type="percentage"),
                    TemplateVariable(name="expected_return", type="percentage"),
                    TemplateVariable(name="std_dev", type="percentage"),
                    TemplateVariable(name="inflation_rate", type="percentage"),
                    TemplateVariable(name="historical_years", type="number")
                ]
            ),
            
            NarrativeTemplate(
                id="trade_off_en_v1",
                category=TemplateCategory.TRADE_OFF,
                name="Trade-Off Analysis",
                description="Analysis of financial trade-offs",
                language=Language.ENGLISH,
                template_text="""Trade-Off Analysis for Your Financial Strategy:

Current Strategy Performance:
- Success probability: {{current_success}}%
- Expected portfolio value: ${{current_value:,.0f}}
- Risk level (volatility): {{current_risk:.1f}}%

Alternative Strategy Options:

1. Conservative Approach ({{conservative_equity}}% equities):
   - Success probability: {{conservative_success}}%
   - Expected value: ${{conservative_value:,.0f}}
   - Risk reduction: {{conservative_risk_reduction:.1f}}%
   - Trade-off: Lower returns but greater stability

2. Aggressive Approach ({{aggressive_equity}}% equities):
   - Success probability: {{aggressive_success}}%
   - Expected value: ${{aggressive_value:,.0f}}
   - Risk increase: {{aggressive_risk_increase:.1f}}%
   - Trade-off: Higher potential returns with increased volatility

3. Balanced Optimization:
   - Optimal equity allocation: {{optimal_equity}}%
   - Success probability: {{optimal_success}}%
   - Expected value: ${{optimal_value:,.0f}}
   - Sharpe ratio improvement: {{sharpe_improvement:.2f}}

Key Consideration: Increasing monthly contributions by ${{additional_monthly:,.0f}} could improve success rate by {{improvement_rate:.1f}} percentage points.""",
                variables=[
                    TemplateVariable(name="current_success", type="percentage"),
                    TemplateVariable(name="current_value", type="currency"),
                    TemplateVariable(name="current_risk", type="percentage"),
                    TemplateVariable(name="conservative_equity", type="percentage"),
                    TemplateVariable(name="conservative_success", type="percentage"),
                    TemplateVariable(name="conservative_value", type="currency"),
                    TemplateVariable(name="conservative_risk_reduction", type="percentage"),
                    TemplateVariable(name="aggressive_equity", type="percentage"),
                    TemplateVariable(name="aggressive_success", type="percentage"),
                    TemplateVariable(name="aggressive_value", type="currency"),
                    TemplateVariable(name="aggressive_risk_increase", type="percentage"),
                    TemplateVariable(name="optimal_equity", type="percentage"),
                    TemplateVariable(name="optimal_success", type="percentage"),
                    TemplateVariable(name="optimal_value", type="currency"),
                    TemplateVariable(name="sharpe_improvement", type="number"),
                    TemplateVariable(name="additional_monthly", type="currency"),
                    TemplateVariable(name="improvement_rate", type="percentage")
                ]
            ),
            
            NarrativeTemplate(
                id="recommendation_en_v1",
                category=TemplateCategory.RECOMMENDATION,
                name="Personalized Recommendations",
                description="AI-generated recommendations based on analysis",
                language=Language.ENGLISH,
                template_text="""Based on your financial analysis, here are our recommendations:

Priority Actions:
1. Adjust asset allocation to {{recommended_equity}}% equities and {{recommended_bonds}}% bonds
   - This optimizes your risk-return profile
   - Expected improvement in returns: {{return_improvement:.1f}}%

2. Increase monthly contributions to ${{recommended_monthly:,.0f}}
   - Current contribution: ${{current_monthly:,.0f}}
   - Additional needed: ${{additional_needed:,.0f}}
   - This increases success probability from {{current_prob}}% to {{improved_prob}}%

3. Rebalancing Strategy:
   - Rebalance portfolio every {{rebalance_months}} months
   - Set deviation threshold at {{deviation_threshold}}%
   - Estimated cost savings: ${{cost_savings:,.0f}} annually

Long-term Optimizations:
- Consider tax-advantaged accounts to save ${{tax_savings:,.0f}} annually
- Review insurance coverage for {{insurance_gap:,.0f}} gap
- Emergency fund target: {{emergency_months}} months of expenses (${{emergency_amount:,.0f}})

Timeline:
- Immediate action: Allocation adjustment
- Within 30 days: Increase contributions
- Quarterly: Review and rebalance
- Annual: Comprehensive strategy review""",
                variables=[
                    TemplateVariable(name="recommended_equity", type="percentage"),
                    TemplateVariable(name="recommended_bonds", type="percentage"),
                    TemplateVariable(name="return_improvement", type="percentage"),
                    TemplateVariable(name="recommended_monthly", type="currency"),
                    TemplateVariable(name="current_monthly", type="currency"),
                    TemplateVariable(name="additional_needed", type="currency"),
                    TemplateVariable(name="current_prob", type="percentage"),
                    TemplateVariable(name="improved_prob", type="percentage"),
                    TemplateVariable(name="rebalance_months", type="number"),
                    TemplateVariable(name="deviation_threshold", type="percentage"),
                    TemplateVariable(name="cost_savings", type="currency"),
                    TemplateVariable(name="tax_savings", type="currency"),
                    TemplateVariable(name="insurance_gap", type="currency"),
                    TemplateVariable(name="emergency_months", type="number"),
                    TemplateVariable(name="emergency_amount", type="currency")
                ]
            ),
            
            # Spanish Templates
            NarrativeTemplate(
                id="sim_summary_es_v1",
                category=TemplateCategory.SIMULATION,
                name="Resumen de Simulación",
                description="Resumen de resultados de simulación Monte Carlo",
                language=Language.SPANISH,
                template_text="""Basado en {{num_simulations}} simulaciones Monte Carlo, su plan financiero muestra una probabilidad del {{success_rate}}% de lograr sus objetivos.

Hallazgos Clave:
- Valor medio de cartera en jubilación: ${{median_value:,.0f}}
- Mejor escenario (percentil 95): ${{best_case:,.0f}}
- Peor escenario (percentil 5): ${{worst_case:,.0f}}
- Ahorro mensual requerido: ${{monthly_savings:,.0f}}

Su asignación actual de {{equity_pct}}% en acciones y {{bond_pct}}% en bonos proporciona un rendimiento anual esperado del {{expected_return:.1f}}% con una desviación estándar del {{std_dev:.1f}}%.

La simulación considera una tasa de inflación promedio del {{inflation_rate:.1f}}% y volatilidad del mercado basada en datos históricos de los últimos {{historical_years}} años.""",
                variables=[
                    TemplateVariable(name="num_simulations", type="number"),
                    TemplateVariable(name="success_rate", type="percentage"),
                    TemplateVariable(name="median_value", type="currency"),
                    TemplateVariable(name="best_case", type="currency"),
                    TemplateVariable(name="worst_case", type="currency"),
                    TemplateVariable(name="monthly_savings", type="currency"),
                    TemplateVariable(name="equity_pct", type="percentage"),
                    TemplateVariable(name="bond_pct", type="percentage"),
                    TemplateVariable(name="expected_return", type="percentage"),
                    TemplateVariable(name="std_dev", type="percentage"),
                    TemplateVariable(name="inflation_rate", type="percentage"),
                    TemplateVariable(name="historical_years", type="number")
                ]
            ),
            
            # Chinese Templates
            NarrativeTemplate(
                id="sim_summary_zh_v1",
                category=TemplateCategory.SIMULATION,
                name="模拟摘要",
                description="蒙特卡洛模拟结果摘要",
                language=Language.CHINESE,
                template_text="""基于{{num_simulations}}次蒙特卡洛模拟，您的财务计划显示实现目标的概率为{{success_rate}}%。

关键发现：
- 退休时投资组合中位数价值：${{median_value:,.0f}}
- 最佳情况（第95百分位）：${{best_case:,.0f}}
- 最坏情况（第5百分位）：${{worst_case:,.0f}}
- 所需月储蓄：${{monthly_savings:,.0f}}

您当前{{equity_pct}}%股票和{{bond_pct}}%债券的配置提供{{expected_return:.1f}}%的预期年回报率，标准差为{{std_dev:.1f}}%。

模拟考虑了{{inflation_rate:.1f}}%的平均通胀率和基于过去{{historical_years}}年历史数据的市场波动性。""",
                variables=[
                    TemplateVariable(name="num_simulations", type="number"),
                    TemplateVariable(name="success_rate", type="percentage"),
                    TemplateVariable(name="median_value", type="currency"),
                    TemplateVariable(name="best_case", type="currency"),
                    TemplateVariable(name="worst_case", type="currency"),
                    TemplateVariable(name="monthly_savings", type="currency"),
                    TemplateVariable(name="equity_pct", type="percentage"),
                    TemplateVariable(name="bond_pct", type="percentage"),
                    TemplateVariable(name="expected_return", type="percentage"),
                    TemplateVariable(name="std_dev", type="percentage"),
                    TemplateVariable(name="inflation_rate", type="percentage"),
                    TemplateVariable(name="historical_years", type="number")
                ]
            ),
            
            # Compliance Templates
            NarrativeTemplate(
                id="compliance_disclaimer_en_v1",
                category=TemplateCategory.COMPLIANCE,
                name="Compliance Disclaimer",
                description="Standard compliance disclaimer",
                language=Language.ENGLISH,
                template_text="""IMPORTANT DISCLAIMER: This analysis is for informational purposes only and does not constitute financial advice. Past performance does not guarantee future results. All projections are based on historical data and assumptions that may not reflect future market conditions. 

The {{success_rate}}% success rate is based on {{num_simulations}} simulations using historical market data. Actual results may vary significantly.

Please consult with a qualified financial advisor before making investment decisions. This analysis generated on {{generation_date}} with data current as of {{data_date}}.""",
                variables=[
                    TemplateVariable(name="success_rate", type="percentage"),
                    TemplateVariable(name="num_simulations", type="number"),
                    TemplateVariable(name="generation_date", type="date"),
                    TemplateVariable(name="data_date", type="date")
                ],
                compliance_required=True
            )
        ]
        
        # Store templates
        for template in default_templates:
            self.templates[template.id] = template
            self._save_template_to_file(template)
    
    def _save_template_to_file(self, template: NarrativeTemplate):
        """Save template to file system."""
        file_path = self.template_dir / f"{template.id}.json"
        with open(file_path, 'w') as f:
            json.dump(template.dict(), f, indent=2, default=str)
    
    def get_template(
        self,
        category: TemplateCategory,
        language: Language = Language.ENGLISH,
        template_id: Optional[str] = None
    ) -> Optional[NarrativeTemplate]:
        """Get a template by category and language."""
        if template_id and template_id in self.templates:
            return self.templates[template_id]
        
        # Find matching template
        for tid, template in self.templates.items():
            if template.category == category and template.language == language:
                return template
        
        # Fallback to English if language not found
        if language != Language.ENGLISH:
            return self.get_template(category, Language.ENGLISH)
        
        return None
    
    def render_template(
        self,
        template: NarrativeTemplate,
        variables: Dict[str, Any],
        validate: bool = True
    ) -> str:
        """Render a template with variables."""
        if validate:
            self._validate_variables(template, variables)
        
        # Format variables according to their types
        formatted_vars = self._format_variables(template, variables)
        
        # Create Jinja2 template
        jinja_template = Template(template.template_text)
        
        # Render
        rendered = jinja_template.render(**formatted_vars)
        
        # Validate length if specified
        if template.max_length and len(rendered) > template.max_length:
            logger.warning(f"Rendered template exceeds max length: {len(rendered)} > {template.max_length}")
        
        return rendered
    
    def _validate_variables(self, template: NarrativeTemplate, variables: Dict[str, Any]):
        """Validate that all required variables are present and valid."""
        for var_def in template.variables:
            if var_def.required and var_def.name not in variables:
                raise ValueError(f"Required variable '{var_def.name}' not provided")
            
            if var_def.name in variables:
                value = variables[var_def.name]
                
                # Type validation
                if var_def.type in ["number", "percentage", "currency"]:
                    if not isinstance(value, (int, float)):
                        raise ValueError(f"Variable '{var_def.name}' must be numeric")
                    
                    # Range validation
                    if var_def.validation:
                        if "min" in var_def.validation and value < var_def.validation["min"]:
                            raise ValueError(f"Variable '{var_def.name}' below minimum: {value} < {var_def.validation['min']}")
                        if "max" in var_def.validation and value > var_def.validation["max"]:
                            raise ValueError(f"Variable '{var_def.name}' above maximum: {value} > {var_def.validation['max']}")
    
    def _format_variables(self, template: NarrativeTemplate, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Format variables according to their type definitions."""
        formatted = {}
        
        for var_def in template.variables:
            if var_def.name in variables:
                value = variables[var_def.name]
                
                # Apply type-specific formatting
                if var_def.type == "currency":
                    formatted[var_def.name] = f"{value:,.2f}"
                elif var_def.type == "percentage":
                    formatted[var_def.name] = f"{value:.1f}"
                elif var_def.type == "number":
                    if isinstance(value, float):
                        formatted[var_def.name] = f"{value:.2f}"
                    else:
                        formatted[var_def.name] = str(value)
                elif var_def.type == "date":
                    if hasattr(value, 'strftime'):
                        formatted[var_def.name] = value.strftime(var_def.format or "%Y-%m-%d")
                    else:
                        formatted[var_def.name] = str(value)
                else:
                    formatted[var_def.name] = str(value)
        
        return formatted
    
    def create_prompt_for_llm(
        self,
        template: NarrativeTemplate,
        variables: Dict[str, Any],
        context: Optional[str] = None
    ) -> str:
        """Create a prompt for LLM to enhance the template."""
        base_narrative = self.render_template(template, variables)
        
        prompt = f"""Please enhance the following financial narrative while maintaining all numerical values exactly as provided. Do not change any numbers, percentages, or currency amounts.

Base Narrative:
{base_narrative}

Requirements:
1. Keep all numbers, percentages, and currency values EXACTLY as shown
2. Enhance the narrative flow and readability
3. Add transitional phrases for better coherence
4. Maintain professional financial advisory tone
5. Ensure compliance with financial regulations
6. Do not add any new numerical claims or projections
"""
        
        if context:
            prompt += f"\n\nAdditional Context:\n{context}"
        
        return prompt
    
    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        language: Optional[Language] = None
    ) -> List[NarrativeTemplate]:
        """List available templates."""
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        if language:
            templates = [t for t in templates if t.language == language]
        
        return templates
    
    def add_custom_template(self, template: NarrativeTemplate) -> str:
        """Add a custom template."""
        self.templates[template.id] = template
        self._save_template_to_file(template)
        logger.info(f"Added custom template: {template.id}")
        return template.id
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing template."""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        template.updated_at = datetime.utcnow()
        self._save_template_to_file(template)
        logger.info(f"Updated template: {template_id}")
        return True
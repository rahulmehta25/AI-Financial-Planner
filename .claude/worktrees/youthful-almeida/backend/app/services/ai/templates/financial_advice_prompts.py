"""
Financial Advice Generation Templates and Prompts with Compliance
Provides structured templates for various financial advisory scenarios
"""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
import json

class AdviceCategory(Enum):
    """Categories of financial advice"""
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    TAX_PLANNING = "tax_planning"
    RETIREMENT_PLANNING = "retirement_planning"
    DEBT_MANAGEMENT = "debt_management"
    ESTATE_PLANNING = "estate_planning"
    INSURANCE_PLANNING = "insurance_planning"
    EDUCATION_PLANNING = "education_planning"
    EMERGENCY_FUND = "emergency_fund"
    INVESTMENT_STRATEGY = "investment_strategy"
    RISK_MANAGEMENT = "risk_management"

@dataclass
class PromptTemplate:
    """Structured prompt template"""
    category: AdviceCategory
    name: str
    system_prompt: str
    user_prompt_template: str
    required_context: List[str]
    compliance_level: str
    disclaimers: List[str]
    examples: Optional[List[Dict[str, str]]] = None

class FinancialAdvicePrompts:
    """Comprehensive prompt library for financial advice generation"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.compliance_disclaimers = self._initialize_disclaimers()
    
    def get_prompt(
        self,
        category: AdviceCategory,
        context: Dict[str, Any],
        include_examples: bool = True,
        compliance_level: str = "standard"
    ) -> str:
        """Get formatted prompt for specific category"""
        
        template = self.templates.get(category)
        if not template:
            return self._get_default_prompt(context)
        
        # Build system prompt
        system_prompt = template.system_prompt
        
        # Add compliance guidelines
        if compliance_level == "strict":
            system_prompt += "\n\n" + self._get_compliance_guidelines()
        
        # Format user prompt with context
        user_prompt = self._format_user_prompt(template, context)
        
        # Add examples if requested
        if include_examples and template.examples:
            user_prompt += "\n\n" + self._format_examples(template.examples)
        
        # Add required disclaimers
        disclaimers = self._get_required_disclaimers(category, compliance_level)
        
        # Combine all parts
        full_prompt = f"""
{system_prompt}

{user_prompt}

IMPORTANT DISCLAIMERS TO INCLUDE:
{chr(10).join(f"- {d}" for d in disclaimers)}

Ensure your response:
1. Is personalized to the user's specific situation
2. Provides actionable recommendations with clear next steps
3. Explains the reasoning behind each recommendation
4. Identifies potential risks and considerations
5. Includes all required disclaimers naturally within the advice
6. Uses clear, accessible language appropriate for the user's financial literacy level
"""
        
        return full_prompt
    
    def _initialize_templates(self) -> Dict[AdviceCategory, PromptTemplate]:
        """Initialize comprehensive prompt templates"""
        
        templates = {}
        
        # Portfolio Optimization Template
        templates[AdviceCategory.PORTFOLIO_OPTIMIZATION] = PromptTemplate(
            category=AdviceCategory.PORTFOLIO_OPTIMIZATION,
            name="Portfolio Optimization Analysis",
            system_prompt="""You are an expert portfolio manager specializing in modern portfolio theory and asset allocation.
Your expertise includes:
- Strategic and tactical asset allocation
- Risk-adjusted return optimization
- Portfolio rebalancing strategies
- Tax-efficient portfolio construction
- Factor-based investing
- Alternative investments integration""",
            
            user_prompt_template="""Analyze and optimize the following portfolio:

Current Portfolio:
- Total Value: ${portfolio_value:,.0f}
- Current Allocation: {current_allocation}
- Holdings: {holdings}

User Profile:
- Age: {age}
- Risk Tolerance: {risk_tolerance}
- Investment Horizon: {time_horizon} years
- Tax Bracket: {tax_bracket}%
- State: {state}

Goals:
{goals}

Market Conditions:
- Current Market Regime: {market_regime}
- Interest Rates: {interest_rates}
- Economic Outlook: {economic_outlook}

Please provide:
1. Portfolio analysis with risk metrics (Sharpe ratio, max drawdown, etc.)
2. Recommended allocation changes with rationale
3. Specific rebalancing actions to take
4. Tax-efficient implementation strategy
5. Risk management recommendations
6. Performance projection scenarios""",
            
            required_context=['portfolio_value', 'current_allocation', 'age', 'risk_tolerance'],
            compliance_level="standard",
            disclaimers=[
                "Past performance does not guarantee future results",
                "All investments carry risk including loss of principal",
                "Rebalancing may trigger taxable events"
            ],
            examples=[
                {
                    "situation": "Young professional with aggressive risk tolerance",
                    "recommendation": "80% stocks (60% US, 20% International), 15% bonds, 5% alternatives"
                },
                {
                    "situation": "Pre-retiree with moderate risk tolerance",
                    "recommendation": "50% stocks, 40% bonds, 10% alternatives with focus on income generation"
                }
            ]
        )
        
        # Tax Planning Template
        templates[AdviceCategory.TAX_PLANNING] = PromptTemplate(
            category=AdviceCategory.TAX_PLANNING,
            name="Tax Optimization Strategy",
            system_prompt="""You are a tax strategist specializing in investment tax optimization.
Your expertise includes:
- Tax loss harvesting strategies
- Asset location optimization
- Tax-advantaged account maximization
- Roth conversion planning
- Charitable giving strategies
- Estate tax planning
- State tax optimization""",
            
            user_prompt_template="""Develop a tax optimization strategy for:

Tax Situation:
- Filing Status: {filing_status}
- Federal Tax Bracket: {federal_bracket}%
- State: {state} (Tax Rate: {state_tax_rate}%)
- YTD Realized Gains: ${ytd_gains:,.0f}
- YTD Realized Losses: ${ytd_losses:,.0f}

Accounts:
- Taxable: ${taxable_balance:,.0f}
- Traditional IRA/401k: ${traditional_balance:,.0f}
- Roth IRA/401k: ${roth_balance:,.0f}
- HSA: ${hsa_balance:,.0f}

Current Year Income:
- W2 Income: ${w2_income:,.0f}
- Investment Income: ${investment_income:,.0f}
- Other Income: ${other_income:,.0f}

Available Deductions:
{deductions}

Please provide:
1. Tax loss harvesting opportunities
2. Asset location recommendations
3. Contribution prioritization strategy
4. Roth conversion analysis
5. Year-end tax moves
6. Multi-year tax planning strategy""",
            
            required_context=['filing_status', 'federal_bracket', 'state', 'taxable_balance'],
            compliance_level="standard",
            disclaimers=[
                "Tax laws are complex and subject to change",
                "Consult with a qualified tax professional",
                "State tax rules vary significantly"
            ]
        )
        
        # Retirement Planning Template
        templates[AdviceCategory.RETIREMENT_PLANNING] = PromptTemplate(
            category=AdviceCategory.RETIREMENT_PLANNING,
            name="Comprehensive Retirement Plan",
            system_prompt="""You are a retirement planning specialist with expertise in:
- Retirement income planning
- Social Security optimization
- Medicare and healthcare planning
- Pension maximization
- Retirement account strategies
- Longevity risk management
- Retirement lifestyle planning""",
            
            user_prompt_template="""Create a comprehensive retirement plan for:

Current Situation:
- Current Age: {current_age}
- Desired Retirement Age: {retirement_age}
- Current Retirement Savings: ${current_savings:,.0f}
- Monthly Contribution: ${monthly_contribution:,.0f}
- Expected Social Security: ${social_security:,.0f}/year
- Pension Benefits: ${pension:,.0f}/year

Retirement Goals:
- Desired Annual Income: ${desired_income:,.0f}
- Expected Retirement Duration: {life_expectancy_years} years
- Legacy Goals: {legacy_goals}
- Healthcare Considerations: {healthcare_needs}

Current Lifestyle:
- Annual Expenses: ${current_expenses:,.0f}
- Expected Inflation: {inflation_rate}%
- Risk Tolerance in Retirement: {retirement_risk_tolerance}

Please provide:
1. Retirement readiness assessment
2. Savings rate recommendations
3. Investment allocation glide path
4. Social Security claiming strategy
5. Healthcare cost planning
6. Withdrawal strategy in retirement
7. Risk mitigation recommendations
8. Monte Carlo success probability""",
            
            required_context=['current_age', 'retirement_age', 'current_savings', 'desired_income'],
            compliance_level="standard",
            disclaimers=[
                "Retirement projections are estimates based on assumptions",
                "Actual results will vary",
                "Healthcare costs in retirement are uncertain"
            ]
        )
        
        # Debt Management Template
        templates[AdviceCategory.DEBT_MANAGEMENT] = PromptTemplate(
            category=AdviceCategory.DEBT_MANAGEMENT,
            name="Debt Optimization Strategy",
            system_prompt="""You are a debt management expert specializing in:
- Debt prioritization strategies
- Refinancing analysis
- Credit optimization
- Debt consolidation
- Student loan strategies
- Mortgage optimization""",
            
            user_prompt_template="""Develop a debt management strategy for:

Current Debts:
{debt_list}

Financial Situation:
- Monthly Income: ${monthly_income:,.0f}
- Monthly Expenses: ${monthly_expenses:,.0f}
- Emergency Fund: ${emergency_fund:,.0f}
- Credit Score: {credit_score}

Goals:
- Debt Freedom Target: {target_date}
- Other Financial Goals: {other_goals}

Available Resources:
- Extra Monthly Payment Capacity: ${extra_payment:,.0f}
- Available Credit Lines: ${available_credit:,.0f}

Please provide:
1. Optimal debt payoff order (avalanche vs snowball analysis)
2. Refinancing recommendations
3. Consolidation opportunities
4. Monthly payment plan
5. Timeline to debt freedom
6. Credit score improvement strategies""",
            
            required_context=['debt_list', 'monthly_income', 'monthly_expenses'],
            compliance_level="standard",
            disclaimers=[
                "Debt payoff strategies depend on individual circumstances",
                "Refinancing may not always be beneficial",
                "Credit scores are subject to multiple factors"
            ]
        )
        
        # Emergency Fund Template
        templates[AdviceCategory.EMERGENCY_FUND] = PromptTemplate(
            category=AdviceCategory.EMERGENCY_FUND,
            name="Emergency Fund Planning",
            system_prompt="""You are a financial security expert specializing in emergency preparedness and liquidity management.""",
            
            user_prompt_template="""Design an emergency fund strategy for:

Current Situation:
- Monthly Expenses: ${monthly_expenses:,.0f}
- Current Emergency Savings: ${current_emergency:,.0f}
- Job Stability: {job_stability}
- Number of Income Sources: {income_sources}
- Dependents: {dependents}

Risk Factors:
- Health Conditions: {health_considerations}
- Industry Volatility: {industry_risk}
- Geographic Risks: {geographic_risks}

Available Resources:
- Monthly Savings Capacity: ${savings_capacity:,.0f}
- Current Liquid Assets: ${liquid_assets:,.0f}

Please provide:
1. Recommended emergency fund target (months of expenses)
2. Savings timeline and milestones
3. Optimal account types and locations
4. Liquidity ladder strategy
5. Risk-specific adjustments
6. Integration with other financial goals""",
            
            required_context=['monthly_expenses', 'current_emergency', 'job_stability'],
            compliance_level="educational",
            disclaimers=[
                "Emergency fund needs vary by individual situation",
                "Consider your specific risk factors"
            ]
        )
        
        return templates
    
    def _initialize_disclaimers(self) -> Dict[str, List[str]]:
        """Initialize compliance disclaimers by category"""
        
        return {
            "universal": [
                "This information is for educational purposes only and should not be considered personalized financial advice.",
                "Past performance does not guarantee future results.",
                "All investments involve risk, including the potential loss of principal.",
                "Tax implications vary by individual situation. Consult a tax professional.",
                "Consider consulting with a qualified financial advisor before making investment decisions."
            ],
            
            "investment": [
                "Investment returns are not guaranteed and you may lose money.",
                "Diversification does not ensure a profit or protect against loss.",
                "Asset allocation does not guarantee investment returns.",
                "Market volatility can significantly impact short-term results."
            ],
            
            "tax": [
                "Tax laws are complex and subject to change.",
                "State tax laws vary significantly.",
                "Tax strategies should be reviewed with a qualified tax professional.",
                "IRS rules and regulations may affect strategy implementation."
            ],
            
            "retirement": [
                "Retirement projections are hypothetical and for illustrative purposes only.",
                "Actual results will vary based on market conditions and personal circumstances.",
                "Social Security benefits are subject to change.",
                "Healthcare costs in retirement are uncertain and typically increase with age."
            ],
            
            "regulatory": [
                "This communication complies with applicable regulatory requirements.",
                "No guarantee of specific outcomes or returns.",
                "Information provided is believed to be accurate but not warranted.",
                "Regulatory requirements may limit certain recommendations."
            ]
        }
    
    def _format_user_prompt(self, template: PromptTemplate, context: Dict[str, Any]) -> str:
        """Format user prompt with context values"""
        
        try:
            # Create a safe context with default values
            safe_context = {}
            for key in template.required_context:
                safe_context[key] = context.get(key, 'Not provided')
            
            # Add any additional context
            safe_context.update(context)
            
            # Format the template
            return template.user_prompt_template.format(**safe_context)
        
        except KeyError as e:
            # Return template with placeholders for missing values
            return template.user_prompt_template.format_map(DefaultDict(lambda: '[MISSING]'))
    
    def _format_examples(self, examples: List[Dict[str, str]]) -> str:
        """Format examples for inclusion in prompt"""
        
        if not examples:
            return ""
        
        formatted = "EXAMPLES:\n"
        for i, example in enumerate(examples, 1):
            formatted += f"\nExample {i}:\n"
            formatted += f"Situation: {example.get('situation', 'N/A')}\n"
            formatted += f"Recommendation: {example.get('recommendation', 'N/A')}\n"
        
        return formatted
    
    def _get_compliance_guidelines(self) -> str:
        """Get strict compliance guidelines"""
        
        return """
STRICT COMPLIANCE REQUIREMENTS:
1. Do not guarantee any investment returns or outcomes
2. Do not provide specific security recommendations (individual stocks/bonds)
3. Always emphasize risks alongside potential benefits
4. Include appropriate disclaimers for the advice category
5. Recommend consultation with licensed professionals when appropriate
6. Ensure suitability of recommendations for the client's situation
7. Disclose any assumptions made in projections or calculations
8. Avoid any language that could be construed as a guarantee
9. Clearly distinguish between education and personalized advice
10. Include regulatory disclosures as required
"""
    
    def _get_required_disclaimers(
        self,
        category: AdviceCategory,
        compliance_level: str
    ) -> List[str]:
        """Get required disclaimers for category and compliance level"""
        
        disclaimers = []
        
        # Always include universal disclaimers
        disclaimers.extend(self.compliance_disclaimers["universal"])
        
        # Add category-specific disclaimers
        if category in [
            AdviceCategory.PORTFOLIO_OPTIMIZATION,
            AdviceCategory.INVESTMENT_STRATEGY
        ]:
            disclaimers.extend(self.compliance_disclaimers["investment"])
        
        elif category == AdviceCategory.TAX_PLANNING:
            disclaimers.extend(self.compliance_disclaimers["tax"])
        
        elif category == AdviceCategory.RETIREMENT_PLANNING:
            disclaimers.extend(self.compliance_disclaimers["retirement"])
        
        # Add regulatory disclaimers for strict compliance
        if compliance_level == "strict":
            disclaimers.extend(self.compliance_disclaimers["regulatory"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_disclaimers = []
        for d in disclaimers:
            if d not in seen:
                seen.add(d)
                unique_disclaimers.append(d)
        
        return unique_disclaimers
    
    def _get_default_prompt(self, context: Dict[str, Any]) -> str:
        """Get default prompt when no specific template matches"""
        
        return f"""
You are a knowledgeable financial advisor providing educational information.

User Context:
{json.dumps(context, indent=2)}

Please provide helpful financial guidance that:
1. Addresses the user's question or concern
2. Provides educational value
3. Suggests general strategies (not specific recommendations)
4. Identifies important considerations
5. Recommends appropriate professional consultation

Remember to:
- Keep advice general and educational
- Include appropriate disclaimers
- Suggest consulting with licensed professionals for specific advice
"""
    
    def get_response_template(self, category: AdviceCategory) -> str:
        """Get structured response template for consistency"""
        
        templates = {
            AdviceCategory.PORTFOLIO_OPTIMIZATION: """
## Portfolio Analysis & Recommendations

### Current Portfolio Assessment
[Analysis of current allocation, risk metrics, and performance]

### Optimization Recommendations
1. **Asset Allocation Adjustments**
   - [Specific changes with rationale]
   
2. **Risk Management**
   - [Risk mitigation strategies]
   
3. **Implementation Plan**
   - [Step-by-step actions]

### Expected Outcomes
- Risk-Return Profile: [Description]
- Time Horizon Alignment: [Assessment]
- Tax Efficiency: [Considerations]

### Important Considerations
[Risks, assumptions, and caveats]

### Next Steps
[Prioritized action items]
""",
            
            AdviceCategory.TAX_PLANNING: """
## Tax Optimization Strategy

### Current Tax Situation Analysis
[Overview of current tax position]

### Optimization Opportunities
1. **Immediate Actions**
   - [Current year strategies]
   
2. **Year-End Planning**
   - [Before December 31 actions]
   
3. **Multi-Year Strategy**
   - [Long-term tax planning]

### Estimated Tax Savings
- Current Year: [Estimate]
- 5-Year Projection: [Estimate]

### Implementation Timeline
[Month-by-month action plan]

### Important Tax Considerations
[Compliance notes and warnings]
""",
            
            AdviceCategory.RETIREMENT_PLANNING: """
## Comprehensive Retirement Plan

### Retirement Readiness Score
[Current status assessment]

### Projected Retirement Income
- Social Security: [Amount and strategy]
- Retirement Accounts: [Withdrawal strategy]
- Other Sources: [Pensions, annuities, etc.]

### Savings & Investment Strategy
1. **Contribution Plan**
   - [Specific amounts and accounts]
   
2. **Investment Allocation**
   - [Age-appropriate strategy]

### Risk Analysis
- Success Probability: [Monte Carlo results]
- Key Risks: [Longevity, inflation, market]

### Healthcare Planning
[Medicare and health cost considerations]

### Action Plan
[Prioritized steps with timeline]
"""
        }
        
        return templates.get(category, """
## Financial Guidance

### Situation Analysis
[Current situation assessment]

### Recommendations
[Numbered list of suggestions]

### Considerations
[Important factors to consider]

### Next Steps
[Action items]

### Disclaimers
[Required disclaimers]
""")

class DefaultDict(dict):
    """Helper class for safe dictionary formatting"""
    def __init__(self, default_value):
        self.default_value = default_value
        super().__init__()
    
    def __missing__(self, key):
        return self.default_value
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAFE AI FINANCIAL ADVISOR
Educational guidance without risky investment advice
"""
import os
from typing import Dict, List, Optional
from portfolio_tracker import PortfolioTracker
import numpy as np
from datetime import datetime

class FinancialAdvisorAI:
    """
    Safe AI financial advisor that provides educational guidance
    based on established financial principles.
    """
    
    def __init__(self, portfolio_tracker: Optional[PortfolioTracker] = None):
        self.tracker = portfolio_tracker or PortfolioTracker()
        self.safety_level = "high"  # Always start with maximum safety
        
        # Track stock mentions to prevent excessive speculation
        self.stock_mention_count = {}
        self.max_stock_mentions_per_week = 3
    
    def analyze_portfolio_health(self) -> Dict[str, any]:
        """Analyze portfolio health based on established metrics"""
        if self.tracker.holdings is None:
            return {"error": "No portfolio loaded"}
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "risk_factors": [],
            "strengths": [],
            "educational_points": [],
            "action_items": []
        }
        
        # Calculate portfolio metrics
        holdings = self.tracker.holdings
        totals = self.tracker.calculate_portfolio()
        
        # 1. Concentration Risk Analysis
        position_weights = {}
        total_value = totals['Total Market Value']
        
        for _, row in holdings.iterrows():
            weight = (row['Market Value'] / total_value) * 100
            position_weights[row['Symbol']] = weight
            
            if weight > 25:
                analysis['risk_factors'].append({
                    'type': 'concentration_risk',
                    'severity': 'high',
                    'message': f"{row['Symbol']} represents {weight:.1f}% of portfolio",
                    'education': "Diversification reduces risk. Most advisors recommend no single position exceed 10-15% of portfolio."
                })
            elif weight > 15:
                analysis['risk_factors'].append({
                    'type': 'concentration_risk',
                    'severity': 'medium',
                    'message': f"{row['Symbol']} is {weight:.1f}% of portfolio",
                    'education': "Consider if this concentration aligns with your risk tolerance."
                })
        
        # 2. Diversification Analysis
        num_positions = len(holdings)
        if num_positions < 5:
            analysis['risk_factors'].append({
                'type': 'insufficient_diversification',
                'severity': 'high',
                'message': f"Only {num_positions} positions in portfolio",
                'education': "A well-diversified portfolio typically holds 15-30 different positions across sectors."
            })
        elif num_positions < 10:
            analysis['educational_points'].append(
                "Consider adding more positions for better diversification. ETFs can provide instant diversification."
            )
        else:
            analysis['strengths'].append(f"Good position count ({num_positions}) for diversification")
        
        # 3. Performance Analysis
        total_gain_pct = totals['Total Gain %']
        if total_gain_pct > 20:
            analysis['strengths'].append(f"Strong performance: {total_gain_pct:.1f}% unrealized gains")
            analysis['educational_points'].append(
                "Remember: Past performance doesn't guarantee future results. Consider rebalancing if positions have drifted from targets."
            )
        elif total_gain_pct < -10:
            analysis['educational_points'].append(
                "Market downturns are normal. Historical data shows patient investors are rewarded over long time horizons."
            )
        
        # 4. Provide Safe, Educational Action Items
        analysis['action_items'] = self._generate_safe_recommendations(position_weights, totals)
        
        return analysis
    
    def _generate_safe_recommendations(self, weights: Dict, totals: Dict) -> List[Dict]:
        """Generate safe, educational recommendations"""
        recommendations = []
        
        # Always start with education
        recommendations.append({
            'priority': 'info',
            'action': 'Review your investment goals',
            'rationale': 'Ensure your portfolio aligns with your time horizon and risk tolerance'
        })
        
        # Check for rebalancing needs
        max_weight = max(weights.values()) if weights else 0
        if max_weight > 25:
            recommendations.append({
                'priority': 'medium',
                'action': 'Consider rebalancing',
                'rationale': f'Your largest position is {max_weight:.1f}% of portfolio. Rebalancing helps maintain target risk levels.',
                'education': 'Rebalancing involves selling winners and buying losers to maintain target allocations.'
            })
        
        # Tax loss harvesting opportunity (safe recommendation)
        for _, row in self.tracker.holdings.iterrows():
            if row.get('Unrealized P&L', 0) < -100:  # Losses over $100
                recommendations.append({
                    'priority': 'low',
                    'action': f"Review {row['Symbol']} for tax loss harvesting",
                    'rationale': 'Realizing losses can offset gains for tax purposes',
                    'warning': 'Be aware of wash sale rules (no repurchase within 30 days)'
                })
                break  # Only suggest one at a time
        
        return recommendations
    
    def explain_financial_concept(self, concept: str) -> str:
        """Explain financial concepts in simple terms"""
        
        concepts = {
            'diversification': """
Diversification means not putting all your eggs in one basket. By owning different types of investments 
(stocks, bonds, different sectors), you reduce the risk that one bad investment ruins your portfolio.
Think of it like a balanced diet - you need different food groups for good health.
            """,
            
            'expense_ratio': """
Expense ratio is the annual fee charged by funds (ETFs/mutual funds) expressed as a percentage.
For example, a 0.10% expense ratio means you pay $1 per year for every $1,000 invested.
Lower is generally better - many good index funds charge less than 0.20%.
            """,
            
            'compound_interest': """
Compound interest is earning returns on your returns. If you invest $1,000 and earn 10% ($100),
next year you earn returns on $1,100, not just the original $1,000. Over time, this snowball
effect is powerful. Einstein allegedly called it "the eighth wonder of the world."
            """,
            
            'dollar_cost_averaging': """
Dollar-cost averaging means investing a fixed amount regularly regardless of market conditions.
For example, investing $500 monthly. When prices are high, you buy fewer shares. When low, you buy more.
This strategy reduces the impact of market timing and is great for beginners.
            """,
            
            'rebalancing': """
Rebalancing means adjusting your portfolio back to target allocations. If you want 60% stocks and 40% bonds,
but stocks grew to 70%, you'd sell some stocks and buy bonds to get back to 60/40.
This naturally enforces "buy low, sell high" discipline.
            """,
            
            'tax_loss_harvesting': """
Tax loss harvesting means selling investments at a loss to offset capital gains taxes.
If you have $1,000 in gains and sell something for a $1,000 loss, they cancel out for tax purposes.
Warning: Can't repurchase the same investment for 30 days (wash sale rule).
            """
        }
        
        concept_lower = concept.lower().replace(' ', '_').replace('-', '_')
        
        if concept_lower in concepts:
            return concepts[concept_lower].strip()
        else:
            return f"I don't have a specific explanation for '{concept}', but I recommend researching it on reputable financial education sites like Investopedia or Bogleheads."
    
    def get_portfolio_allocation_advice(self) -> Dict[str, any]:
        """Provide safe allocation guidance based on age and risk tolerance"""
        
        return {
            'classic_strategies': {
                'three_fund_portfolio': {
                    'description': 'Simple, diversified portfolio popularized by Bogleheads',
                    'allocation': {
                        'US Total Market': '60%',
                        'International Markets': '30%',
                        'Bonds': '10%'
                    },
                    'example_etfs': ['VTI', 'VTIAX', 'BND'],
                    'pros': 'Simple, low-cost, broadly diversified',
                    'cons': 'No tactical adjustments, may be too simple for some'
                },
                
                'age_in_bonds': {
                    'description': 'Your age = percentage in bonds (e.g., 30 years old = 30% bonds)',
                    'rationale': 'Automatically becomes more conservative as you age',
                    'example': 'At 40: 60% stocks, 40% bonds'
                },
                
                'target_date_approach': {
                    'description': 'Single fund that automatically adjusts over time',
                    'example': 'Vanguard Target Retirement 2055 Fund',
                    'pros': 'Completely hands-off, automatic rebalancing',
                    'cons': 'May not match individual risk tolerance perfectly'
                }
            },
            
            'risk_considerations': [
                'Your ability to take risk (time horizon, job stability)',
                'Your willingness to take risk (emotional tolerance)',
                'Need to take risk (required returns to meet goals)'
            ],
            
            'disclaimer': 'These are educational examples, not personalized advice. Consider consulting a fee-only financial advisor for personalized recommendations.'
        }
    
    def analyze_tax_optimization_opportunities(self) -> Dict[str, any]:
        """Identify tax optimization opportunities"""
        
        if self.tracker.holdings is None:
            return {"error": "No portfolio loaded"}
        
        opportunities = {
            'tax_loss_harvesting': [],
            'account_placement': [],
            'contribution_strategies': []
        }
        
        # Identify tax loss harvesting opportunities
        for _, row in self.tracker.holdings.iterrows():
            unrealized_pl = row.get('Unrealized P&L', 0)
            if unrealized_pl < -50:  # Losses over $50
                opportunities['tax_loss_harvesting'].append({
                    'symbol': row['Symbol'],
                    'unrealized_loss': f"${abs(unrealized_pl):.2f}",
                    'action': 'Consider selling to realize loss',
                    'warning': 'Remember 30-day wash sale rule',
                    'alternative': f'Could replace with similar but not identical ETF'
                })
        
        # Account placement advice (educational)
        opportunities['account_placement'] = [
            {
                'asset_type': 'Tax-inefficient (bonds, REITs)',
                'best_account': 'Tax-deferred (401k, Traditional IRA)',
                'reason': 'Interest taxed as ordinary income'
            },
            {
                'asset_type': 'Tax-efficient (index funds)',
                'best_account': 'Taxable account',
                'reason': 'Qualified dividends and long-term capital gains get preferential rates'
            },
            {
                'asset_type': 'High-growth stocks',
                'best_account': 'Roth IRA',
                'reason': 'Tax-free growth and withdrawals in retirement'
            }
        ]
        
        # Contribution strategy
        opportunities['contribution_strategies'] = [
            {
                'priority': 1,
                'action': 'Contribute to 401(k) up to employer match',
                'reason': 'Free money - 100% immediate return'
            },
            {
                'priority': 2,
                'action': 'Max out HSA if available',
                'reason': 'Triple tax advantage: deductible, tax-free growth, tax-free withdrawals for medical'
            },
            {
                'priority': 3,
                'action': 'Consider Roth IRA if income eligible',
                'reason': 'Tax-free growth and withdrawals in retirement'
            },
            {
                'priority': 4,
                'action': 'Max out remaining 401(k) space',
                'reason': 'Reduce current taxable income'
            }
        ]
        
        return opportunities
    
    def generate_market_context(self, user_portfolio_performance: float) -> str:
        """Provide market context without speculation"""
        
        context = f"""
Your portfolio performance: {user_portfolio_performance:.1f}%

Historical Context (Educational):
- S&P 500 average annual return (1926-2023): ~10%
- Typical year sees 3-4 corrections of 5-10%
- Bear markets (20%+ decline) occur every 3-4 years on average
- Markets have recovered from every downturn in history

Important Reminders:
1. Time in the market beats timing the market
2. Your investment timeline matters more than daily movements
3. Diversification is your best defense against uncertainty
4. Costs matter - minimize fees and taxes when possible

This is educational context, not a prediction of future performance.
        """
        
        return context.strip()


def demonstrate_safe_advisor():
    """Demonstrate the safe AI financial advisor"""
    print("\n" + "="*60)
    print("SAFE AI FINANCIAL ADVISOR DEMO")
    print("="*60)
    
    # Load sample portfolio
    tracker = PortfolioTracker()
    tracker.load_holdings('docs/holdings_sample.csv')
    tracker.update_prices()
    tracker.calculate_portfolio()
    
    # Create advisor
    advisor = FinancialAdvisorAI(tracker)
    
    # 1. Portfolio Health Analysis
    print("\n1. PORTFOLIO HEALTH ANALYSIS")
    print("-" * 40)
    health = advisor.analyze_portfolio_health()
    
    if health.get('risk_factors'):
        print("\nRisk Factors:")
        for risk in health['risk_factors']:
            print(f"  • {risk['message']}")
            print(f"    Education: {risk['education']}")
    
    if health.get('strengths'):
        print("\nStrengths:")
        for strength in health['strengths']:
            print(f"  ✓ {strength}")
    
    if health.get('action_items'):
        print("\nRecommended Actions:")
        for item in health['action_items']:
            print(f"  [{item['priority']}] {item['action']}")
            print(f"    Rationale: {item['rationale']}")
    
    # 2. Educational Concepts
    print("\n2. FINANCIAL EDUCATION")
    print("-" * 40)
    concepts = ['diversification', 'tax_loss_harvesting', 'expense_ratio']
    for concept in concepts:
        print(f"\nWhat is {concept.replace('_', ' ').title()}?")
        print(advisor.explain_financial_concept(concept))
    
    # 3. Tax Optimization
    print("\n3. TAX OPTIMIZATION OPPORTUNITIES")
    print("-" * 40)
    tax_ops = advisor.analyze_tax_optimization_opportunities()
    
    if tax_ops['tax_loss_harvesting']:
        print("\nTax Loss Harvesting Opportunities:")
        for opp in tax_ops['tax_loss_harvesting']:
            print(f"  • {opp['symbol']}: {opp['unrealized_loss']} loss")
            print(f"    {opp['warning']}")
    
    print("\nContribution Priority (Educational):")
    for strategy in tax_ops['contribution_strategies']:
        print(f"  {strategy['priority']}. {strategy['action']}")
        print(f"     Why: {strategy['reason']}")
    
    # 4. Market Context
    print("\n4. MARKET CONTEXT")
    print("-" * 40)
    totals = tracker.calculate_portfolio()
    context = advisor.generate_market_context(totals['Total Gain %'])
    print(context)
    
    print("\n" + "="*60)
    print("Remember: This is educational guidance, not personalized advice.")
    print("Always consult with qualified professionals for your specific situation.")
    print("="*60)


if __name__ == "__main__":
    demonstrate_safe_advisor()
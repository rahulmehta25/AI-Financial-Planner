"""
AI-powered financial advice endpoints
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import User

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    context: str = "general"


@router.post("/chat")
async def ai_chat(
    message_data: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Chat with AI financial advisor"""
    # Mock AI response for now
    responses = {
        "emergency fund": "Based on your income of $6,500/month, I recommend maintaining 3-6 months of expenses as an emergency fund. That would be approximately $12,600-$25,200. You're currently at $15,000, which is excellent progress!",
        "retirement": "Your retirement savings of $85,000 is a great start! To reach $500,000 by retirement, consider increasing your monthly contributions. The power of compound interest will help your money grow over time.",
        "budget": "Your current savings rate of 35.4% is excellent! Most financial experts recommend 20% savings rate. You're doing great with your budgeting.",
        "default": "I'm here to help with your financial planning! Ask me about budgeting, saving, investments, or any financial goals you'd like to discuss."
    }
    
    # Simple keyword matching for demo
    user_message = message_data.message.lower()
    response_key = "default"
    
    for key in responses.keys():
        if key in user_message:
            response_key = key
            break
    
    return {
        "response": responses[response_key],
        "timestamp": datetime.utcnow().isoformat(),
        "context": message_data.context,
        "suggestions": [
            "Tell me about my emergency fund progress",
            "How am I doing with retirement savings?",
            "What's my current savings rate?",
            "Should I increase my investment contributions?"
        ]
    }


@router.get("/recommendations")
async def get_ai_recommendations(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get personalized AI financial recommendations"""
    return {
        "recommendations": [
            {
                "id": "rec-1",
                "type": "savings",
                "title": "Increase Emergency Fund",
                "description": "Consider increasing your emergency fund allocation by 5% this month to reach your $25,000 target faster.",
                "priority": "medium",
                "impact": "high",
                "estimated_benefit": "$200/month additional savings",
                "action_required": "Adjust automatic transfer to savings account"
            },
            {
                "id": "rec-2", 
                "type": "investment",
                "title": "Rebalance Portfolio",
                "description": "Your investment portfolio has drifted from your target allocation. Consider rebalancing to maintain optimal risk-return profile.",
                "priority": "low",
                "impact": "medium", 
                "estimated_benefit": "2-3% improved annual returns",
                "action_required": "Review and adjust investment allocations"
            },
            {
                "id": "rec-3",
                "type": "tax_optimization",
                "title": "Tax-Loss Harvesting",
                "description": "You have some underperforming investments that could be sold to offset capital gains and reduce tax liability.",
                "priority": "high",
                "impact": "high",
                "estimated_benefit": "$1,200 tax savings this year",
                "action_required": "Review investment portfolio with tax advisor"
            }
        ],
        "summary": {
            "total_recommendations": 3,
            "high_priority": 1,
            "medium_priority": 1,
            "low_priority": 1,
            "estimated_annual_benefit": 15000
        }
    }


@router.get("/insights")  
async def get_ai_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get AI-generated financial insights"""
    return {
        "insights": [
            {
                "id": "insight-1",
                "category": "spending_patterns",
                "title": "Spending Trend Analysis",
                "insight": "Your grocery spending has increased by 12% over the last 3 months, likely due to inflation. Consider meal planning to optimize costs.",
                "data_points": ["grocery_spending: +12%", "inflation_rate: 8.2%"],
                "confidence": 0.85
            },
            {
                "id": "insight-2",
                "category": "savings_opportunity", 
                "title": "Subscription Optimization",
                "insight": "You have 7 active subscriptions totaling $89/month. 3 haven't been used in 60+ days and could be canceled to save $35/month.",
                "data_points": ["unused_subscriptions: 3", "potential_savings: $420/year"],
                "confidence": 0.92
            },
            {
                "id": "insight-3",
                "category": "investment_performance",
                "title": "Portfolio Performance",
                "insight": "Your investment portfolio is outperforming the S&P 500 by 1.8% this year, showing strong asset allocation decisions.",
                "data_points": ["portfolio_return: 12.3%", "sp500_return: 10.5%"],
                "confidence": 0.98
            }
        ],
        "summary": {
            "total_insights": 3,
            "average_confidence": 0.92,
            "categories": ["spending_patterns", "savings_opportunity", "investment_performance"]
        }
    }


@router.get("/analysis")
async def get_financial_analysis(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get comprehensive AI financial analysis"""
    return {
        "analysis": {
            "financial_health_score": 82,
            "risk_profile": "moderate",
            "strengths": [
                "High savings rate (35.4%)",
                "Diversified investment portfolio", 
                "Emergency fund in progress",
                "Consistent income stream"
            ],
            "areas_for_improvement": [
                "Increase emergency fund to 6 months expenses",
                "Consider tax-advantaged accounts",
                "Optimize subscription spending"
            ],
            "goal_progress": {
                "emergency_fund": {
                    "progress": 60.0,
                    "on_track": True,
                    "projected_completion": "2024-08-15"
                },
                "retirement": {
                    "progress": 17.0,
                    "on_track": True,
                    "projected_completion": "2054-01-01"
                },
                "house_down_payment": {
                    "progress": 30.0,
                    "on_track": False,
                    "projected_completion": "2025-09-15",
                    "recommendation": "Increase monthly contribution by $500"
                }
            },
            "cash_flow_analysis": {
                "monthly_surplus": 2300.00,
                "debt_to_income_ratio": 0.15,
                "savings_rate": 0.354,
                "expense_categories": {
                    "needs": 3200.00,  # 76% of income
                    "wants": 1000.00,  # 15% of income
                    "savings": 2300.00  # 35% of income
                }
            }
        },
        "recommendations": [
            "Continue current savings rate - it's excellent!",
            "Consider increasing retirement contributions by $200/month",
            "Review and optimize monthly subscriptions",
            "Maintain current investment allocation strategy"
        ],
        "generated_at": datetime.utcnow().isoformat()
    }
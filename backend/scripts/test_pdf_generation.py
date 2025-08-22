"""
Test script for PDF generation functionality
Run this to test the PDF generation system independently
"""

import asyncio
import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.pdf_generator import PDFGeneratorService, FinancialPlanData
from app.services.chart_generator import ChartGeneratorService

# Mock data classes to simulate database models
class MockUser:
    def __init__(self):
        self.id = "12345678-1234-5678-9012-123456789012"
        self.first_name = "John"
        self.last_name = "Doe"
        self.email = "john.doe@example.com"

class MockFinancialProfile:
    def __init__(self):
        self.user_id = "12345678-1234-5678-9012-123456789012"
        self.date_of_birth = date(1988, 5, 15)
        self.annual_income = Decimal('75000')
        self.monthly_expenses = Decimal('4500')
        self.liquid_assets = Decimal('25000')
        self.retirement_accounts = Decimal('45000')
        self.real_estate_value = Decimal('250000')
        self.other_investments = Decimal('15000')
        self.personal_property_value = Decimal('25000')
        self.mortgage_balance = Decimal('180000')
        self.credit_card_debt = Decimal('3500')
        self.student_loans = Decimal('12000')
        self.auto_loans = Decimal('8000')
        self.other_debts = Decimal('2000')
        self.risk_tolerance = "moderate"
        self.investment_experience = "intermediate"
        self.employment_status = "employed"
        
    @property
    def age(self):
        return 36
    
    @property
    def net_worth(self):
        total_assets = float(
            self.liquid_assets + self.retirement_accounts + 
            self.real_estate_value + self.other_investments + 
            self.personal_property_value
        )
        total_liabilities = float(
            self.mortgage_balance + self.credit_card_debt + 
            self.student_loans + self.auto_loans + self.other_debts
        )
        return total_assets - total_liabilities
    
    @property
    def debt_to_income_ratio(self):
        debt = float(self.credit_card_debt + self.student_loans + self.auto_loans + self.other_debts)
        return debt / float(self.annual_income)

class MockGoal:
    def __init__(self, name, target_amount, current_amount, target_date, monthly_contribution):
        self.id = f"goal-{name.lower().replace(' ', '-')}"
        self.name = name
        self.target_amount = Decimal(str(target_amount))
        self.current_amount = Decimal(str(current_amount))
        self.target_date = target_date
        self.monthly_contribution = Decimal(str(monthly_contribution))
        self.status = "active"
        
    @property
    def progress_percentage(self):
        if self.target_amount > 0:
            return min(100, (float(self.current_amount) / float(self.target_amount)) * 100)
        return 0
    
    @property
    def progress_status(self):
        if self.progress_percentage >= 75:
            return "on_track"
        elif self.progress_percentage >= 50:
            return "behind"
        else:
            return "significantly_behind"


async def test_chart_generation():
    """Test chart generation functionality"""
    print("Testing chart generation...")
    
    chart_service = ChartGeneratorService()
    
    # Test net worth projection
    projection_data = [
        {'year': 2024 + i, 'net_worth': 160000 * (1.07 ** i)}
        for i in range(10)
    ]
    
    net_worth_chart = chart_service.generate_net_worth_projection(
        projection_data, 160000, "Net Worth Projection Test"
    )
    print(f"✓ Net worth chart generated: {len(net_worth_chart)} chars")
    
    # Test goals progress
    goals_data = [
        {'name': 'Emergency Fund', 'progress_percentage': 75.0},
        {'name': 'Retirement', 'progress_percentage': 45.0},
        {'name': 'House Down Payment', 'progress_percentage': 30.0}
    ]
    
    goals_chart = chart_service.generate_goal_progress_chart(goals_data)
    print(f"✓ Goals progress chart generated: {len(goals_chart)} chars")
    
    # Test asset allocation
    allocation_data = {
        'Cash & Savings': 25000,
        'Retirement Accounts': 45000,
        'Real Estate': 250000,
        'Other Investments': 15000
    }
    
    allocation_chart = chart_service.generate_asset_allocation_pie(allocation_data)
    print(f"✓ Asset allocation chart generated: {len(allocation_chart)} chars")
    
    print("Chart generation tests completed successfully!")
    return True


async def test_pdf_generation():
    """Test PDF generation functionality"""
    print("\nTesting PDF generation...")
    
    # Create mock data
    user = MockUser()
    financial_profile = MockFinancialProfile()
    
    goals = [
        MockGoal("Emergency Fund", 30000, 22500, date(2024, 12, 31), 500),
        MockGoal("Retirement Savings", 100000, 45000, date(2034, 12, 31), 800),
        MockGoal("House Down Payment", 50000, 15000, date(2026, 6, 30), 1200)
    ]
    
    # Create simulation results
    simulation_results = {
        'net_worth_projection': [
            {'year': 2024 + i, 'net_worth': financial_profile.net_worth * (1.07 ** i)}
            for i in range(10)
        ],
        'monte_carlo': {
            'years': list(range(2024, 2034)),
            'percentile_10': [financial_profile.net_worth * (1.04 ** i) for i in range(10)],
            'percentile_50': [financial_profile.net_worth * (1.07 ** i) for i in range(10)],
            'percentile_90': [financial_profile.net_worth * (1.10 ** i) for i in range(10)]
        },
        'cash_flow': [
            {'month': f'2024-{i:02d}', 'income': 6250, 'expenses': 4500}
            for i in range(1, 13)
        ]
    }
    
    # AI narrative
    ai_narrative = """
    Based on your moderate risk profile and current financial position, you are well-positioned 
    to achieve your long-term financial goals. Your debt-to-income ratio of 34% is within 
    healthy ranges, and your current savings rate of 18% demonstrates strong financial discipline.
    
    Key strengths include your diversified asset base and consistent contribution to retirement 
    accounts. Areas for improvement include building your emergency fund to 6 months of expenses 
    and considering tax-loss harvesting strategies for your investment portfolio.
    
    With continued disciplined saving and strategic investment allocation, you should be able 
    to achieve financial independence by age 55 while maintaining your current lifestyle.
    """
    
    # Recommendations
    recommendations = [
        {
            "title": "Emergency Fund Completion",
            "description": "Complete your emergency fund to reach 6 months of expenses ($27,000) within the next 10 months.",
            "priority": "high",
            "action_items": [
                "Increase monthly emergency fund contribution to $450",
                "Consider high-yield savings account for emergency funds",
                "Set up automatic transfers to build consistency"
            ]
        },
        {
            "title": "Investment Portfolio Optimization",
            "description": "Rebalance your investment portfolio to align with your moderate risk tolerance.",
            "priority": "medium",
            "action_items": [
                "Review current asset allocation quarterly",
                "Consider low-cost index funds for core holdings",
                "Implement tax-loss harvesting strategies"
            ]
        },
        {
            "title": "Retirement Acceleration",
            "description": "Increase retirement contributions to take advantage of compound growth.",
            "priority": "medium",
            "action_items": [
                "Maximize employer 401(k) match if available",
                "Consider Roth IRA contributions for tax diversification",
                "Review contribution limits annually"
            ]
        }
    ]
    
    # Create plan data
    plan_data = FinancialPlanData(
        user=user,
        financial_profile=financial_profile,
        goals=goals,
        simulation_results=simulation_results,
        ai_narrative=ai_narrative.strip(),
        recommendations=recommendations
    )
    
    # Initialize PDF service
    pdf_service = PDFGeneratorService()
    
    # Test different formats
    formats_to_test = [
        ("executive_summary", "Executive Summary"),
        ("professional", "Professional Report"),
        ("detailed", "Detailed Analysis")
    ]
    
    for format_type, format_name in formats_to_test:
        try:
            print(f"Generating {format_name}...")
            start_time = datetime.now()
            
            pdf_bytes = await pdf_service.generate_comprehensive_plan_pdf(
                plan_data, 
                format_type=format_type
            )
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Save PDF to file
            filename = f"test_financial_plan_{format_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(os.path.dirname(__file__), filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            
            file_size_kb = len(pdf_bytes) / 1024
            
            print(f"✓ {format_name} generated successfully!")
            print(f"  - File: {filename}")
            print(f"  - Size: {file_size_kb:.1f} KB")
            print(f"  - Generation time: {generation_time:.2f} seconds")
            print(f"  - Saved to: {filepath}")
            
        except Exception as e:
            print(f"✗ Error generating {format_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\nPDF generation tests completed!")
    return True


async def main():
    """Main test function"""
    print("=== Financial Planning PDF Generation Test ===")
    print(f"Test started at: {datetime.now()}")
    print()
    
    try:
        # Test chart generation
        await test_chart_generation()
        
        # Test PDF generation
        await test_pdf_generation()
        
        print("\n=== All Tests Completed Successfully! ===")
        print("Check the generated PDF files in the scripts directory.")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
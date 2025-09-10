#!/usr/bin/env python3
"""
Test script for screenshot-based PDF generation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the chatbot directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.simple_pdf_generator import SimplePDFGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_screenshot_pdf_generation():
    """Test the screenshot-based PDF generation"""
    print("🧪 Testing Screenshot-Based PDF Generation...")
    
    # Sample portfolio data
    portfolio_data = {
        'client_name': 'Test Client',
        'age': 38,
        'marital_status': 'married',
        'dependents': 2,
        'health_status': 'good',
        'tobacco_use': 'no',
        'total_assets': 2214840,
        'investable_portfolio': 491800,
        'total_net_worth': 1355640,
        'liquid_assets': 61800,
        'monthly_income': 22167,
        'monthly_expenses': 7000,
        'equity_allocation': 1506091,
        'fixed_income_allocation': 398671,
        'real_estate_allocation': 1650000,
        'cash_allocation': 61800,
        'alternative_allocation': 0,
        'retirement_accounts': 430000,
        'taxable_accounts': 129000,
        'education_accounts': 45000,
        'liabilities_total': 859200,
        'risk_tolerance': 'moderate',
        'investment_horizon': 20,
        'retirement_target': 4000000,
        'legacy_goals': 0,
        'current_life_insurance': 1000000,
        'individual_life': 1000000,
        'group_life': 0,
        'income_replacement_years': 10,
        'cash_value_importance': 'yes',
        'permanent_coverage': 'yes',
        'coverage_goals': ['income_replacement', 'debt_payoff', 'education', 'funeral', 'legacy'],
        'other_coverage_goal': '',
        'recommended_coverage': 3990060,
        'gap': 2990060,
        'duration_years': 25,
        'product_recommendation': 'JPM TermVest+ IUL Track',
        'rationale': 'At age 38.0 with $266,004 annual income and 2.0 dependents, you\'re an ideal candidate for the IUL Track. Start with term coverage and convert to permanent coverage as your financial situation allows, building cash value for retirement and legacy planning.',
        'portfolio_metrics': {
            'total_assets': 491800.0,
            'asset_allocation_percentages': {
                'equity': 68.0, 'fixed_income': 18.0, 'cash': 4.0, 'alternative': 0.0, 'real_estate': 10.0
            },
            'portfolio_health_score': 68,
            'risk_level': 'moderate',
            'risk_score': 45,
            'liquidity_ratio': 8.8,
            'diversification_score': 75,
            'concentration_risks': [],
            'rebalancing_needs': [],
            'industry_benchmarks': {}
        },
        'life_insurance_needs': {
            'total_need': 3990060,
            'income_replacement': 2793042,
            'debt_payoff': 859200,
            'education_funding': 200000,
            'funeral_expenses': 8000,
            'legacy_amount': 532008,
            'special_needs': 100000,
            'coverage_gap': 2990060,
            'recommended_coverage': 3990060,
            'duration_years': 25,
            'product_recommendation': 'JPM TermVest+ IUL Track',
            'rationale': 'At age 38.0 with $266,004 annual income and 2.0 dependents, you\'re an ideal candidate for the IUL Track. Start with term coverage and convert to permanent coverage as your financial situation allows, building cash value for retirement and legacy planning.'
        },
        'cash_value_projection': [
            {'year': 1, 'value': 11730}, {'year': 2, 'value': 24000}, {'year': 3, 'value': 36900},
            {'year': 4, 'value': 50400}, {'year': 5, 'value': 64500}, {'year': 10, 'value': 145000},
            {'year': 20, 'value': 400000}, {'year': 30, 'value': 900000}, {'year': 40, 'value': 2015500}
        ],
        'projection_parameters': {
            'illustrated_rate': 0.06, 'year1_allocation': 0.85, 'year2plus_allocation': 0.95,
            'duration_years': 40, 'monthly_contribution': 1150
        },
        'recommended_monthly_savings': 1150,
        'max_monthly_contribution': 2000
    }
    
    # Sample assessment data
    assessment_data = {
        'client_name': 'Test Client',
        'age': 38,
        'marital_status': 'married',
        'dependents': 2,
        'health_status': 'good',
        'tobacco_use': 'no',
        'monthly_income': 8000,
        'monthly_expenses': 5000,
        'mortgage_balance': 250000,
        'other_debts': 15000,
        'additional_obligations': 5000,
        'provide_education': True,
        'num_children': 2,
        'education_type': 'public_4_in',
        'education_cost_per_child': 23250 * 4,
        'funeral_expenses': 8000,
        'legacy_amount': 50000,
        'special_needs': 'Dependent care needs',
        'savings': 20000,
        'investments': 50000,
        'individual_life': 100000,
        'group_life': 50000,
        'other_assets': 10000,
        'advisor_notes': 'Client is looking for comprehensive coverage and cash value growth.',
        'recommended_coverage': 750000,
        'gap': 500000,
        'product_recommendation': 'JPM TermVest+ IUL Track',
        'duration_years': 20,
        'rationale': 'Based on your financial profile and goals, the IUL Track is recommended for its cash value growth and permanent coverage.',
        'needs_breakdown': {
            'living_expenses': 400000,
            'debts': 150000,
            'education': 100000,
            'funeral': 8000,
            'legacy': 50000,
            'other': 0
        },
        'cash_value_projection': [
            {'year': 1, 'value': 4000}, {'year': 2, 'value': 8200}, {'year': 3, 'value': 12600},
            {'year': 4, 'value': 17200}, {'year': 5, 'value': 22000}, {'year': 10, 'value': 50000},
            {'year': 20, 'value': 150000}
        ],
        'recommended_monthly_savings': 400,
        'max_monthly_contribution': 1000,
        'projection_parameters': {
            'illustrated_rate': 0.055, 'year1_allocation': 0.8, 'year2plus_allocation': 0.9,
            'duration_years': 20, 'monthly_contribution': 400
        }
    }
    
    try:
        # Initialize PDF generator
        pdf_generator = SimplePDFGenerator()
        
        print("📊 Generating Portfolio Analysis PDF...")
        portfolio_pdf_id = await pdf_generator.generate_portfolio_pdf(portfolio_data, "test_portfolio")
        print(f"✅ Portfolio PDF generated: {portfolio_pdf_id}")
        
        print("📋 Generating Client Assessment PDF...")
        assessment_pdf_id = await pdf_generator.generate_assessment_pdf(assessment_data, "test_assessment")
        print(f"✅ Assessment PDF generated: {assessment_pdf_id}")
        
        # Verify file existence and size
        portfolio_pdf_path = pdf_generator.get_pdf_path(portfolio_pdf_id)
        assessment_pdf_path = pdf_generator.get_pdf_path(assessment_pdf_id)
        
        print(f"📁 Portfolio PDF path: {portfolio_pdf_path}")
        print(f"📁 Assessment PDF path: {assessment_pdf_path}")
        
        if portfolio_pdf_path.exists() and assessment_pdf_path.exists():
            print(f"📊 Portfolio PDF size: {portfolio_pdf_path.stat().st_size} bytes")
            print(f"📊 Assessment PDF size: {assessment_pdf_path.stat().st_size} bytes")
            print("\n🎉 Screenshot-based PDF generation test completed successfully!")
            print("📄 Both PDFs should now contain:")
            print("   • Exact 1:1 visual copies of the frontend")
            print("   • All charts, graphs, and styling")
            print("   • Complete data visualization")
            print("   • Professional layout and formatting")
            return True
        else:
            print("❌ PDF files were not generated.")
            return False
            
    except Exception as e:
        print(f"❌ Error during PDF generation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_screenshot_pdf_generation())
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)

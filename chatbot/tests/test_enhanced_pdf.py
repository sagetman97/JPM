#!/usr/bin/env python3
"""
Test script for enhanced PDF generation with charts
"""

import asyncio
import sys
import os
sys.path.append('chatbot')

from chatbot.core.pdf_generator import PDFGenerator

async def test_enhanced_pdf_generation():
    """Test the enhanced PDF generation with sample data"""
    
    # Sample portfolio data matching the structure from terminal output
    sample_portfolio_data = {
        'client_name': 'Alex Rivera',
        'age': 38,
        'marital_status': 'Married',
        'dependents': 2,
        'health_status': 'Good',
        'tobacco_use': 'No',
        'total_assets': 2214840,
        'investable_portfolio': 491800,
        'total_net_worth': 1355640,
        'liquid_assets': 61800,
        'monthly_income': 22167,
        'monthly_expenses': 7000,
        'asset_allocation': {
            'equity': 1506091,
            'fixed_income': 398671,
            'real_estate': 1650000,
            'cash': 61800,
            'alternative_investments': 0
        },
        'retirement_accounts': 430000,
        'taxable_accounts': 129000,
        'education_accounts': 45000,
        'real_estate_value': 1650000,
        'liabilities_total': 859200,
        'portfolio_metrics': {
            'risk_level': 'moderate',
            'risk_score': 68,
            'portfolio_health_score': 68,
            'liquidity_ratio': 8.83,
            'diversification_score': 75
        },
        'life_insurance_needs': {
            'total_need': 3990060,
            'income_replacement': 2793042,
            'debt_payoff': 859200,
            'education_funding': 200000,
            'funeral_expenses': 8000,
            'legacy_amount': 532008,
            'coverage_gap': 2990060
        },
        'product_recommendation': 'JPM TermVest+ IUL Track',
        'duration_years': 20,
        'recommended_monthly_savings': 1150,
        'max_monthly_contribution': 2000,
        'cash_value_projection': [
            {'year': 5, 'value': 75000},
            {'year': 10, 'value': 180000},
            {'year': 20, 'value': 450000},
            {'year': 30, 'value': 1200000},
            {'year': 40, 'value': 2015500}
        ],
        'key_findings': [
            'Portfolio shows strong equity allocation at 68%',
            'Real estate represents 74.5% of total assets',
            'Liquidity ratio of 8.83 months is excellent',
            'Significant coverage gap of $2.99M identified'
        ],
        'risk_analysis': [
            'Moderate risk tolerance appropriate for age 38',
            'High real estate concentration may limit diversification',
            'Strong liquidity position provides financial flexibility',
            'Portfolio health score of 68/100 indicates room for improvement'
        ],
        'recommendations': [
            'Consider rebalancing to reduce real estate concentration',
            'Implement life insurance coverage to address $2.99M gap',
            'Maintain current liquidity levels for emergency preparedness',
            'Review asset allocation annually for optimal diversification'
        ],
        'rationale': 'Based on the comprehensive analysis, Alex Rivera shows a strong financial position with excellent liquidity and solid asset base. However, the high real estate concentration and significant life insurance coverage gap present key opportunities for optimization. The recommended JPM TermVest+ IUL Track provides both protection and cash value accumulation potential, addressing the coverage gap while building long-term wealth.'
    }
    
    # Sample assessment data
    sample_assessment_data = {
        'client_name': 'John Smith',
        'age': 35,
        'marital_status': 'Married',
        'dependents': 2,
        'health_status': 'Good',
        'tobacco_use': 'No',
        'monthly_income': 15000,
        'monthly_expenses': 8000,
        'mortgage_balance': 300000,
        'other_debts': 25000,
        'additional_obligations': 5000,
        'savings': 50000,
        'investments': 100000,
        'other_assets': 25000,
        'needs_breakdown': {
            'living_expenses': 960000,
            'debts': 330000,
            'education': 200000,
            'funeral': 15000,
            'legacy': 100000
        },
        'recommended_coverage': 1605000,
        'gap': 1605000,
        'product_recommendation': 'Term Life Insurance',
        'duration_years': 20,
        'recommended_monthly_savings': 200,
        'max_monthly_contribution': 500,
        'cash_value_projection': [
            {'year': 5, 'value': 15000},
            {'year': 10, 'value': 35000},
            {'year': 20, 'value': 85000}
        ],
        'rationale': 'Based on the comprehensive needs analysis, John Smith requires $1.605M in life insurance coverage to adequately protect his family. The recommended term life insurance provides maximum coverage at an affordable premium, ensuring his family\'s financial security during the critical child-rearing years.'
    }
    
    print("🧪 Testing Enhanced PDF Generation...")
    
    # Initialize PDF generator
    pdf_generator = PDFGenerator()
    
    try:
        # Test portfolio PDF generation
        print("📊 Generating Portfolio Analysis PDF...")
        portfolio_pdf_id = await pdf_generator.generate_portfolio_pdf(sample_portfolio_data, "test_portfolio")
        print(f"✅ Portfolio PDF generated: {portfolio_pdf_id}")
        
        # Test assessment PDF generation
        print("📋 Generating Client Assessment PDF...")
        assessment_pdf_id = await pdf_generator.generate_assessment_pdf(sample_assessment_data, "test_assessment")
        print(f"✅ Assessment PDF generated: {assessment_pdf_id}")
        
        # Check if files exist
        portfolio_path = pdf_generator.get_pdf_path(portfolio_pdf_id)
        assessment_path = pdf_generator.get_pdf_path(assessment_pdf_id)
        
        print(f"📁 Portfolio PDF path: {portfolio_path}")
        print(f"📁 Assessment PDF path: {assessment_path}")
        print(f"📊 Portfolio PDF size: {portfolio_path.stat().st_size} bytes")
        print(f"📊 Assessment PDF size: {assessment_path.stat().st_size} bytes")
        
        print("\n🎉 Enhanced PDF generation test completed successfully!")
        print("📄 Both PDFs should now contain:")
        print("   • Professional styling with colors")
        print("   • Interactive charts and graphs")
        print("   • Complete data visualization")
        print("   • Visual risk indicators")
        print("   • Comprehensive analysis sections")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during PDF generation: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_pdf_generation())
    sys.exit(0 if success else 1)

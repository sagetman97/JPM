#!/usr/bin/env python3
"""
Test script to verify the PDF generation flow works correctly
"""

import asyncio
import json
from chatbot.core.screenshot_pdf_generator import ScreenshotPDFGenerator

async def test_portfolio_pdf_generation():
    """Test portfolio PDF generation with the new flow"""
    
    # Sample portfolio data
    portfolio_data = {
        "client_name": "Test Client",
        "age": 35,
        "marital_status": "married",
        "dependents": 2,
        "health_status": "good",
        "tobacco_use": "no",
        "total_assets": 1000000,
        "investable_portfolio": 800000,
        "total_net_worth": 900000,
        "liquid_assets": 50000,
        "monthly_income": 10000,
        "monthly_expenses": 6000,
        "equity_allocation": 600000,
        "fixed_income_allocation": 200000,
        "real_estate_allocation": 150000,
        "cash_allocation": 50000,
        "alternative_allocation": 0,
        "retirement_accounts": 400000,
        "taxable_accounts": 200000,
        "education_accounts": 100000,
        "liabilities_total": 100000,
        "current_life_insurance": 500000,
        "individual_life": 500000,
        "group_life": 0,
        "funeral_expenses": 10000,
        "special_needs": "",
        "cash_value_importance": "yes",
        "permanent_coverage": "yes",
        "coverage_goals": ["income_replacement", "debt_payoff", "education"],
        "other_coverage_goal": ""
    }
    
    print("Testing portfolio PDF generation with new flow...")
    
    async with ScreenshotPDFGenerator() as pdf_generator:
        try:
            pdf_id = await pdf_generator.generate_portfolio_pdf(portfolio_data, "test_session_123")
            print(f"✅ Portfolio PDF generated successfully: {pdf_id}")
            return True
        except Exception as e:
            print(f"❌ Portfolio PDF generation failed: {e}")
            return False

async def test_assessment_pdf_generation():
    """Test assessment PDF generation with the new flow"""
    
    # Sample assessment data
    assessment_data = {
        "age": "35",
        "marital_status": "married",
        "dependents": "2",
        "health_status": "good",
        "tobacco_use": "no",
        "cash_value_importance": "yes",
        "permanent_coverage": "yes",
        "coverage_goals": ["income_replacement", "debt_payoff", "education"],
        "other_coverage_goal": "",
        "monthly_income": "10000",
        "monthly_expenses": "6000",
        "adjust_inflation": True,
        "mortgage_balance": "300000",
        "other_debts": "50000",
        "additional_obligations": "0",
        "provide_education": True,
        "num_children": "2",
        "education_type": "private",
        "education_cost_per_child": "100000",
        "funeral_expenses": "10000",
        "legacy_amount": "500000",
        "special_needs": "",
        "savings": "100000",
        "investments": "200000",
        "individual_life": "500000",
        "group_life": "100000",
        "other_assets": "50000",
        "advisor_notes": "Test assessment",
        "income_replacement_years": "10"
    }
    
    print("Testing assessment PDF generation with new flow...")
    
    async with ScreenshotPDFGenerator() as pdf_generator:
        try:
            pdf_id = await pdf_generator.generate_assessment_pdf(assessment_data, "test_session_456")
            print(f"✅ Assessment PDF generated successfully: {pdf_id}")
            return True
        except Exception as e:
            print(f"❌ Assessment PDF generation failed: {e}")
            return False

async def main():
    """Run all tests"""
    print("🧪 Testing PDF Generation Flow")
    print("=" * 50)
    
    # Test portfolio PDF generation
    portfolio_success = await test_portfolio_pdf_generation()
    
    print()
    
    # Test assessment PDF generation
    assessment_success = await test_assessment_pdf_generation()
    
    print()
    print("=" * 50)
    print("📊 Test Results:")
    print(f"Portfolio PDF Generation: {'✅ PASS' if portfolio_success else '❌ FAIL'}")
    print(f"Assessment PDF Generation: {'✅ PASS' if assessment_success else '❌ FAIL'}")
    
    if portfolio_success and assessment_success:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())

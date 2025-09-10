#!/usr/bin/env python3

import sys
import os
sys.path.append('/mnt/c/AIProjects/RoboAdvisor/chatbot')

from main import _generate_detailed_report_message

# Test data that matches what we're sending
test_data = {
    "formData": {
        "age": "38",
        "marital_status": "married", 
        "monthly_income": "22167",
        "individual_life": "1000000",
        "group_life": "0"
    },
    "result": {
        "analysis": {
            "life_insurance_needs": {
                "total_need": 3965058,
                "coverage_gap": 2965058,
                "product_recommendation": "JPM TermVest+ IUL Track",
                "duration_years": 25,
                "income_replacement": 2793042,
                "debt_payoff": 532008,
                "education_funding": 0,
                "funeral_expenses": 8000,
                "legacy_amount": 532008
            },
            "portfolio_metrics": {
                "risk_level": "moderate",
                "portfolio_health_score": 68,
                "risk_score": 55,
                "liquidity_ratio": 8.8
            },
            "key_findings": ["Strong portfolio foundation", "Significant insurance gap", "IUL integration opportunity"],
            "risk_analysis": ["Balanced risk profile with moderate exposure"],
            "opportunities": ["IUL integration", "Tax efficiency optimization", "Portfolio diversification"],
            "recommendations": ["Address insurance gap", "Implement IUL strategy", "Quarterly rebalancing"],
            "tax_efficiency": ["Significant tax optimization opportunities through IUL"],
            "rebalancing_needs": ["Increase liquidity", "Optimize asset allocation"],
            "cash_value_projection": [
                {"year": 1, "value": 0},
                {"year": 5, "value": 95038.99},
                {"year": 10, "value": 224700.31},
                {"year": 20, "value": 636481.79},
                {"year": 30, "value": 1387952.37},
                {"year": 40, "value": 2759330.29}
            ],
            "total_assets": 2214840,
            "total_net_worth": 1355640,
            "investable_portfolio": 491800,
            "asset_allocation_dollars": {
                "equity": 1506091,
                "fixed_income": 398671,
                "real_estate": 1650000,
                "cash": 61800
            },
            "asset_allocation_percentages": {
                "equity": 68.0,
                "fixed_income": 18.0,
                "real_estate": 74.5,
                "cash": 2.8
            },
            "account_distribution": {
                "retirement_accounts": 430000,
                "taxable_accounts": 129000,
                "education_accounts": 45000
            },
            "recommended_monthly_savings": 1150,
            "max_monthly_contribution": 5000,
            "projection_parameters": {
                "illustrated_rate": 0.06,
                "year1_allocation": 0.85,
                "year2plus_allocation": 0.95
            }
        },
        "current_coverage": 1000000,
        "individual_life": 1000000,
        "group_life": 0
    }
}

print("Testing detailed report generation...")
print("=" * 50)

try:
    result = _generate_detailed_report_message("portfolio", test_data)
    print("SUCCESS: Function executed without error")
    print("=" * 50)
    print("DETAILED REPORT PREVIEW (first 2000 characters):")
    print(result[:2000])
    print("=" * 50)
    print("CHECKING FOR KEY INDICATORS:")
    print(f"Contains 'Total Assets:': {'Total Assets:' in result}")
    print(f"Contains 'Asset Allocation:': {'Asset Allocation:' in result}")
    print(f"Contains 'Portfolio Health Score:': {'Portfolio Health Score:' in result}")
    print(f"Contains 'portfolio analysis completed': {'portfolio analysis completed' in result.lower()}")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

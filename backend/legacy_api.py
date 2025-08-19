"""
Legacy CSV parsing functions for backward compatibility.
These functions maintain the existing parsing logic while the new system is being implemented.
"""

import csv
import io
from typing import Dict, List, Any, Optional

def parse_csv_structure(file_bytes: bytes, file_name: str) -> Optional[Dict[str, Any]]:
    """
    STAGE 1: Parse CSV and extract basic structure without LLM calls.
    This gives us a foundation to work with.
    """
    try:
        csv_text = file_bytes.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(csv_text))
        rows = list(csv_reader)
        
        if not rows or len(rows) < 2:
            return None
        
        headers = rows[0]
        data_rows = rows[1:]
        
        # Analyze record types from column 55 (where "Position", "Account", etc. are stored)
        record_types = set()
        for row in data_rows:
            if len(row) > 55 and row[55]:  # Column 55 contains record types
                record_types.add(row[55])
        
        return {
            "headers": headers,
            "rows": data_rows,
            "record_types": list(record_types),
            "file_name": file_name
        }
        
    except Exception as e:
        print(f"CSV parsing failed: {e}")
        return None

def create_default_household_profile() -> Dict[str, Any]:
    """Create default household profile data"""
    return {
        "client_age": 35,
        "marital_status": "Unknown",
        "dependents_count": 0,
        "dependents_ages": "",
        "risk_tolerance": "Unknown",
        "time_horizon_years": 20,
        "income_w2_annual": 0,
        "income_1099_annual": 0,
        "spouse_income_annual": 0,
        "other_income_annual": 0,
        "monthly_expenses_fixed": 0,
        "monthly_expenses_variable": 0,
        "savings_rate_pct": 0,
        "emergency_fund_target_months": 6
    }

def create_default_financial_summary() -> Dict[str, Any]:
    """Create default financial summary data"""
    return {
        "total_portfolio_value": 0,
        "total_net_worth": 0,
        "liquid_assets": 0,
        "total_liabilities": 0,
        "monthly_income_total": 0,
        "monthly_expenses_total": 0
    }

def create_default_asset_allocation() -> Dict[str, Any]:
    """Create default asset allocation data"""
    return {
        "equity": 0,
        "fixed_income": 0,
        "real_estate": 0,
        "cash": 0,
        "alternative_investments": 0
    }

def create_default_account_breakdown() -> Dict[str, Any]:
    """Create default account breakdown data"""
    return {
        "retirement_accounts": 0,
        "taxable_accounts": 0,
        "education_accounts": 0,
        "real_estate_value": 0,
        "insurance_cash_value": 0
    }

def create_default_insurance_data() -> Dict[str, Any]:
    """Create default insurance data"""
    return {
        "individual_life": 0,
        "group_life": 0,
        "total_life_coverage": 0
    }

def create_default_liability_data() -> Dict[str, Any]:
    """Create default liability data"""
    return {
        "mortgage_balance": 0,
        "student_loans": 0,
        "credit_cards": 0,
        "other_debts": 0
    }

def create_default_financial_goals() -> Dict[str, Any]:
    """Create default financial goals data"""
    return {
        "retirement_target": 0,
        "education_funding_needs": 0,
        "legacy_goals": 0
    }

def create_default_additional_fields() -> Dict[str, Any]:
    """Create default additional fields data"""
    return {
        "health_status": "Good",
        "tobacco_use": "No",
        "client_name": "Client Name",
        "funeral_expenses": 8000,
        "special_needs": ""
    } 
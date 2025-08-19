"""
Simple financial data models for Phase 1 CSV parsing.
Focused on reliable data extraction without complex analysis.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class AssetClass(str, Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    ALTERNATIVE = "alternative_investments"

class AccountType(str, Enum):
    RETIREMENT = "retirement"
    TAXABLE = "taxable"
    EDUCATION = "education"
    INSURANCE = "insurance"
    REAL_ESTATE = "real_estate"

class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"

class MaritalStatus(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"

class FormData(BaseModel):
    """Simple form data structure for Phase 1 - just what we need to populate the form"""
    
    # Household Profile
    client_age: int = 35
    marital_status: str = "Unknown"
    dependents_count: int = 0
    dependents_ages: str = ""
    risk_tolerance: str = "Unknown"
    time_horizon_years: int = 20
    income_w2_annual: float = 0.0
    income_1099_annual: float = 0.0
    spouse_income_annual: float = 0.0
    other_income_annual: float = 0.0
    monthly_expenses_fixed: float = 0.0
    monthly_expenses_variable: float = 0.0
    savings_rate_pct: float = 0.0
    emergency_fund_target_months: int = 6
    
    # Financial Summary
    total_assets: float = 0.0  # Total assets including real estate
    investable_portfolio: float = 0.0   # Investable assets excluding real estate
    total_portfolio_value: float = 0.0  # Alias for investable_portfolio for compatibility
    total_net_worth: float = 0.0
    liquid_assets: float = 0.0
    total_liabilities: float = 0.0
    monthly_income_total: float = 0.0
    monthly_expenses_total: float = 0.0
    
    # Asset Allocation (for frontend display)
    equity_allocation: float = 0.0
    fixed_income_allocation: float = 0.0
    real_estate_allocation: float = 0.0
    cash_allocation: float = 0.0
    alternative_allocation: float = 0.0
    
    # Asset Allocation (for backend calculations - legacy compatibility)
    equity: float = 0.0
    fixed_income: float = 0.0
    real_estate: float = 0.0
    cash: float = 0.0
    alternative_investments: float = 0.0
    
    # Account Breakdown
    retirement_accounts: float = 0.0
    taxable_accounts: float = 0.0
    education_accounts: float = 0.0
    real_estate_value: float = 0.0
    insurance_cash_value: float = 0.0
    
    # Current Insurance (for frontend display)
    current_life_insurance: float = 0.0
    
    # Current Insurance (for backend calculations - legacy compatibility)
    individual_life: float = 0.0
    group_life: float = 0.0
    total_life_coverage: float = 0.0
    
    # Liabilities Detail (for frontend display)
    liabilities_total: float = 0.0
    
    # Liabilities Detail (for backend calculations - legacy compatibility)
    mortgage_balance: float = 0.0
    student_loans: float = 0.0
    credit_cards: float = 0.0
    other_debts: float = 0.0
    
    # Financial Goals
    retirement_target: float = 0.0
    education_funding_needs: float = 0.0
    legacy_goals: float = 0.0
    
    # Additional Fields
    health_status: str = "Good"
    tobacco_use: str = "No"
    client_name: str = "Client Name"
    funeral_expenses: float = 8000.0
    special_needs: str = ""
    
    # Additional fields for form compatibility
    investment_horizon: int = 20
    retirement_target: float = 0.0
    legacy_goals: float = 0.0
    cash_value_importance: str = "yes"
    permanent_coverage: str = "yes"
    coverage_goals: List[str] = ["income_replacement", "debt_payoff", "education", "funeral", "legacy"]
    other_coverage_goal: str = "Not provided"
    income_replacement_years: int = 10
    
    class Config:
        extra = "allow"  # Allow extra fields for flexibility

def create_default_form_data() -> FormData:
    """Create default form data with all fields set to safe defaults"""
    return FormData()

def convert_to_legacy_format(form_data: FormData) -> Dict[str, Any]:
    """Convert FormData to the legacy format expected by the frontend"""
    return {
        "household_profile": {
            "client_age": form_data.client_age,
            "marital_status": form_data.marital_status,
            "dependents_count": form_data.dependents_count,
            "dependents_ages": form_data.dependents_ages,
            "risk_tolerance": form_data.risk_tolerance,
            "time_horizon_years": form_data.time_horizon_years,
            "income_w2_annual": form_data.income_w2_annual,
            "income_1099_annual": form_data.income_1099_annual,
            "spouse_income_annual": form_data.spouse_income_annual,
            "other_income_annual": form_data.other_income_annual,
            "monthly_expenses_fixed": form_data.monthly_expenses_fixed,
            "monthly_expenses_variable": form_data.monthly_expenses_variable,
            "savings_rate_pct": form_data.savings_rate_pct,
            "emergency_fund_target_months": form_data.emergency_fund_target_months
        },
        "financial_summary": {
            "total_assets": form_data.total_assets,
            "total_portfolio_value": form_data.total_portfolio_value,  # Add missing field
            "investable_portfolio": form_data.investable_portfolio,  # Add investable portfolio field
            "total_net_worth": form_data.total_net_worth,
            "liquid_assets": form_data.liquid_assets,
            "total_liabilities": form_data.total_liabilities,
            "monthly_income_total": form_data.monthly_income_total,
            "monthly_expenses_total": form_data.monthly_expenses_total
        },
        "portfolio_overview": {
            "total_assets": form_data.total_assets,
            "investable_portfolio": form_data.investable_portfolio,
            "total_net_worth": form_data.total_net_worth,
            "liquid_assets": form_data.liquid_assets
        },
        "asset_allocation": {
            "equity": form_data.equity,
            "fixed_income": form_data.fixed_income,
            "real_estate": form_data.real_estate,
            "cash": form_data.cash,
            "alternative_investments": form_data.alternative_investments
        },
        "account_breakdown": {
            "retirement_accounts": form_data.retirement_accounts,
            "taxable_accounts": form_data.taxable_accounts,
            "education_accounts": form_data.education_accounts,
            "real_estate_value": form_data.real_estate_value,
            "insurance_cash_value": form_data.insurance_cash_value
        },
        "current_insurance": {
            "individual_life": form_data.individual_life,
            "group_life": form_data.group_life,
            "total_life_coverage": form_data.total_life_coverage
        },
        "liabilities_detail": {
            "mortgage_balance": form_data.mortgage_balance,
            "student_loans": form_data.student_loans,
            "credit_cards": form_data.credit_cards,
            "other_debts": form_data.other_debts
        },
        "financial_goals": {
            "retirement_target": form_data.retirement_target,
            "education_funding_needs": form_data.education_funding_needs,
            "legacy_goals": form_data.legacy_goals
        },
        "additional_fields": {
            "health_status": form_data.health_status,
            "tobacco_use": form_data.tobacco_use,
            "client_name": form_data.client_name,
            "funeral_expenses": form_data.funeral_expenses,
            "special_needs": form_data.special_needs,
            "investment_horizon": form_data.investment_horizon,
            "cash_value_importance": form_data.cash_value_importance,
            "permanent_coverage": form_data.permanent_coverage,
            "coverage_goals": form_data.coverage_goals,
            "other_coverage_goal": form_data.other_coverage_goal,
            "income_replacement_years": form_data.income_replacement_years
        }
    } 
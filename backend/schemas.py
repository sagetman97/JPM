from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class NeedsAssessmentInput(BaseModel):
    # Step 1: Coverage Goals (multi-select)
    coverage_goals: Optional[List[str]] = []
    other_coverage_goal: Optional[str] = None
    # Demographics
    age: Optional[int] = None
    marital_status: Optional[str] = None
    dependents: Optional[int] = None
    health_status: Optional[str] = None
    tobacco_use: Optional[str] = None
    # Preferences
    cash_value_importance: Optional[str] = None  # 'yes', 'no', 'unsure'
    permanent_coverage: Optional[str] = None
    income_replacement_years: Optional[int] = 10
    premium_budget: Optional[float] = None
    product_preference: Optional[str] = None  # 'term', 'iul', 'unsure'
    years_of_coverage: Optional[int] = None
    # Step 2: Income & Expenses
    monthly_income: Optional[float] = None
    support_years: Optional[int] = None
    adjust_inflation: Optional[bool] = False
    # Step 3: Debt & Obligations
    mortgage_balance: Optional[float] = None
    other_debts: Optional[float] = None
    additional_obligations: Optional[float] = None
    # Step 4: Education Needs
    provide_education: Optional[bool] = None
    num_children: Optional[int] = None
    education_type: Optional[str] = None
    education_cost_per_child: Optional[float] = None
    # Step 5: Final Expenses & Legacy
    funeral_expenses: Optional[float] = None
    legacy_amount: Optional[float] = None
    special_needs: Optional[str] = None
    # Step 6: Existing Assets & Coverage
    savings: Optional[float] = None
    investments: Optional[float] = None
    individual_life: Optional[float] = None
    group_life: Optional[float] = None
    other_assets: Optional[float] = None
    # Step 7: Advisor Notes
    advisor_notes: Optional[str] = None

class NeedsBreakdown(BaseModel):
    living_expenses: float = 0
    debts: float = 0
    education: float = 0
    funeral: float = 0
    legacy: float = 0
    other: float = 0

class CashValueProjectionPoint(BaseModel):
    year: int
    value: float

class NeedsAssessmentResult(BaseModel):
    needs_breakdown: NeedsBreakdown
    recommended_coverage: float
    gap: float
    suggested_policy_type: Optional[str] = None
    duration_years: Optional[int] = None
    advisor_notes: Optional[str] = None
    product_recommendation: Optional[str] = None
    rationale: Optional[str] = None
    cash_value_projection: Optional[List[CashValueProjectionPoint]] = None
    recommended_monthly_savings: Optional[float] = None
    max_monthly_contribution: Optional[float] = None
    projection_parameters: Optional[Dict[str, float]] = None
    conversion_timeline: Optional[List[Dict[str, Any]]] = None

class FAQRequest(BaseModel):
    question: str

class FAQResponse(BaseModel):
    answer: str
    related: List[str]

class ScenarioRequest(BaseModel):
    base: NeedsAssessmentInput
    scenarios: List[Dict[str, Any]]

class ScenarioResult(BaseModel):
    scenario: dict
    result: NeedsAssessmentResult

# New Portfolio Analysis Models
class PortfolioAnalysisInput(BaseModel):
    # Client Demographics
    client_name: Optional[str] = None
    age: Optional[int] = None
    marital_status: Optional[str] = None
    dependents: Optional[int] = None
    health_status: Optional[str] = None
    tobacco_use: Optional[str] = None
    
    # Portfolio Overview
    total_portfolio_value: Optional[float] = None
    total_net_worth: Optional[float] = None
    liquid_assets: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    
    # Asset Allocation
    equity_allocation: Optional[float] = None
    fixed_income_allocation: Optional[float] = None
    real_estate_allocation: Optional[float] = None
    cash_allocation: Optional[float] = None
    alternative_allocation: Optional[float] = None
    
    # Account Details
    retirement_accounts: Optional[float] = None
    taxable_accounts: Optional[float] = None
    education_accounts: Optional[float] = None
    real_estate_value: Optional[float] = None
    liabilities_total: Optional[float] = None
    
    # Risk Profile & Goals
    risk_tolerance: Optional[str] = None
    investment_horizon: Optional[int] = None
    retirement_target: Optional[float] = None
    legacy_goals: Optional[float] = None
    
    # Insurance & Protection
    current_life_insurance: Optional[float] = None
    individual_life: Optional[float] = None
    group_life: Optional[float] = None
    income_replacement_years: Optional[int] = 10
    funeral_expenses: Optional[float] = None
    special_needs: Optional[str] = None
    
    # Financial Goals
    cash_value_importance: Optional[str] = None
    permanent_coverage: Optional[str] = None
    coverage_goals: Optional[List[str]] = []
    other_coverage_goal: Optional[str] = None

class PortfolioAnalysis(BaseModel):
    asset_allocation: Dict[str, float]
    risk_score: float
    risk_level: str
    concentration_risks: List[str]
    diversification_opportunities: List[str]

class IULAnalysis(BaseModel):
    optimal_allocation: Dict[str, float]
    projection: List[Dict[str, Any]]
    fixed_income_comparison: Dict[str, Any]
    portfolio_impact: Dict[str, Any]

class PortfolioAnalysisResult(BaseModel):
    needs_breakdown: NeedsBreakdown
    recommended_coverage: float
    gap: float
    duration_years: Optional[int] = None
    product_recommendation: Optional[str] = None
    rationale: Optional[str] = None
    cash_value_projection: Optional[List[CashValueProjectionPoint]] = None
    recommended_monthly_savings: Optional[float] = None
    max_monthly_contribution: Optional[float] = None
    projection_parameters: Optional[Dict[str, float]] = None
    portfolio_analysis: Optional[PortfolioAnalysis] = None
    iul_analysis: Optional[IULAnalysis] = None 
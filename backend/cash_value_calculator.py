from typing import Dict, Any, List
from dataclasses import dataclass
import math

@dataclass
class CashValueProjectionPoint:
    year: int
    value: float
    death_benefit: float
    net_cost: float

@dataclass
class CashValueProjection:
    projection: List[CashValueProjectionPoint]
    projection_parameters: Dict[str, float]
    recommended_monthly_savings: float
    max_monthly_contribution: float
    total_contributions: float
    projected_cash_value_30yr: float
    projected_death_benefit_30yr: float

class CashValueCalculator:
    """Calculate IUL cash value projections and recommendations"""
    
    def __init__(self):
        # IUL allocation parameters (based on age and risk tolerance)
        self.age_allocation_rules = {
            (18, 30): {"year1": 0.85, "year2plus": 0.90, "illustrated_rate": 0.065},
            (31, 40): {"year1": 0.80, "year2plus": 0.85, "illustrated_rate": 0.062},
            (41, 50): {"year1": 0.75, "year2plus": 0.80, "illustrated_rate": 0.060},
            (51, 60): {"year1": 0.70, "year2plus": 0.75, "illustrated_rate": 0.058},
            (61, 70): {"year1": 0.65, "year2plus": 0.70, "illustrated_rate": 0.055}
        }
        
        # Risk tolerance adjustments
        self.risk_adjustments = {
            "conservative": {"multiplier": 0.9, "rate_reduction": 0.005},
            "moderate": {"multiplier": 1.0, "rate_reduction": 0.0},
            "aggressive": {"multiplier": 1.1, "rate_reduction": 0.003}
        }
    
    def calculate_cash_value_projection(self, form_data: Dict[str, Any]) -> CashValueProjection:
        """Calculate comprehensive cash value projection"""
        try:
            # Extract key data
            age = self._parse_number(form_data.get("age", 0))
            risk_tolerance = form_data.get("risk_tolerance", "moderate")
            monthly_income = self._parse_number(form_data.get("monthly_income", 0))
            monthly_expenses = self._parse_number(form_data.get("monthly_expenses", 0))
            dependents = self._parse_number(form_data.get("dependents", 0))
            current_coverage = self._parse_number(form_data.get("total_life_coverage", 0))
            
            # Calculate recommended monthly savings
            recommended_savings = self._calculate_recommended_savings(
                monthly_income, monthly_expenses, dependents, current_coverage
            )
            
            # Get allocation parameters based on age
            allocation_params = self._get_allocation_parameters(age, risk_tolerance)
            
            # Generate projection
            projection = self._generate_projection(
                recommended_savings, allocation_params, age
            )
            
            # Calculate projection parameters
            projection_params = {
                "year1_allocation": allocation_params["year1"],
                "year2plus_allocation": allocation_params["year2plus"],
                "illustrated_rate": allocation_params["illustrated_rate"],
                "risk_adjustment": self.risk_adjustments[risk_tolerance]["multiplier"]
            }
            
            # Calculate totals
            total_contributions = recommended_savings * 12 * 30  # 30 years
            projected_cash_value_30yr = projection[-1].value if projection else 0
            projected_death_benefit_30yr = projection[-1].death_benefit if projection else 0
            
            return CashValueProjection(
                projection=projection,
                projection_parameters=projection_params,
                recommended_monthly_savings=recommended_savings,
                max_monthly_contribution=min(recommended_savings * 1.5, 2500),  # Cap at MEC limit
                total_contributions=total_contributions,
                projected_cash_value_30yr=projected_cash_value_30yr,
                projected_death_benefit_30yr=projected_death_benefit_30yr
            )
            
        except Exception as e:
            print(f"Cash value calculation failed: {e}")
            # Return default projection
            return self._get_default_projection()
    
    def _calculate_recommended_savings(self, monthly_income: float, monthly_expenses: float, 
                                     dependents: int, current_coverage: float) -> float:
        """Calculate realistic monthly savings for IUL"""
        if monthly_income <= 0:
            return 500  # Default minimum
        
        # Calculate disposable income
        disposable_income = monthly_income - monthly_expenses
        
        # Base savings rate (8-12% of disposable income is more realistic)
        base_savings_rate = 0.10  # Conservative base rate
        
        # Adjust for dependents (more dependents = higher savings need)
        dependent_multiplier = 1 + (dependents * 0.05)  # Reduced multiplier
        
        # Adjust for existing coverage (less coverage = higher savings need)
        coverage_factor = max(0.7, 1 - (current_coverage / (monthly_income * 12 * 10)))
        
        # Calculate recommended savings
        recommended = disposable_income * base_savings_rate * dependent_multiplier * coverage_factor
        
        # Apply MEC limit considerations (Modified Endowment Contract)
        # MEC limit is typically $2,000-$3,000 per month for most policies
        mec_limit = 2500  # Conservative MEC limit
        
        # Ensure reasonable bounds based on industry best practices
        min_savings = 250  # Minimum viable amount
        max_savings = min(disposable_income * 0.20, mec_limit)  # Cap at 20% of disposable income or MEC limit
        
        # Additional constraint: should not exceed 15% of monthly income
        max_income_based = monthly_income * 0.15
        
        final_recommendation = max(min_savings, min(recommended, max_savings, max_income_based))
        
        return round(final_recommendation, 2)
    
    def _get_allocation_parameters(self, age: int, risk_tolerance: str) -> Dict[str, float]:
        """Get IUL allocation parameters based on age and risk tolerance"""
        # Find age bracket
        for (min_age, max_age), params in self.age_allocation_rules.items():
            if min_age <= age <= max_age:
                base_params = params.copy()
                
                # Apply risk tolerance adjustments
                risk_adj = self.risk_adjustments.get(risk_tolerance, {"multiplier": 1.0, "rate_reduction": 0.0})
                
                return {
                    "year1": base_params["year1"] * risk_adj["multiplier"],
                    "year2plus": base_params["year2plus"] * risk_adj["multiplier"],
                    "illustrated_rate": base_params["illustrated_rate"] - risk_adj["rate_reduction"]
                }
        
        # Default for age > 70
        return {"year1": 0.60, "year2plus": 0.65, "illustrated_rate": 0.052}
    
    def _generate_projection(self, monthly_savings: float, allocation_params: Dict[str, float], 
                           age: int) -> List[CashValueProjectionPoint]:
        """Generate 30-year cash value projection with proper compound growth"""
        projection = []
        cash_value = 0
        death_benefit = 100000  # Base death benefit
        
        for year in range(1, 31):
            # Calculate cash value growth with proper compound interest
            if year == 1:
                # First year: premium allocation applies
                premium_contribution = monthly_savings * 12 * allocation_params["year1"]
                cash_value += premium_contribution
            else:
                # Subsequent years: compound growth + premium allocation
                # Apply illustrated rate to existing cash value
                cash_value = cash_value * (1 + allocation_params["illustrated_rate"])
                # Add new premium contribution
                premium_contribution = monthly_savings * 12 * allocation_params["year2plus"]
                cash_value += premium_contribution
            
            # Calculate death benefit (increases with cash value, minimum $100K)
            death_benefit = max(100000, cash_value * 2.5)
            
            # Calculate net cost (premiums paid minus cash value)
            total_premiums = monthly_savings * 12 * year
            net_cost = total_premiums - cash_value
            
            projection.append(CashValueProjectionPoint(
                year=year,
                value=round(cash_value, 2),
                death_benefit=round(death_benefit, 2),
                net_cost=round(net_cost, 2)
            ))
        
        return projection
    
    def _get_default_projection(self) -> CashValueProjection:
        """Return default projection if calculation fails"""
        default_projection = [
            CashValueProjectionPoint(year=i, value=i*1000, death_benefit=100000, net_cost=i*500)
            for i in range(1, 31)
        ]
        
        return CashValueProjection(
            projection=default_projection,
            projection_parameters={"year1": 0.80, "year2plus": 0.85, "illustrated_rate": 0.060},
            recommended_monthly_savings=500,
            max_monthly_contribution=1000,
            total_contributions=180000,
            projected_cash_value_30yr=30000,
            projected_death_benefit_30yr=100000
        )
    
    def _parse_number(self, value: Any) -> float:
        """Parse numeric value from various formats"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').replace('%', '')
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0 
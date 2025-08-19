"""
Life Insurance Needs Calculator
Implements industry-standard calculations for determining life insurance coverage needs.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class LifeInsuranceNeeds:
    """Life insurance needs calculation result"""
    total_need: float
    income_replacement: float
    debt_payoff: float
    education_funding: float
    funeral_expenses: float
    legacy_amount: float
    special_needs: float
    coverage_gap: float
    recommended_coverage: float
    duration_years: int
    product_recommendation: str
    rationale: str

class LifeInsuranceCalculator:
    """Calculate life insurance needs using industry-standard methods"""
    
    def __init__(self):
        # Industry standard multipliers and assumptions
        self.income_multiplier = 10  # 10x annual income for income replacement
        self.max_need_multiplier = 15  # Maximum realistic need (15x annual income)
        self.education_cost_per_child = 23250  # Realistic yearly college cost
        self.funeral_cost = 8000  # Average funeral expenses
        self.emergency_fund_months = 6  # Emergency fund coverage
    
    def calculate_needs(self, portfolio_data: Dict[str, Any]) -> LifeInsuranceNeeds:
        """Calculate comprehensive life insurance needs"""
        try:
            # Debug logging
            print(f"DEBUG: Life insurance calculator received portfolio_data: {portfolio_data}")
            
            # Extract key data
            age = self._parse_number(portfolio_data.get("age", 35))
            monthly_income = self._parse_number(portfolio_data.get("monthly_income", 0))
            monthly_expenses = self._parse_number(portfolio_data.get("monthly_expenses", 0))
            dependents = self._parse_number(portfolio_data.get("dependents", 0))
            current_coverage = self._parse_number(portfolio_data.get("current_life_insurance", 0))
            individual_life = self._parse_number(portfolio_data.get("individual_life", 0))
            group_life = self._parse_number(portfolio_data.get("group_life", 0))
            
            # Debug logging for extracted values
            print(f"DEBUG: Extracted values - age: {age}, monthly_income: {monthly_income}, monthly_expenses: {monthly_expenses}, dependents: {dependents}")
            print(f"DEBUG: Extracted values - current_coverage: {current_coverage}, individual_life: {individual_life}, group_life: {group_life}")
            
            # Validate input data
            if age < 18 or age > 85:
                print(f"Warning: Age {age} is outside reasonable range (18-85)")
                age = max(18, min(85, age))
            
            if monthly_income < 0:
                print(f"Warning: Monthly income is negative: {monthly_income}")
                monthly_income = 0
            
            if monthly_expenses < 0:
                print(f"Warning: Monthly expenses is negative: {monthly_expenses}")
                monthly_expenses = 0
            
            if dependents < 0:
                print(f"Warning: Dependents count is negative: {dependents}")
                dependents = 0
            
            if dependents > 10:
                print(f"Warning: Dependents count {dependents} seems unrealistic")
                dependents = min(dependents, 10)
            
            if current_coverage < 0:
                print(f"Warning: Current coverage is negative: {current_coverage}")
                current_coverage = 0
            
            if individual_life < 0:
                print(f"Warning: Individual life is negative: {individual_life}")
                individual_life = 0
            
            if group_life < 0:
                print(f"Warning: Group life is negative: {group_life}")
                group_life = 0
            
            # Calculate annual income
            annual_income = monthly_income * 12
            print(f"DEBUG: Calculated annual_income: ${annual_income:,.2f}")
            
            # Calculate needs components with realistic caps
            income_replacement = self._calculate_income_replacement(annual_income, age)
            debt_payoff = self._parse_number(portfolio_data.get("total_liabilities", 0))
            education_funding = self._calculate_education_funding(dependents, age)
            funeral_expenses = self._parse_number(portfolio_data.get("funeral_expenses", 0)) or self.funeral_cost
            legacy_amount = self._calculate_legacy_amount(annual_income, age)
            special_needs = self._calculate_special_needs(portfolio_data.get("special_needs", ""))
            
            # Debug logging for calculated needs
            print(f"DEBUG: Calculated needs - income_replacement: ${income_replacement:,.2f}, debt_payoff: ${debt_payoff:,.2f}")
            print(f"DEBUG: Calculated needs - education_funding: ${education_funding:,.2f}, funeral_expenses: ${funeral_expenses:,.2f}")
            print(f"DEBUG: Calculated needs - legacy_amount: ${legacy_amount:,.2f}, special_needs: ${special_needs:,.2f}")
            
            # Apply realistic caps to individual components
            max_realistic_need = annual_income * self.max_need_multiplier
            
            # Cap income replacement at 12x annual income
            income_replacement = min(income_replacement, annual_income * 12)
            
            # Cap debt payoff at 2x annual income
            debt_payoff = min(debt_payoff, annual_income * 2)
            
            # Cap legacy amount at 3x annual income
            legacy_amount = min(legacy_amount, annual_income * 3)
            
            # Calculate total need
            total_need = income_replacement + debt_payoff + education_funding + funeral_expenses + legacy_amount + special_needs
            
            # Final cap on total need
            total_need = min(total_need, max_realistic_need)
            
            # Calculate coverage gap
            total_current_coverage = current_coverage + individual_life + group_life
            coverage_gap = max(0, total_need - total_current_coverage)
            
            # Determine product recommendation
            product_recommendation = self._determine_product_recommendation(age, annual_income, dependents, total_need)
            
            # Determine duration
            duration_years = self._determine_duration(age, annual_income, dependents)
            
            # Generate rationale
            rationale = self._generate_rationale(age, annual_income, dependents, total_need, product_recommendation)
            
            return LifeInsuranceNeeds(
                total_need=round(total_need),
                income_replacement=round(income_replacement),
                debt_payoff=round(debt_payoff),
                education_funding=round(education_funding),
                funeral_expenses=round(funeral_expenses),
                legacy_amount=round(legacy_amount),
                special_needs=round(special_needs),
                coverage_gap=round(coverage_gap),
                recommended_coverage=round(total_need),
                duration_years=duration_years,
                product_recommendation=product_recommendation,
                rationale=rationale
            )
            
        except Exception as e:
            print(f"Life insurance needs calculation failed: {e}")
            return self._get_default_needs()
    
    def _parse_number(self, value: Any) -> float:
        """Parse various number formats to float"""
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace("$", "").replace(",", "").replace(" ", "")
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0
    
    def _calculate_income_replacement(self, annual_income: float, age: int) -> float:
        """Calculate income replacement needs"""
        if annual_income <= 0:
            return 0
        
        # Base income replacement (10x annual income)
        base_replacement = annual_income * self.income_multiplier
        
        # Adjust for age (longer coverage needed for younger clients)
        if age < 30:
            age_multiplier = 1.1  # 10% more coverage for very young
        elif age < 40:
            age_multiplier = 1.05  # 5% more coverage for young
        elif age < 50:
            age_multiplier = 1.0  # Standard coverage
        elif age < 60:
            age_multiplier = 0.95  # 5% less coverage for older clients
        else:
            age_multiplier = 0.9  # 10% less coverage for older clients
        
        # Apply realistic cap (12x annual income maximum)
        calculated_replacement = base_replacement * age_multiplier
        return min(calculated_replacement, annual_income * 12)
    
    def _calculate_debt_payoff(self, liabilities_total: float, liquid_assets: float) -> float:
        """Calculate debt payoff needs"""
        if liabilities_total <= 0:
            return 0
        
        # If liquid assets can cover debts, no additional coverage needed
        if liquid_assets >= liabilities_total:
            return 0
        
        # Return the gap between debts and liquid assets
        return max(0, liabilities_total - liquid_assets)
    
    def _calculate_education_funding(self, dependents: int, age: int) -> float:
        """Calculate education funding needs"""
        if dependents <= 0:
            return 0
        
        # Estimate years until college (assuming children are young)
        # For a 38-year-old client, children are likely 6-15 years old
        # Use more realistic assumptions based on typical family planning
        if age < 30:
            years_to_college = 18  # Children very young
        elif age < 35:
            years_to_college = 15  # Children likely 3-12 years old
        elif age < 40:
            years_to_college = 12  # Children likely 6-15 years old
        elif age < 45:
            years_to_college = 8   # Children likely 10-18 years old
        elif age < 50:
            years_to_college = 5   # Children likely 13-20 years old
        else:
            years_to_college = 2   # Children likely 16+ years old
        
        # Calculate total education cost using realistic college costs
        # Use $23,250/year from quick calculator (public 4-year in-state)
        yearly_cost_per_child = self.education_cost_per_child
        total_education_cost = dependents * yearly_cost_per_child * 4  # 4 years of college
        
        # Adjust for inflation (assume 3% annual inflation)
        inflation_factor = (1.03) ** years_to_college
        inflated_cost = total_education_cost * inflation_factor
        
        # Cap at realistic maximum (4x annual income per dependent)
        max_education_per_dependent = 100000  # Realistic cap
        capped_cost = min(inflated_cost, dependents * max_education_per_dependent)
        
        # Round to nearest thousand for realistic planning
        return round(capped_cost / 1000) * 1000
    
    def _calculate_legacy_amount(self, annual_income: float, age: int) -> float:
        """Calculate legacy/inheritance amount"""
        if annual_income <= 0:
            return 0
        
        # Legacy amount is typically 2-3x annual income
        if age < 40:
            legacy_multiplier = 2.0  # Younger clients, more conservative
        elif age < 50:
            legacy_multiplier = 2.5  # Prime earning years
        elif age < 60:
            legacy_multiplier = 2.0  # Approaching retirement
        else:
            legacy_multiplier = 1.5  # Retirement age, less legacy focus
        
        # Apply realistic cap (3x annual income maximum)
        calculated_legacy = annual_income * legacy_multiplier
        return min(calculated_legacy, annual_income * 3)
    
    def _calculate_special_needs(self, special_needs: str) -> float:
        """Calculate special needs funding"""
        if not special_needs or special_needs.lower() == "no":
            return 0
        
        # If special needs mentioned, allocate additional funding
        # This is a simplified calculation - in practice would need more details
        return 100000  # $100k for special needs
    
    def _determine_product_recommendation(self, age: int, annual_income: float, dependents: int, total_need: float) -> str:
        """Determine product recommendation"""
        
        # Debug logging
        print(f"DEBUG: Product recommendation - age: {age}, annual_income: ${annual_income:,.2f}, dependents: {dependents}, total_need: ${total_need:,.2f}")
        
        # Determine if client should consider IUL vs Term
        should_consider_iul = (
            age < 45 and  # Young enough to benefit from cash value growth
            annual_income >= 100000 and  # High enough income to afford premiums
            dependents > 0  # Has dependents to protect
        )
        
        print(f"DEBUG: Product recommendation - should_consider_iul: {should_consider_iul}")
        print(f"DEBUG: Product recommendation - age < 45: {age < 45}, annual_income >= 100000: {annual_income >= 100000}, dependents > 0: {dependents > 0}")
        
        if should_consider_iul:
            # Recommend IUL with term conversion option
            recommendation = "JPM TermVest+ IUL Track"
            print(f"DEBUG: Product recommendation - recommending IUL Track: {recommendation}")
            return recommendation
        else:
            # Recommend term life
            if age < 30:
                recommendation = "JPM TermVest+ Term Track"
            elif age < 40:
                recommendation = "JPM TermVest+ Term Track"
            elif age < 50:
                recommendation = "JPM TermVest+ Term Track"
            else:
                recommendation = "JPM TermVest+ Term Track"
            
            print(f"DEBUG: Product recommendation - recommending Term Track: {recommendation}")
            return recommendation
    
    def _determine_duration(self, age: int, annual_income: float, dependents: int) -> int:
        """Determine duration based on age and income"""
        if age < 30:
            return 30
        elif age < 40:
            return 25
        elif age < 50:
            return 20
        else:
            return 15
    
    def _generate_rationale(self, age: int, annual_income: float, dependents: int, total_need: float, product_recommendation: str) -> str:
        """Generate rationale for the recommendation"""
        if product_recommendation == "JPM TermVest+ IUL Track":
            return (
                f"At age {age} with ${annual_income:,.0f} annual income and {dependents} dependents, "
                "you're an ideal candidate for the IUL Track. Start with term coverage and convert "
                "to permanent coverage as your financial situation allows, building cash value for "
                "retirement and legacy planning."
            )
        else:
            return (
                f"Term life insurance provides essential protection at an affordable premium. "
                f"With {self._determine_duration(age, annual_income, dependents)} years of coverage, "
                f"you'll have protection during your peak earning years and family responsibilities. "
                f"You can convert to permanent coverage later when your financial situation allows."
            )
    
    def _get_default_needs(self) -> LifeInsuranceNeeds:
        """Return default needs in case of calculation failure"""
        return LifeInsuranceNeeds(
            total_need=0,
            income_replacement=0,
            debt_payoff=0,
            education_funding=0,
            funeral_expenses=0,
            legacy_amount=0,
            special_needs=0,
            coverage_gap=0,
            recommended_coverage=0,
            duration_years=0,
            product_recommendation="",
            rationale=""
        ) 
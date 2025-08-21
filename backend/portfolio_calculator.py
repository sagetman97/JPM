"""
Portfolio Analysis Calculator
Implements proper portfolio calculations for asset allocation, health scoring, and risk analysis.
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import math

@dataclass
class PortfolioMetrics:
    """Portfolio analysis metrics"""
    total_assets: float
    asset_allocation_percentages: Dict[str, float]
    portfolio_health_score: int
    risk_level: str
    risk_score: int
    liquidity_ratio: float
    diversification_score: int
    concentration_risks: List[str]
    rebalancing_needs: List[str]
    industry_benchmarks: Dict[str, Any]

class PortfolioCalculator:
    """Calculate portfolio metrics and health indicators"""
    
    def __init__(self):
        # Industry standard benchmarks by age
        self.age_benchmarks = {
            25: {"equity": 0.80, "fixed_income": 0.20, "cash": 0.05},
            30: {"equity": 0.75, "fixed_income": 0.25, "cash": 0.05},
            35: {"equity": 0.70, "fixed_income": 0.30, "cash": 0.05},
            40: {"equity": 0.65, "fixed_income": 0.35, "cash": 0.05},
            45: {"equity": 0.60, "fixed_income": 0.40, "cash": 0.05},
            50: {"equity": 0.55, "fixed_income": 0.45, "cash": 0.05},
            55: {"equity": 0.50, "fixed_income": 0.50, "cash": 0.05},
            60: {"equity": 0.45, "fixed_income": 0.55, "cash": 0.05},
            65: {"equity": 0.40, "fixed_income": 0.60, "cash": 0.05},
            70: {"equity": 0.35, "fixed_income": 0.65, "cash": 0.05}
        }
    
    def calculate_portfolio_metrics(self, portfolio_data: Dict[str, Any]) -> PortfolioMetrics:
        """Calculate comprehensive portfolio metrics"""
        
        # Debug logging
        print(f"DEBUG: Portfolio calculator received data keys: {list(portfolio_data.keys())}")
        print(f"DEBUG: Portfolio calculator - age: {portfolio_data.get('age')}, total_assets: {portfolio_data.get('total_assets')}")
        
        # Extract key values from portfolio_data
        age = self._parse_number(portfolio_data.get("age", 35))
        equity = self._parse_number(portfolio_data.get("equity", 0))
        fixed_income = self._parse_number(portfolio_data.get("fixed_income", 0))
        real_estate = self._parse_number(portfolio_data.get("real_estate", 0))
        cash = self._parse_number(portfolio_data.get("cash", 0))
        alternative = self._parse_number(portfolio_data.get("alternative_investments", 0))
        investable_portfolio = self._parse_number(portfolio_data.get("investable_portfolio", 0))
        total_assets = self._parse_number(portfolio_data.get("total_assets", 0))
        liquid_assets = self._parse_number(portfolio_data.get("liquid_assets", 0))
        monthly_expenses = self._parse_number(portfolio_data.get("monthly_expenses", 0))
        total_liabilities = self._parse_number(portfolio_data.get("total_liabilities", 0))
        
        # Debug logging for extracted values
        print(f"DEBUG: Portfolio calculator extracted values:")
        print(f"  - age: {age}, equity: ${equity:,.2f}, fixed_income: ${fixed_income:,.2f}")
        print(f"  - real_estate: ${real_estate:,.2f}, cash: ${cash:,.2f}, alternative: ${alternative:,.2f}")
        print(f"  - investable_portfolio: ${investable_portfolio:,.2f}, total_assets: ${total_assets:,.2f}")
        print(f"  - liquid_assets: ${liquid_assets:,.2f}, monthly_expenses: ${monthly_expenses:,.2f}")
        print(f"  - total_liabilities: ${total_liabilities:,.2f}")
        
        # Validate asset allocation values
        if equity < 0:
            print(f"Warning: Equity allocation is negative: {equity}")
            equity = 0
        
        if fixed_income < 0:
            print(f"Warning: Fixed income allocation is negative: {fixed_income}")
            fixed_income = 0
        
        if real_estate < 0:
            print(f"Warning: Real estate allocation is negative: {real_estate}")
            real_estate = 0
        
        if cash < 0:
            print(f"Warning: Cash allocation is negative: {cash}")
            cash = 0
        
        if alternative < 0:
            print(f"Warning: Alternative allocation is negative: {alternative}")
            alternative = 0
        
        # Validate data consistency
        if total_assets < 0:
            print(f"Warning: Total assets is negative: {total_assets}")
            total_assets = 0
        
        if investable_portfolio < 0:
            print(f"Warning: Investable portfolio is negative: {investable_portfolio}")
            investable_portfolio = 0
        
        if investable_portfolio > total_assets:
            print(f"Warning: Investable portfolio ({investable_portfolio}) exceeds total assets ({total_assets})")
            investable_portfolio = total_assets
        
        if liquid_assets < 0:
            print(f"Warning: Liquid assets is negative: {liquid_assets}")
            liquid_assets = 0
        
        if liquid_assets > total_assets:
            print(f"Warning: Liquid assets ({liquid_assets}) exceeds total assets ({total_assets})")
            liquid_assets = total_assets
        
        # Use investable_portfolio if available, otherwise calculate it
        if investable_portfolio > 0:
            total_investable = investable_portfolio
        else:
            # Calculate total investable assets (excluding real estate for allocation purposes)
            total_investable = equity + fixed_income + cash + alternative
        
        # Calculate asset allocation percentages (based on investable assets, not total portfolio)
        asset_allocation_percentages = self._calculate_allocation_percentages(
            equity, fixed_income, cash, alternative, total_investable
        )
        
        # Add real estate allocation percentage (based on total assets including real estate)
        if total_assets > 0:
            real_estate_percentage = round((real_estate / total_assets) * 100, 1)
            asset_allocation_percentages["real_estate"] = real_estate_percentage
        else:
            asset_allocation_percentages["real_estate"] = 0
        
        # Calculate portfolio health score
        portfolio_health_score = self._calculate_portfolio_health_score(
            portfolio_data, asset_allocation_percentages, total_investable
        )
        
        # Calculate risk metrics
        risk_level, risk_score = self._calculate_risk_metrics(
            age, asset_allocation_percentages, total_investable, total_assets, real_estate, total_liabilities
        )
        
        # Calculate liquidity ratio - use liquid_assets from portfolio_data, not from asset allocation
        liquid_assets = self._parse_number(portfolio_data.get("liquid_assets", 0))
        monthly_expenses = self._parse_number(portfolio_data.get("monthly_expenses", 0))
        liquidity_ratio = self._calculate_liquidity_ratio(liquid_assets, monthly_expenses)
        
        print(f"DEBUG: Liquidity ratio calculation - liquid_assets: ${liquid_assets:,.2f}, monthly_expenses: ${monthly_expenses:,.2f}, ratio: {liquidity_ratio}")
        
        # Calculate diversification score
        diversification_score = self._calculate_diversification_score(asset_allocation_percentages)
        
        # Identify concentration risks
        concentration_risks = self._identify_concentration_risks(
            asset_allocation_percentages, real_estate, total_assets
        )
        
        # Identify rebalancing needs
        rebalancing_needs = self._identify_rebalancing_needs(
            age, asset_allocation_percentages, self._get_age_benchmark(age)
        )
        
        # Get industry benchmarks
        industry_benchmarks = self._get_industry_benchmarks(age, total_assets)
        
        return PortfolioMetrics(
            total_assets=total_investable,
            asset_allocation_percentages=asset_allocation_percentages,
            portfolio_health_score=portfolio_health_score,
            risk_level=risk_level,
            risk_score=risk_score,
            liquidity_ratio=liquidity_ratio,
            diversification_score=diversification_score,
            concentration_risks=concentration_risks,
            rebalancing_needs=rebalancing_needs,
            industry_benchmarks=industry_benchmarks
        )
    
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
    
    def _calculate_allocation_percentages(self, equity: float, fixed_income: float, cash: float, alternative: float, total: float) -> Dict[str, float]:
        """Calculate asset allocation percentages based on investable assets"""
        if total <= 0:
            return {"equity": 0, "fixed_income": 0, "cash": 0, "alternative": 0}
        
        return {
            "equity": round((equity / total) * 100, 1),
            "fixed_income": round((fixed_income / total) * 100, 1),
            "cash": round((cash / total) * 100, 1),
            "alternative": round((alternative / total) * 100, 1)
        }
    
    def _calculate_portfolio_health_score(self, portfolio_data: Dict[str, Any], allocation: Dict[str, float], total_investable: float) -> int:
        """Calculate portfolio health score (0-100) with real estate concentration penalties"""
        score = 0
        
        # Debug logging
        print(f"DEBUG: Portfolio health score calculation - portfolio_data keys: {list(portfolio_data.keys())}")
        print(f"DEBUG: Portfolio health score calculation - allocation: {allocation}")
        print(f"DEBUG: Portfolio health score calculation - total_investable: ${total_investable:,.2f}")
        
        # Asset allocation diversity (30 points)
        if allocation["equity"] > 0:
            score += 8
        if allocation["fixed_income"] > 0:
            score += 8
        if allocation["cash"] > 0:
            score += 7
        if allocation["alternative"] > 0:
            score += 7
        
        # Portfolio size adequacy (20 points)
        total_assets = self._parse_number(portfolio_data.get("total_assets", 0))
        if total_assets >= 1000000:  # $1M+
            score += 20
        elif total_assets >= 500000:  # $500K+
            score += 15
        elif total_assets >= 100000:  # $100K+
            score += 10
        
        # Liquidity adequacy (20 points)
        liquid_assets = self._parse_number(portfolio_data.get("liquid_assets", 0))
        monthly_expenses = self._parse_number(portfolio_data.get("monthly_expenses", 0))
        if monthly_expenses > 0:
            months_coverage = liquid_assets / monthly_expenses
            if months_coverage >= 6:
                score += 20
            elif months_coverage >= 3:
                score += 15
            elif months_coverage >= 1:
                score += 10
        
        # Insurance coverage (15 points)
        individual_life = self._parse_number(portfolio_data.get("individual_life", 0))
        if individual_life > 0:
            score += 15
        
        # Real estate concentration penalty (context-aware)
        # Use real_estate_allocation from the allocation parameter (percentage) and convert to dollar value
        real_estate_percentage = allocation.get("real_estate", 0)
        real_estate_value = (real_estate_percentage / 100) * total_assets
        total_assets_value = total_assets
        net_worth = total_assets_value - self._parse_number(portfolio_data.get("total_liabilities", 0))
        
        print(f"DEBUG: Portfolio health score - real_estate_percentage: {real_estate_percentage}%, real_estate_value: ${real_estate_value:,.2f}")
        print(f"DEBUG: Portfolio health score - total_assets: ${total_assets_value:,.2f}, net_worth: ${net_worth:,.2f}")
        
        if total_assets_value > 0:
            real_estate_concentration = real_estate_value / total_assets_value
            # Context-aware penalties based on net worth
            if real_estate_concentration > 0.7:  # Over 70% in real estate
                if net_worth > 1000000:  # High net worth
                    score -= 10
                else:
                    score -= 20
            elif real_estate_concentration > 0.5:  # Over 50% in real estate
                if net_worth > 500000:  # Moderate net worth
                    score -= 5
                else:
                    score -= 15
            elif real_estate_concentration > 0.3:  # Over 30% in real estate
                if net_worth > 250000:  # Lower net worth
                    score -= 3
                else:
                    score -= 8
        
        print(f"DEBUG: Portfolio health score final: {score}/100")
        return max(0, min(100, score))
    
    def _calculate_risk_metrics(self, age: int, allocation: Dict[str, float], total_investable: float, total_assets: float, real_estate: float, total_liabilities: float = 0) -> Tuple[str, int]:
        """Calculate risk metrics based on age and allocation"""
        risk_score = 50  # Start with moderate risk
        
        # Age-based risk adjustment
        if age < 30:
            risk_score -= 20  # Younger = more aggressive
        elif age < 40:
            risk_score -= 10
        elif age < 50:
            risk_score += 0  # Neutral
        elif age < 60:
            risk_score += 10
        else:
            risk_score += 15  # More conservative for older
        
        # Asset allocation risk adjustment
        if allocation["equity"] > 70:
            risk_score -= 20  # High equity = aggressive
        elif allocation["equity"] > 50:
            risk_score -= 10
        elif allocation["equity"] < 30:
            risk_score += 15  # Low equity = conservative
        
        # Real estate concentration risk adjustment (context-aware)
        if total_assets > 0 and total_investable > 0:
            real_estate_concentration = real_estate / total_assets
            net_worth = total_assets - total_liabilities
            
            # Context-aware risk assessment
            if real_estate_concentration > 0.7:  # Over 70% in real estate
                risk_score += 25  # High concentration risk
            elif real_estate_concentration > 0.5:  # Over 50% in real estate
                # Check if this is appropriate for net worth level
                if net_worth > 1000000:  # High net worth can handle concentration
                    risk_score += 10
                else:
                    risk_score += 20
            elif real_estate_concentration > 0.3:  # Over 30% in real estate
                if net_worth > 500000:  # Moderate net worth
                    risk_score += 5
                else:
                    risk_score += 15
        
        # Determine risk level based on final score
        if risk_score >= 70:
            risk_level = "low"
        elif risk_score >= 40:
            risk_level = "moderate"
        else:
            risk_level = "high"  # High real estate concentration = high risk
        
        return risk_level, risk_score
    
    def _calculate_liquidity_ratio(self, liquid_assets: float, monthly_expenses: float) -> float:
        """Calculate liquidity ratio (months of expenses covered)"""
        if monthly_expenses <= 0:
            return 0
        
        months_coverage = liquid_assets / monthly_expenses
        return round(months_coverage, 1)
    
    def _calculate_diversification_score(self, allocation: Dict[str, float]) -> int:
        """Calculate diversification score (0-100)"""
        score = 0
        
        # Reward for having multiple asset classes
        asset_classes = sum(1 for pct in allocation.values() if pct > 0)
        score += asset_classes * 25
        
        # Bonus for balanced allocation (no single class > 60%)
        max_allocation = max(allocation.values())
        if max_allocation <= 60:
            score += 25
        
        return min(score, 100)
    
    def _identify_concentration_risks(self, allocation: Dict[str, float], real_estate: float, total_assets: float) -> List[str]:
        """Identify concentration risks in the portfolio"""
        risks = []
        
        # Check for over-concentration in single asset class
        if allocation["equity"] > 70:
            risks.append("High equity concentration - consider diversification")
        if allocation["fixed_income"] > 60:
            risks.append("High fixed income concentration - may limit growth")
        if allocation["cash"] > 30:
            risks.append("High cash concentration - may lose to inflation")
        
        # Check real estate concentration (context-aware)
        if total_assets > 0:
            real_estate_pct = (real_estate / total_assets) * 100
            if real_estate_pct > 70:
                risks.append(f"Very high real estate concentration ({real_estate_pct:.1f}%) - consider diversification")
            elif real_estate_pct > 50:
                risks.append(f"High real estate concentration ({real_estate_pct:.1f}%) - monitor liquidity needs")
            elif real_estate_pct > 30:
                risks.append(f"Moderate real estate concentration ({real_estate_pct:.1f}%) - ensure adequate diversification")
        
        return risks
    
    def _identify_rebalancing_needs(self, age: int, current_allocation: Dict[str, float], target_allocation: Dict[str, float]) -> List[str]:
        """Identify rebalancing needs based on age-appropriate targets"""
        needs = []
        
        # Check equity allocation
        target_equity = target_allocation.get("equity", 70)
        current_equity = current_allocation.get("equity", 0)
        
        if current_equity < target_equity - 10:
            needs.append(f"Increase equity allocation from {current_equity}% to target {target_equity}%")
        elif current_equity > target_equity + 10:
            needs.append(f"Reduce equity allocation from {current_equity}% to target {target_equity}%")
        
        # Check fixed income allocation
        target_fixed = target_allocation.get("fixed_income", 30)
        current_fixed = current_allocation.get("fixed_income", 0)
        
        if current_fixed < target_fixed - 10:
            needs.append(f"Increase fixed income allocation from {current_fixed}% to target {target_fixed}%")
        elif current_fixed > target_fixed + 10:
            needs.append(f"Reduce fixed income allocation from {current_fixed}% to target {target_fixed}%")
        
        return needs
    
    def _get_age_benchmark(self, age: int) -> Dict[str, float]:
        """Get age-appropriate asset allocation benchmark"""
        # Find closest age benchmark
        ages = sorted(self.age_benchmarks.keys())
        closest_age = min(ages, key=lambda x: abs(x - age))
        return self.age_benchmarks[closest_age]
    
    def _get_industry_benchmarks(self, age: int, portfolio_value: float) -> Dict[str, Any]:
        """Get industry benchmarks for comparison"""
        target_allocation = self._get_age_benchmark(age)
        
        # Portfolio size benchmarks by age
        portfolio_benchmarks = {
            25: 50000,
            30: 100000,
            35: 150000,
            40: 250000,
            45: 400000,
            50: 600000,
            55: 800000,
            60: 1000000,
            65: 1200000,
            70: 1400000
        }
        
        closest_age = min(portfolio_benchmarks.keys(), key=lambda x: abs(x - age))
        avg_portfolio_size = portfolio_benchmarks[closest_age]
        
        return {
            "age": age,
            "target_equity": target_allocation["equity"] * 100,
            "target_fixed_income": target_allocation["fixed_income"] * 100,
            "avg_portfolio_size": avg_portfolio_size,
            "portfolio_size_percentile": self._calculate_percentile(portfolio_value, avg_portfolio_size)
        }
    
    def _calculate_percentile(self, value: float, benchmark: float) -> str:
        """Calculate percentile relative to benchmark"""
        if benchmark <= 0:
            return "Unknown"
        
        ratio = value / benchmark
        if ratio >= 2.0:
            return "Top 10%"
        elif ratio >= 1.5:
            return "Top 25%"
        elif ratio >= 1.0:
            return "Above Average"
        elif ratio >= 0.7:
            return "Average"
        elif ratio >= 0.5:
            return "Below Average"
        else:
            return "Needs Improvement" 
"""
Portfolio Analysis Agent for Financial Advisor Assistant

This agent analyzes uploaded portfolio data and provides recommendations on how
life insurance fits into the client's overall financial plan and risk management strategy.
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import MessagesPlaceholder
import json
import re
import pandas as pd

from utils.confidence import assess_confidence_score
from utils.file_processing import extract_financial_data_from_excel, extract_portfolio_summary
from config.settings import settings

class PortfolioAgent:
    """
    Portfolio analysis agent that analyzes financial data and provides life insurance integration recommendations.
    """
    
    def __init__(self, llm: ChatOpenAI, calculator_agent):
        self.llm = llm
        self.calculator_agent = calculator_agent
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        
        # Portfolio analysis prompt
        self.portfolio_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial advisor specializing in portfolio analysis and life insurance integration.

Your role is to analyze client portfolios and provide comprehensive recommendations on how life insurance fits into their overall financial strategy.

**Portfolio Analysis Framework:**
1. **Asset Allocation Review**: Analyze current asset allocation and risk exposure
2. **Risk Assessment**: Evaluate portfolio risk and identify gaps in risk management
3. **Life Insurance Integration**: Determine how life insurance complements the portfolio
4. **Holistic Planning**: Show how life insurance supports overall financial goals
5. **Implementation Strategy**: Provide actionable steps for integration

**Key Analysis Areas:**
- **Risk Management**: How life insurance reduces portfolio risk
- **Asset Protection**: Protecting accumulated wealth and income streams
- **Estate Planning**: Life insurance in estate and legacy planning
- **Tax Efficiency**: Tax advantages of life insurance in portfolio context
- **Liquidity Management**: Life insurance as a source of liquidity
- **Diversification**: Life insurance as a non-correlated asset class

**Life Insurance Benefits in Portfolio Context:**
- **Risk Reduction**: Protects against loss of income and wealth
- **Tax Advantages**: Tax-deferred growth, tax-free death benefits
- **Liquidity**: Cash value can provide emergency funds
- **Estate Planning**: Efficient wealth transfer and legacy creation
- **Business Continuity**: Key person insurance for business owners
- **Retirement Planning**: Supplement retirement income with cash value

**Recommendation Structure:**
1. **Portfolio Summary**: Current allocation and risk profile
2. **Risk Analysis**: Identified gaps and vulnerabilities
3. **Life Insurance Recommendations**: Specific products and amounts
4. **Integration Strategy**: How to implement recommendations
5. **Monitoring Plan**: Ongoing review and adjustment process

**Response Guidelines:**
- Focus on life insurance as part of holistic financial planning
- Emphasize risk management and portfolio diversification benefits
- Provide specific, actionable recommendations
- Consider client's unique circumstances and goals
- Explain the rationale behind each recommendation
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Risk assessment prompt
        self.risk_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a risk assessment specialist analyzing financial portfolios for life insurance integration.

**Risk Assessment Framework:**
1. **Income Risk**: Vulnerability to loss of primary income
2. **Asset Risk**: Exposure to market volatility and loss
3. **Liability Risk**: Potential financial obligations and debts
4. **Longevity Risk**: Outliving retirement savings
5. **Inflation Risk**: Purchasing power erosion over time
6. **Tax Risk**: Tax implications of current and future financial decisions

**Life Insurance Risk Mitigation:**
- **Income Protection**: Replaces lost income for dependents
- **Debt Protection**: Covers outstanding debts and obligations
- **Asset Protection**: Preserves accumulated wealth
- **Tax Efficiency**: Provides tax-advantaged growth and transfer
- **Liquidity**: Offers emergency funds through cash value
- **Legacy Planning**: Ensures wealth transfer to beneficiaries

**Assessment Criteria:**
- Age and health of primary income earner
- Family situation and dependents
- Current debt levels and obligations
- Portfolio size and allocation
- Income stability and growth potential
- Financial goals and time horizons
- Existing insurance coverage
- Tax situation and estate planning needs

Provide a comprehensive risk assessment with specific life insurance recommendations.
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the analysis chains
        self.portfolio_chain = self.portfolio_prompt | self.llm | self.json_parser
        self.risk_chain = self.risk_prompt | self.llm | self.str_parser
    
    def analyze_portfolio_data(self, portfolio_data: Dict[str, Any], client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze portfolio data and provide life insurance integration recommendations.
        
        Args:
            portfolio_data: Extracted portfolio information
            client_info: Additional client information
            
        Returns:
            Dict with portfolio analysis and recommendations
        """
        # Prepare analysis context
        analysis_context = {
            "portfolio_data": portfolio_data,
            "client_info": client_info or {},
            "analysis_framework": [
                "asset_allocation",
                "risk_assessment", 
                "life_insurance_integration",
                "holistic_planning",
                "implementation_strategy"
            ]
        }
        
        # Generate portfolio analysis
        analysis_result = self.portfolio_chain.invoke({
            "messages": [HumanMessage(content=f"Analyze portfolio for life insurance integration: {json.dumps(analysis_context)}")]
        })
        
        return analysis_result
    
    def assess_portfolio_risk(self, portfolio_data: Dict[str, Any], client_info: Dict[str, Any] = None) -> str:
        """
        Assess portfolio risk and identify life insurance needs.
        
        Args:
            portfolio_data: Portfolio information
            client_info: Client information
            
        Returns:
            Risk assessment and recommendations
        """
        # Prepare risk assessment context
        risk_context = {
            "portfolio_data": portfolio_data,
            "client_info": client_info or {},
            "risk_categories": [
                "income_risk",
                "asset_risk", 
                "liability_risk",
                "longevity_risk",
                "inflation_risk",
                "tax_risk"
            ]
        }
        
        # Generate risk assessment
        risk_assessment = self.risk_chain.invoke({
            "messages": [HumanMessage(content=f"Assess portfolio risk and life insurance needs: {json.dumps(risk_context)}")]
        })
        
        return risk_assessment
    
    def calculate_portfolio_based_coverage(self, portfolio_data: Dict[str, Any], client_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate life insurance coverage needs based on portfolio analysis.
        
        Args:
            portfolio_data: Portfolio information
            client_info: Client information
            
        Returns:
            Coverage recommendations based on portfolio analysis
        """
        # Extract key portfolio metrics
        total_assets = portfolio_data.get("total_assets", 0)
        annual_income = portfolio_data.get("annual_income", 0)
        debts = portfolio_data.get("total_debts", 0)
        dependents = client_info.get("dependents", 0) if client_info else 0
        
        # Calculate coverage needs based on portfolio
        portfolio_based_coverage = {
            "asset_protection": total_assets * 0.1,  # 10% of assets for protection
            "income_replacement": annual_income * 10,  # 10x annual income
            "debt_coverage": debts * 1.2,  # 120% of debts for safety margin
            "education_funding": dependents * 50000,  # $50k per dependent for education
            "estate_tax_coverage": total_assets * 0.4,  # 40% for potential estate taxes
            "business_continuity": annual_income * 5 if portfolio_data.get("business_owner", False) else 0
        }
        
        # Calculate total recommended coverage
        total_coverage = sum(portfolio_based_coverage.values())
        
        # Adjust based on existing coverage
        existing_coverage = portfolio_data.get("existing_life_insurance", 0)
        additional_coverage_needed = max(0, total_coverage - existing_coverage)
        
        return {
            "portfolio_based_coverage": portfolio_based_coverage,
            "total_recommended_coverage": total_coverage,
            "existing_coverage": existing_coverage,
            "additional_coverage_needed": additional_coverage_needed,
            "coverage_breakdown": {
                "asset_protection_pct": (portfolio_based_coverage["asset_protection"] / total_coverage * 100) if total_coverage > 0 else 0,
                "income_replacement_pct": (portfolio_based_coverage["income_replacement"] / total_coverage * 100) if total_coverage > 0 else 0,
                "debt_coverage_pct": (portfolio_based_coverage["debt_coverage"] / total_coverage * 100) if total_coverage > 0 else 0,
                "education_funding_pct": (portfolio_based_coverage["education_funding"] / total_coverage * 100) if total_coverage > 0 else 0,
                "estate_tax_coverage_pct": (portfolio_based_coverage["estate_tax_coverage"] / total_coverage * 100) if total_coverage > 0 else 0,
                "business_continuity_pct": (portfolio_based_coverage["business_continuity"] / total_coverage * 100) if total_coverage > 0 else 0
            }
        }
    
    def recommend_portfolio_integration(self, portfolio_data: Dict[str, Any], coverage_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend how to integrate life insurance into the portfolio.
        
        Args:
            portfolio_data: Portfolio information
            coverage_analysis: Coverage needs analysis
            
        Returns:
            Integration recommendations
        """
        total_assets = portfolio_data.get("total_assets", 0)
        additional_coverage = coverage_analysis.get("additional_coverage_needed", 0)
        portfolio_allocation = portfolio_data.get("asset_allocation", {})
        
        # Calculate recommended premium allocation
        recommended_premium_allocation = {
            "percentage_of_income": min(0.15, additional_coverage / (portfolio_data.get("annual_income", 1) * 100)),
            "percentage_of_assets": min(0.05, additional_coverage / (total_assets * 100)) if total_assets > 0 else 0.02,
            "monthly_premium_budget": additional_coverage * 0.001  # Rough estimate: $1 per $1000 coverage
        }
        
        # Recommend policy types based on portfolio characteristics
        policy_recommendations = []
        
        # Term Life for basic protection
        if additional_coverage > 0:
            policy_recommendations.append({
                "type": "Term Life",
                "amount": additional_coverage * 0.7,  # 70% of additional coverage
                "rationale": "Cost-effective basic protection",
                "portfolio_benefit": "Provides essential risk protection without impacting investment allocation"
            })
        
        # Whole Life for permanent needs and cash value
        if total_assets > 1000000:  # High net worth clients
            policy_recommendations.append({
                "type": "Whole Life",
                "amount": additional_coverage * 0.3,  # 30% of additional coverage
                "rationale": "Permanent protection with cash value accumulation",
                "portfolio_benefit": "Provides tax-advantaged cash value growth and estate planning benefits"
            })
        
        # Universal Life for flexibility
        if portfolio_data.get("variable_income", False) or portfolio_data.get("business_owner", False):
            policy_recommendations.append({
                "type": "Universal Life",
                "amount": additional_coverage * 0.2,  # 20% of additional coverage
                "rationale": "Flexible premiums and death benefit",
                "portfolio_benefit": "Adapts to changing financial circumstances and business needs"
            })
        
        return {
            "premium_allocation": recommended_premium_allocation,
            "policy_recommendations": policy_recommendations,
            "integration_strategy": {
                "immediate_actions": [
                    "Implement term life coverage for basic protection",
                    "Review existing insurance coverage",
                    "Establish premium budget within portfolio allocation"
                ],
                "long_term_planning": [
                    "Consider permanent life insurance for estate planning",
                    "Integrate life insurance into overall financial plan",
                    "Regular review and adjustment of coverage needs"
                ],
                "monitoring_plan": [
                    "Annual review of coverage adequacy",
                    "Portfolio rebalancing to accommodate insurance premiums",
                    "Adjust coverage as financial circumstances change"
                ]
            }
        }
    
    def analyze_uploaded_portfolio(self, file_data: Dict[str, Any], session_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze uploaded portfolio file and provide comprehensive recommendations.
        
        Args:
            file_data: Extracted data from uploaded file
            session_context: Current session context
            
        Returns:
            Comprehensive portfolio analysis and life insurance recommendations
        """
        # Extract portfolio data
        portfolio_data = self._extract_portfolio_metrics(file_data)
        
        # Get client info from session context
        client_info = session_context.get("client_info", {}) if session_context else {}
        
        # Perform portfolio analysis
        portfolio_analysis = self.analyze_portfolio_data(portfolio_data, client_info)
        
        # Assess portfolio risk
        risk_assessment = self.assess_portfolio_risk(portfolio_data, client_info)
        
        # Calculate coverage needs
        coverage_analysis = self.calculate_portfolio_based_coverage(portfolio_data, client_info)
        
        # Get integration recommendations
        integration_recommendations = self.recommend_portfolio_integration(portfolio_data, coverage_analysis)
        
        # Combine with calculator agent for comprehensive analysis
        if client_info:
            calculator_analysis = self.calculator_agent.calculate_needs_analysis(client_info)
        else:
            calculator_analysis = {}
        
        return {
            "portfolio_analysis": portfolio_analysis,
            "risk_assessment": risk_assessment,
            "coverage_analysis": coverage_analysis,
            "integration_recommendations": integration_recommendations,
            "calculator_analysis": calculator_analysis,
            "portfolio_data": portfolio_data,
            "client_info": client_info
        }
    
    def _extract_portfolio_metrics(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key portfolio metrics from uploaded file data.
        
        Args:
            file_data: Raw file data
            
        Returns:
            Extracted portfolio metrics
        """
        # Extract basic metrics
        portfolio_metrics = {
            "total_assets": file_data.get("total_assets", 0),
            "annual_income": file_data.get("annual_income", 0),
            "total_debts": file_data.get("total_debts", 0),
            "existing_life_insurance": file_data.get("existing_life_insurance", 0),
            "asset_allocation": file_data.get("asset_allocation", {}),
            "business_owner": file_data.get("business_owner", False),
            "variable_income": file_data.get("variable_income", False),
            "retirement_accounts": file_data.get("retirement_accounts", 0),
            "investment_accounts": file_data.get("investment_accounts", 0),
            "real_estate": file_data.get("real_estate", 0),
            "cash_equivalents": file_data.get("cash_equivalents", 0)
        }
        
        # Calculate derived metrics
        if portfolio_metrics["total_assets"] > 0:
            portfolio_metrics["debt_to_assets_ratio"] = portfolio_metrics["total_debts"] / portfolio_metrics["total_assets"]
            portfolio_metrics["insurance_to_assets_ratio"] = portfolio_metrics["existing_life_insurance"] / portfolio_metrics["total_assets"]
        else:
            portfolio_metrics["debt_to_assets_ratio"] = 0
            portfolio_metrics["insurance_to_assets_ratio"] = 0
        
        return portfolio_metrics
    
    def get_portfolio_feedback(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate user-friendly feedback about the portfolio analysis.
        
        Args:
            analysis_result: Result from portfolio analysis
            
        Returns:
            Feedback message for the user
        """
        coverage_analysis = analysis_result.get("coverage_analysis", {})
        additional_coverage = coverage_analysis.get("additional_coverage_needed", 0)
        total_assets = analysis_result.get("portfolio_data", {}).get("total_assets", 0)
        
        if additional_coverage > 0:
            return f"I've analyzed your portfolio and identified a need for approximately ${additional_coverage:,.0f} in additional life insurance coverage. This analysis considers your ${total_assets:,.0f} in assets, income, debts, and overall financial situation."
        else:
            return "I've analyzed your portfolio and your current life insurance coverage appears adequate for your financial situation. However, I recommend regular reviews as your circumstances change." 
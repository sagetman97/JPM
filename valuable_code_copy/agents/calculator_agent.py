"""
Life Insurance Calculator Agent for Financial Advisor Assistant

This agent provides interactive life insurance needs analysis and policy recommendations
based on user financial information and goals.
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

from utils.confidence import assess_confidence_score
from config.settings import settings

class CalculatorAgent:
    """
    Life insurance calculator agent that provides needs analysis and policy recommendations.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.json_parser = JsonOutputParser()
        self.str_parser = StrOutputParser()
        
        # Calculator prompt for structured analysis
        self.calculator_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert life insurance calculator and financial advisor specializing in life insurance needs analysis.

Your role is to help financial advisors and their clients determine appropriate life insurance coverage amounts and policy types.

**Calculation Methods:**
1. **Human Life Value Method**: Annual income × years until retirement
2. **Needs-Based Method**: Income replacement + debt payoff + education + final expenses
3. **DIME Method**: Debt + Income + Mortgage + Education
4. **Rule of Thumb**: 10-15x annual income

**Policy Types to Recommend:**
- **Term Life**: Temporary coverage, lower cost, no cash value
- **Whole Life**: Permanent coverage, cash value, higher cost
- **Universal Life**: Flexible premiums, cash value, adjustable death benefit
- **Indexed Universal Life**: Cash value tied to market index, potential growth
- **Variable Universal Life**: Investment component, higher risk/reward

**Key Factors to Consider:**
- Age and health of insured
- Income and earning potential
- Existing assets and liabilities
- Family situation and dependents
- Risk tolerance and financial goals
- Budget constraints
- Existing insurance coverage

**Recommendation Framework:**
1. Calculate multiple coverage amounts using different methods
2. Consider client's specific circumstances and goals
3. Recommend appropriate policy type based on needs and budget
4. Provide rationale for recommendations
5. Suggest next steps for implementation

Return structured analysis with:
- Coverage amount recommendations
- Policy type recommendations
- Rationale for each recommendation
- Implementation steps
- Risk considerations
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Interactive prompt for Q&A sessions
        self.interactive_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an interactive life insurance calculator helping a financial advisor or client determine their life insurance needs.

**Your Approach:**
- Ask relevant questions to gather necessary information
- Provide immediate calculations and insights as information becomes available
- Explain the reasoning behind each calculation
- Suggest appropriate policy types based on the information provided
- Keep the conversation engaging and educational

**Key Information to Gather:**
- Age and health status
- Annual income and earning potential
- Family situation (spouse, children, dependents)
- Existing assets and liabilities
- Financial goals and risk tolerance
- Budget for insurance premiums
- Existing insurance coverage

**Calculation Methods to Use:**
- Income replacement (10-15x annual income)
- Needs-based analysis (debts + final expenses + education + income replacement)
- Human life value (income × years to retirement)
- DIME method (Debt + Income + Mortgage + Education)

**Policy Type Guidance:**
- **Term Life**: For temporary needs, budget-conscious clients
- **Whole Life**: For permanent needs, estate planning, cash value accumulation
- **Universal Life**: For flexibility in premiums and death benefit
- **Indexed Universal Life**: For cash value growth with market participation
- **Variable Universal Life**: For sophisticated investors seeking investment component

**Response Style:**
- Professional but conversational
- Educational - explain concepts clearly
- Actionable - provide specific recommendations
- Comprehensive - consider multiple factors
- Transparent - explain assumptions and limitations
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the calculator chains
        self.calculator_chain = self.calculator_prompt | self.llm | self.json_parser
        self.interactive_chain = self.interactive_prompt | self.llm | self.str_parser
    
    def calculate_needs_analysis(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive life insurance needs analysis.
        
        Args:
            client_info: Dictionary containing client information
            
        Returns:
            Dict with analysis results and recommendations
        """
        # Prepare client information for analysis
        analysis_context = {
            "client_info": client_info,
            "calculation_methods": ["human_life_value", "needs_based", "dime", "rule_of_thumb"],
            "policy_types": ["term", "whole", "universal", "indexed_universal", "variable_universal"]
        }
        
        # Generate structured analysis
        analysis_result = self.calculator_chain.invoke({
            "messages": [HumanMessage(content=f"Analyze life insurance needs for: {json.dumps(analysis_context)}")]
        })
        
        return analysis_result
    
    def interactive_calculation(self, query: str, session_context: Optional[Dict] = None) -> str:
        """
        Handle interactive calculator queries and provide immediate insights.
        
        Args:
            query: User's calculator-related query
            session_context: Current session context with client information
            
        Returns:
            Interactive response with calculations and insights
        """
        # Prepare context for interactive response
        context = {
            "query": query,
            "session_context": session_context or {},
            "client_info": session_context.get("client_info", {}) if session_context else {},
            "previous_calculations": session_context.get("calculator_history", []) if session_context else []
        }
        
        # Generate interactive response
        response = self.interactive_chain.invoke({
            "messages": [HumanMessage(content=f"Interactive calculation request: {json.dumps(context)}")]
        })
        
        return response
    
    def get_calculation_questions(self, current_info: Dict[str, Any] = None) -> List[str]:
        """
        Generate relevant questions to gather missing information for calculation.
        
        Args:
            current_info: Currently available client information
            
        Returns:
            List of questions to ask the client
        """
        current_info = current_info or {}
        
        # Define essential information categories
        essential_info = {
            "personal": ["age", "health_status", "occupation"],
            "financial": ["annual_income", "existing_assets", "debts"],
            "family": ["marital_status", "children", "dependents"],
            "goals": ["financial_goals", "risk_tolerance", "budget"],
            "existing_coverage": ["current_insurance", "employer_benefits"]
        }
        
        # Determine missing information
        missing_questions = []
        
        if not current_info.get("age"):
            missing_questions.append("What is your age? (This affects both coverage needs and premium rates)")
        
        if not current_info.get("annual_income"):
            missing_questions.append("What is your annual income? (This is crucial for calculating income replacement needs)")
        
        if not current_info.get("family_situation"):
            missing_questions.append("Do you have a spouse, children, or other dependents who rely on your income?")
        
        if not current_info.get("debts"):
            missing_questions.append("What are your current debts? (mortgage, loans, credit cards)")
        
        if not current_info.get("financial_goals"):
            missing_questions.append("What are your primary financial goals? (education funding, retirement, estate planning)")
        
        if not current_info.get("budget"):
            missing_questions.append("What monthly premium budget are you comfortable with?")
        
        return missing_questions
    
    def calculate_coverage_amounts(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate coverage amounts using multiple methods.
        
        Args:
            client_info: Client information for calculations
            
        Returns:
            Dict with calculated coverage amounts and methodology
        """
        income = client_info.get("annual_income", 0)
        age = client_info.get("age", 30)
        debts = client_info.get("debts", 0)
        dependents = client_info.get("dependents", 0)
        years_to_retirement = 65 - age if age < 65 else 0
        
        calculations = {
            "human_life_value": income * years_to_retirement if years_to_retirement > 0 else income * 20,
            "rule_of_thumb": income * 12,  # 12x annual income
            "needs_based": {
                "income_replacement": income * 10,
                "debt_payoff": debts,
                "final_expenses": 15000,
                "education_funding": dependents * 50000,
                "total": income * 10 + debts + 15000 + (dependents * 50000)
            },
            "dime": {
                "debt": debts,
                "income": income * 10,
                "mortgage": client_info.get("mortgage", 0),
                "education": dependents * 50000,
                "total": debts + (income * 10) + client_info.get("mortgage", 0) + (dependents * 50000)
            }
        }
        
        # Calculate recommended range
        amounts = [
            calculations["human_life_value"],
            calculations["rule_of_thumb"],
            calculations["needs_based"]["total"],
            calculations["dime"]["total"]
        ]
        
        recommended_range = {
            "minimum": min(amounts),
            "maximum": max(amounts),
            "recommended": sum(amounts) / len(amounts)
        }
        
        return {
            "calculations": calculations,
            "recommended_range": recommended_range,
            "methodology": "Multiple calculation methods used to provide comprehensive coverage analysis"
        }
    
    def recommend_policy_type(self, client_info: Dict[str, Any], coverage_amount: float) -> Dict[str, Any]:
        """
        Recommend appropriate policy type based on client circumstances.
        
        Args:
            client_info: Client information
            coverage_amount: Recommended coverage amount
            
        Returns:
            Dict with policy recommendations and rationale
        """
        age = client_info.get("age", 30)
        income = client_info.get("annual_income", 0)
        budget = client_info.get("budget", 0)
        risk_tolerance = client_info.get("risk_tolerance", "moderate")
        goals = client_info.get("financial_goals", [])
        
        recommendations = []
        
        # Term Life recommendations
        if budget < 100 or age > 50 or "temporary" in goals:
            recommendations.append({
                "type": "Term Life",
                "rationale": "Cost-effective temporary coverage",
                "pros": ["Lower premiums", "Simple structure", "Temporary needs"],
                "cons": ["No cash value", "Expires at term end"],
                "suitable_for": "Young families, budget-conscious clients"
            })
        
        # Whole Life recommendations
        if "permanent" in goals or "estate_planning" in goals or budget > 200:
            recommendations.append({
                "type": "Whole Life",
                "rationale": "Permanent coverage with cash value",
                "pros": ["Permanent coverage", "Cash value accumulation", "Guaranteed premiums"],
                "cons": ["Higher premiums", "Lower cash value initially"],
                "suitable_for": "Estate planning, permanent needs, cash value seekers"
            })
        
        # Universal Life recommendations
        if "flexibility" in goals or "premium_flexibility" in goals:
            recommendations.append({
                "type": "Universal Life",
                "rationale": "Flexible premiums and death benefit",
                "pros": ["Premium flexibility", "Adjustable death benefit", "Cash value"],
                "cons": ["Complex structure", "Requires monitoring"],
                "suitable_for": "Clients wanting flexibility, sophisticated planning"
            })
        
        # Indexed Universal Life recommendations
        if "growth" in goals and risk_tolerance in ["moderate", "aggressive"]:
            recommendations.append({
                "type": "Indexed Universal Life",
                "rationale": "Cash value growth with market participation",
                "pros": ["Market-linked growth", "Downside protection", "Cash value"],
                "cons": ["Complex structure", "Caps on growth"],
                "suitable_for": "Growth-oriented clients, market participation seekers"
            })
        
        # Default to Term if no specific recommendations
        if not recommendations:
            recommendations.append({
                "type": "Term Life",
                "rationale": "Standard recommendation for most clients",
                "pros": ["Cost-effective", "Simple", "Adequate coverage"],
                "cons": ["Temporary", "No cash value"],
                "suitable_for": "Most clients starting with life insurance"
            })
        
        return {
            "recommendations": recommendations,
            "primary_recommendation": recommendations[0],
            "considerations": f"Based on age {age}, income ${income:,.0f}, budget ${budget}/month, and goals: {goals}"
        }
    
    def get_calculator_feedback(self, calculation_result: Dict[str, Any]) -> str:
        """
        Generate user-friendly feedback about the calculation process.
        
        Args:
            calculation_result: Result from calculation methods
            
        Returns:
            Feedback message for the user
        """
        if "recommended_range" in calculation_result:
            recommended = calculation_result["recommended_range"]["recommended"]
            return f"I've calculated your life insurance needs using multiple methods. The recommended coverage amount is approximately ${recommended:,.0f}. This analysis considers your income, debts, family situation, and financial goals."
        else:
            return "I've analyzed your life insurance needs and provided recommendations based on your specific circumstances." 
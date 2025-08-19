import logging
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .schemas import CalculatorSelection, CalculatorType, ConversationContext, KnowledgeLevel
from .config import config

logger = logging.getLogger(__name__)

class SemanticCalculatorSelector:
    """Uses semantic understanding to select the right calculator"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def select_calculator_semantically(self, query: str, context: ConversationContext) -> CalculatorSelection:
        """Understand user's semantic intent to select appropriate calculator"""
        
        try:
            prompt = self._build_calculator_selection_prompt(query, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            selection_data = self._parse_calculator_selection(response.choices[0].message.content)
            
            # Validate the selection
            validated_selection = self._validate_calculator_selection(selection_data, context)
            
            logger.info(f"Calculator selection: {validated_selection.selected_calculator} with confidence {validated_selection.confidence}")
            
            return validated_selection
            
        except Exception as e:
            logger.error(f"Error in calculator selection: {e}")
            return self._get_fallback_calculator_selection(query, context)
    
    def _build_calculator_selection_prompt(self, query: str, context: ConversationContext) -> str:
        """Build comprehensive prompt for calculator selection"""
        
        return f"""
        Analyze this request semantically to determine which calculator best serves the user's needs:
        
        **User Request:** "{query}"
        
        **Conversation Context:**
        - User's knowledge level: {context.knowledge_level.value}
        - Previous questions: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        - Expressed goals: {', '.join(context.user_goals) if context.user_goals else 'None'}
        - Current focus area: {context.current_topic or 'General'}
        
        **Calculator Options:**
        1. **Quick Calculator**: 5 basic questions, immediate estimate
           - Best for: Quick estimates, basic planning, initial discussions
           - Questions: Age, income, dependents, debt, mortgage
           - Output: Basic coverage recommendation
           - Time: 2-3 minutes
        
        2. **New Client Detailed Calculator**: 50+ comprehensive questions
           - Best for: Thorough analysis, client assessments, detailed planning
           - Questions: Demographics, goals, education, special needs, legacy planning
           - Output: Comprehensive report with multiple scenarios
           - Time: 15-20 minutes
        
        3. **Portfolio Analysis Calculator**: Portfolio-focused insurance analysis
           - Best for: Investment-focused clients, portfolio integration, holistic planning
           - Questions: Asset allocation, risk profile, investment goals, insurance integration
           - Output: Portfolio analysis with insurance recommendations
           - Time: 10-15 minutes
        
        **Semantic Analysis Required:**
        - What is the user's underlying goal?
        - What level of detail do they actually need?
        - Are they looking for speed or comprehensiveness?
        - Do they want to understand insurance in portfolio context?
        - What is their current situation (new client, existing client, portfolio review)?
        
        **Selection Criteria:**
        - **Quick Calculator**: "I need a fast estimate" | "Just give me a ballpark" | "Quick calculation" | "Basic planning" | "Initial discussion"
        - **Detailed Calculator**: "Comprehensive analysis" | "Client assessment" | "Detailed planning" | "All factors" | "Thorough review" | "Complete analysis"
        - **Portfolio Calculator**: "Portfolio integration" | "Investment context" | "Asset allocation" | "Financial picture" | "Holistic planning" | "Portfolio review"
        
        **Knowledge Level Considerations:**
        - Beginner: Likely needs Quick Calculator or Detailed Calculator with guidance
        - Intermediate: May prefer Detailed Calculator for comprehensive planning
        - Expert: Could use any calculator based on specific needs
        
        **Response Format:**
        Return ONLY a valid JSON object with this exact structure:
        {{
            "selected_calculator": "quick|detailed|portfolio",
            "confidence": 0.95,
            "semantic_reasoning": "detailed explanation of why this calculator matches their intent",
            "clarification_questions": ["question1", "question2", "question3"],
            "expected_outcome": "what they'll get from this calculator",
            "time_estimate": "estimated time to complete",
            "complexity_level": "simple|moderate|complex"
        }}
        
        **Important:**
        - Focus on semantic meaning, not surface-level words
        - Consider the user's knowledge level and goals
        - Provide specific reasoning for your selection
        - Include relevant clarification questions
        - Be precise about expected outcomes
        """
    
    def _parse_calculator_selection(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into calculator selection data"""
        
        try:
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            selection_data = json.loads(response)
            
            # Validate required fields
            required_fields = ["selected_calculator", "confidence", "semantic_reasoning", "expected_outcome"]
            for field in required_fields:
                if field not in selection_data:
                    raise ValueError(f"Missing required field: {field}")
            
            return selection_data
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing calculator selection: {e}")
            logger.error(f"Raw response: {response}")
            raise
    
    def _validate_calculator_selection(self, selection_data: Dict[str, Any], context: ConversationContext) -> CalculatorSelection:
        """Validate and enhance calculator selection data"""
        
        # Validate calculator type
        calculator_type = CalculatorType(selection_data["selected_calculator"])
        
        # Validate confidence score
        confidence = float(selection_data["confidence"])
        if confidence < 0.0 or confidence > 1.0:
            confidence = max(0.0, min(1.0, confidence))
            logger.warning(f"Confidence score adjusted to valid range: {confidence}")
        
        # Get clarification questions
        clarification_questions = selection_data.get("clarification_questions", [])
        if not clarification_questions:
            clarification_questions = self._generate_default_clarification_questions(calculator_type, context)
        
        # Get expected outcome
        expected_outcome = selection_data.get("expected_outcome", "")
        if not expected_outcome:
            expected_outcome = self._get_default_expected_outcome(calculator_type)
        
        return CalculatorSelection(
            selected_calculator=calculator_type,
            confidence=confidence,
            semantic_reasoning=selection_data["semantic_reasoning"],
            clarification_questions=clarification_questions,
            expected_outcome=expected_outcome
        )
    
    def _generate_default_clarification_questions(self, calculator_type: CalculatorType, context: ConversationContext) -> List[str]:
        """Generate default clarification questions based on calculator type and context"""
        
        if calculator_type == CalculatorType.QUICK:
            return [
                "What is your age?",
                "What is your annual income?",
                "How many dependents do you have?",
                "What is your current debt (mortgage, loans, etc.)?",
                "What are your primary financial goals?"
            ]
        
        elif calculator_type == CalculatorType.DETAILED:
            return [
                "Are you looking for a comprehensive financial assessment?",
                "Do you have specific life insurance needs or goals?",
                "Are you planning for retirement, legacy, or business protection?",
                "Do you have any special circumstances or health considerations?",
                "What is your timeline for implementing life insurance?"
            ]
        
        elif calculator_type == CalculatorType.PORTFOLIO:
            return [
                "Do you have an existing investment portfolio?",
                "Are you looking to integrate insurance with your investments?",
                "What is your current asset allocation?",
                "Are you focused on retirement planning or wealth building?",
                "Do you have specific risk management goals?"
            ]
        
        return ["Could you provide more details about your specific needs?"]
    
    def _get_default_expected_outcome(self, calculator_type: CalculatorType) -> str:
        """Get default expected outcome description"""
        
        if calculator_type == CalculatorType.QUICK:
            return "Immediate insurance needs estimate with basic coverage recommendations"
        
        elif calculator_type == CalculatorType.DETAILED:
            return "Comprehensive insurance needs analysis with detailed planning recommendations"
        
        elif calculator_type == CalculatorType.PORTFOLIO:
            return "Portfolio-integrated insurance analysis with holistic financial planning insights"
        
        return "Insurance needs assessment and recommendations"
    
    def _get_fallback_calculator_selection(self, query: str, context: ConversationContext) -> CalculatorSelection:
        """Get fallback calculator selection when main selection fails"""
        
        # Simple fallback logic based on keywords
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["quick", "fast", "estimate", "basic", "simple"]):
            calculator_type = CalculatorType.QUICK
            reasoning = "Fallback to quick calculator based on speed-related keywords"
        elif any(word in query_lower for word in ["portfolio", "investment", "asset", "allocation"]):
            calculator_type = CalculatorType.PORTFOLIO
            reasoning = "Fallback to portfolio calculator based on investment-related keywords"
        else:
            calculator_type = CalculatorType.DETAILED
            reasoning = "Fallback to detailed calculator for comprehensive analysis"
        
        return CalculatorSelection(
            selected_calculator=calculator_type,
            confidence=0.6,
            semantic_reasoning=reasoning,
            clarification_questions=self._generate_default_clarification_questions(calculator_type, context),
            expected_outcome=self._get_default_expected_outcome(calculator_type)
        )
    
    async def confirm_calculator_selection(self, selection: CalculatorSelection, context: ConversationContext) -> str:
        """Generate confirmation message with semantic understanding"""
        
        if selection.confidence < 0.8:
            # Ask for clarification
            return f"""
            I want to make sure I understand your needs correctly. Based on what you've told me, I think you want the **{selection.selected_calculator.value.replace('_', ' ').title()} Calculator**.
            
            **Why I think this fits:**
            {selection.semantic_reasoning}
            
            **What you'll get:**
            {selection.expected_outcome}
            
            **Is this what you're looking for, or would you prefer:**
            • **Quick Calculator**: 5 questions, immediate estimate (2-3 minutes)
            • **Detailed Calculator**: Comprehensive analysis with 50+ questions (15-20 minutes)  
            • **Portfolio Calculator**: Portfolio-focused insurance analysis (10-15 minutes)
            
            Which would you like to use?
            """
        else:
            # High confidence - proceed with confirmation
            return f"""
            Perfect! I understand you want {selection.semantic_reasoning.lower()}.
            
            I'll use the **{selection.selected_calculator.value.replace('_', ' ').title()} Calculator** for you.
            
            **What you'll get:**
            {selection.expected_outcome}
            
            {self._get_calculator_introduction(selection.selected_calculator)}
            """
    
    def _get_calculator_introduction(self, calculator_type: CalculatorType) -> str:
        """Get introduction text for the selected calculator"""
        
        if calculator_type == CalculatorType.QUICK:
            return """
            **Quick Calculator Process:**
            I'll ask you 5 key questions to provide an immediate insurance needs estimate. This will give you a solid foundation for planning.
            """
        
        elif calculator_type == CalculatorType.DETAILED:
            return """
            **Detailed Calculator Process:**
            I'll guide you through a comprehensive assessment with detailed questions about your situation, goals, and needs. This will provide a thorough analysis for complete financial planning.
            """
        
        elif calculator_type == CalculatorType.PORTFOLIO:
            return """
            **Portfolio Calculator Process:**
            I'll analyze your insurance needs in the context of your overall financial portfolio, helping you understand how life insurance integrates with your investment strategy.
            """
        
        return "Let's get started with your assessment." 
import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from .schemas import IntentResult, IntentCategory, CalculatorType, ConversationContext, KnowledgeLevel
from .config import config

logger = logging.getLogger(__name__)

class ConversationContextAnalyzer:
    """Analyzes conversation history to extract semantic context"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(api_key=config.openai_api_key)
    
    async def extract_semantic_context(self, chat_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract semantic meaning from conversation history using LLM"""
        
        if not chat_history:
            return self._get_default_context()
        
        try:
            # Analyze last 10 messages for context using LLM
            recent_messages = chat_history[-10:]
            
            prompt = self._build_context_analysis_prompt(recent_messages)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse LLM response for semantic context
            context_data = self._parse_context_response(response.choices[0].message.content)
            return context_data
            
        except Exception as e:
            logger.error(f"Error in semantic context analysis: {e}")
            return self._get_default_context()
    
    def _build_context_analysis_prompt(self, messages: List[Dict[str, Any]]) -> str:
        """Build prompt for LLM-based context analysis"""
        
        message_texts = []
        for msg in messages:
            if msg.get("type") == "user":
                message_texts.append(f"User: {msg.get('content', '')}")
            else:
                message_texts.append(f"Assistant: {msg.get('content', '')}")
        
        conversation_text = "\n".join(message_texts)
        
        return f"""
        Analyze this conversation to extract semantic context and user characteristics:
        
        **Conversation:**
        {conversation_text}
        
        **Extract the following semantic information:**
        1. **User Goals**: What financial goals or objectives is the user expressing?
        2. **Knowledge Level**: beginner, intermediate, or expert based on language and questions
        3. **Semantic Themes**: What topics and concepts are being discussed?
        4. **Current Focus**: What is the user currently most interested in?
        5. **Client Context**: Are they asking for themselves or for client assessment?
        6. **Previous Calculations**: Any mentions of calculations or assessments?
        7. **Expressed Preferences**: Any specific preferences or requirements mentioned?
        
        **Return JSON format:**
        {{
            "user_goals": ["goal1", "goal2"],
            "knowledge_level": "beginner|intermediate|expert",
            "semantic_themes": ["theme1", "theme2"],
            "current_topic": "main topic of interest",
            "client_context": "personal|client_assessment|both",
            "previous_calculations": ["calc1", "calc2"],
            "expressed_preferences": ["pref1", "pref2"]
        }}
        
        **Analysis Guidelines:**
        - Focus on semantic meaning, not just keywords
        - Consider context and implied goals
        - Assess knowledge level from question complexity and terminology
        - Identify underlying financial planning needs
        """
    
    def _parse_context_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response for context data"""
        
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                context_data = json.loads(json_str)
                
                # Validate and set defaults
                return {
                    "user_goals": context_data.get("user_goals", []),
                    "knowledge_level": KnowledgeLevel(context_data.get("knowledge_level", "beginner")),
                    "semantic_themes": context_data.get("semantic_themes", []),
                    "current_topic": context_data.get("current_topic", "general"),
                    "client_context": context_data.get("client_context", "personal"),
                    "previous_calculations": context_data.get("previous_calculations", []),
                    "expressed_preferences": context_data.get("expressed_preferences", [])
                }
            
        except Exception as e:
            logger.error(f"Error parsing context response: {e}")
        
        # Fallback to default context
        return self._get_default_context()
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Get default context when analysis fails"""
        
        return {
            "user_goals": [],
            "knowledge_level": KnowledgeLevel.BEGINNER,
            "client_context": "personal",
            "previous_calculations": [],
            "expressed_preferences": [],
            "semantic_themes": [],
            "current_topic": "general"
        }

class SemanticIntentClassifier:
    """Uses pure LLM-based semantic understanding for intent classification"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        self.context_analyzer = ConversationContextAnalyzer()
    
    async def classify_intent_semantically(self, query: str, context: ConversationContext) -> IntentResult:
        """Classify intent using pure semantic understanding"""
        
        try:
            # Build comprehensive semantic analysis prompt
            prompt = self._build_semantic_intent_prompt(query, context)
            
            # Get LLM response
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse semantic intent result
            intent_result = self._parse_semantic_intent(response.choices[0].message.content, query, context)
            
            logger.info(f"Semantic intent classification: {intent_result.intent.value}, confidence: {intent_result.confidence}")
            return intent_result
            
        except Exception as e:
            logger.error(f"Error in semantic intent classification: {e}")
            return self._get_fallback_intent(query, context)
    
    def _build_semantic_intent_prompt(self, query: str, context: ConversationContext) -> str:
        """Build comprehensive prompt for semantic intent analysis"""
        
        return f"""
        You are an expert financial advisor assistant. Analyze this query to understand the user's semantic intent and underlying needs.
        
        **User Query:** "{query}"
        
        **Conversation Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        - Current Focus: {context.current_topic or 'General'}
        - Expressed Goals: {', '.join(context.user_goals) if context.user_goals else 'None'}
        - Client Context: {context.client_context or 'Personal'}
        - Calculator State: {context.calculator_state or 'None'}
        - Calculator Type: {context.calculator_type or 'None'}
        
        **Semantic Analysis Required:**
        1. **What is the user REALLY asking for?** (not just surface-level words)
        2. **What is their underlying goal or need?**
        3. **What type of analysis would best serve their intent?**
        4. **Are they looking for education, calculation, analysis, or guidance?**
        5. **What is their semantic intent category?**
        6. **Do they need a calculator, and if so, which type?**
        
        **Intent Categories:**
        1. life_insurance_education - Learning about concepts, products, strategies
        2. insurance_needs_calculation - Wanting to determine coverage amounts
        3. portfolio_integration_analysis - Understanding insurance in financial context
        4. client_assessment_support - Helping assess client situations
        5. product_comparison - Comparing different insurance options
        6. scenario_analysis - "What if" questions and planning
        7. general_financial_advice - General financial planning questions
        8. calculator_selection_choice - User needs calculation but calculator type unclear
        9. calculator_choice_selected - User has chosen calculator type
        
        **Calculator Type Detection (ONLY if calculation is needed):**
        - quick_calculation: Simple, fast estimate needed
        - detailed_assessment: Comprehensive analysis required
        - portfolio_analysis: Portfolio-focused insurance analysis
        - none: No calculation needed (use for education, general advice, etc.)

        **NEW: Calculator Selection Logic:**
        - If user asks about calculation/coverage but doesn't specify calculator type:
          * Set intent to "calculator_selection_choice"
          * Set calculator_type to "none" (user needs to choose)
          * Add follow_up_clarification: ["Which type of calculation would you prefer?"]
        
        **Calculator Selection Intent:**
        - calculator_selection_choice: User needs calculation but calculator type unclear
        - Requires followup to determine: quick, detailed, or portfolio calculator
        
        **IMPORTANT:** Only set calculator_type if the user is explicitly asking for a calculation or needs assessment. For general questions, education, or information requests, set calculator_type to "none".
        
        **Response Format (JSON):**
        {{
            "intent": "intent_category",
            "semantic_goal": "what they really want in detail",
            "calculator_type": "quick|detailed|portfolio|none",
            "confidence": 0.95,
            "reasoning": "detailed explanation of why this classification",
            "follow_up_clarification": "questions to confirm understanding if needed",
            "user_knowledge_assessment": "beginner|intermediate|expert",
            "priority_level": "high|medium|low",
            "needs_external_search": true|false,
            "needs_calculator_selection": true|false,
            "suggested_calculator": "quick|detailed|portfolio|none"
        }}

        **CRITICAL RULES:**
        - For education queries (life_insurance_education, product_comparison), set calculator_type to "none"
        - For general advice queries, set calculator_type to "none" 
        - **AGGRESSIVELY detect calculator needs** when users ask about:
          * "how much coverage do I need"
          * "calculate my insurance needs" 
          * "what amount of life insurance"
          * "coverage calculation"
          * "needs assessment"
          * "insurance calculator"
          * "start calculation"
        - **When in doubt about calculation intent, prefer calculator detection over "none"**
        - **Calculator queries should be classified as insurance_needs_calculation intent**
        - **MANDATORY: If intent is "insurance_needs_calculation", calculator_type MUST be "quick" (not "none")**
        - **MANDATORY: If intent is "portfolio_integration_analysis", calculator_type MUST be "portfolio" (not "none")**
        - **MANDATORY: If intent is "client_assessment_support", calculator_type MUST be "detailed" (not "none")**
        - **NEW: If intent is "calculator_selection_choice", set needs_calculator_selection to true**
        
        **EXTERNAL SEARCH DECISION LOGIC:**
        - **Set needs_external_search to TRUE only when the query requires current, real-time information that our knowledge base might not have:**
          * Current rates, pricing, or market conditions (e.g., "current term life rates", "today's market rates")
          * Recent company-specific information (e.g., "Progressive's latest offerings", "Allstate's new products")
          * Time-sensitive regulatory changes (e.g., "recent tax law changes", "new compliance requirements")
          * Breaking industry news or events (e.g., "latest insurance industry developments")
        - **Set needs_external_search to FALSE for:**
          * General educational questions (e.g., "what is whole life insurance", "how does term insurance work")
          * Product comparisons and explanations (e.g., "term vs whole life", "IUL benefits")
          * Calculation requests (e.g., "calculate my needs", "how much coverage")
          * Portfolio analysis and planning (e.g., "how does insurance fit my portfolio")
        - **Be CONSERVATIVE - only use external search when absolutely necessary for current information**
        
        **Analysis Guidelines:**
        - Focus on understanding what the user really wants
        - Consider their knowledge level and previous conversation
        - Think about whether they need help calculating or just learning
        - Assess how complex their request is
        - Consider where they are in their financial planning journey
        - **CRITICAL: External search should be rare and only for truly current/real-time needs**
        - **NEW: Consider calculator state when determining intent**
        """
    
    def _parse_semantic_intent(self, response: str, original_query: str, context: ConversationContext) -> IntentResult:
        """Parse LLM response for semantic intent"""
        
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response[start_idx:end_idx]
                intent_data = json.loads(json_str)
                
                # Map intent category
                intent_category = self._map_intent_category(intent_data.get("intent", ""))
                
                # Map calculator type
                calculator_type = self._map_calculator_type(intent_data.get("calculator_type", ""))
                
                # Handle follow_up_clarification - ensure it's a list
                follow_up = intent_data.get("follow_up_clarification", [])
                if isinstance(follow_up, str):
                    follow_up = [follow_up] if follow_up else []
                elif not isinstance(follow_up, list):
                    follow_up = []
                
                # Handle needs_external_search - ensure it's a boolean
                needs_external_search = intent_data.get("needs_external_search", False)
                if isinstance(needs_external_search, str):
                    needs_external_search = needs_external_search.lower() == "true"
                
                # Handle needs_calculator_selection - ensure it's a boolean
                needs_calculator_selection = intent_data.get("needs_calculator_selection", False)
                if isinstance(needs_calculator_selection, str):
                    needs_calculator_selection = needs_calculator_selection.lower() == "true"
                
                # Handle suggested_calculator - ensure it's a string
                suggested_calculator = intent_data.get("suggested_calculator", "none")
                if isinstance(suggested_calculator, str):
                    suggested_calculator = suggested_calculator.lower()
                
                return IntentResult(
                    intent=intent_category,
                    semantic_goal=intent_data.get("semantic_goal", original_query),
                    calculator_type=calculator_type,
                    confidence=float(intent_data.get("confidence", 0.8)),
                    reasoning=intent_data.get("reasoning", "Semantic analysis completed"),
                    follow_up_clarification=follow_up,
                    needs_external_search=needs_external_search,
                    needs_calculator_selection=needs_calculator_selection,
                    suggested_calculator=suggested_calculator
                )
            
        except Exception as e:
            logger.error(f"Error parsing semantic intent: {e}")
        
        # Fallback to basic intent
        return self._get_fallback_intent(original_query, context)
    
    def _map_intent_category(self, intent_str: str) -> IntentCategory:
        """Map string intent to IntentCategory enum"""
        
        intent_mapping = {
            "life_insurance_education": IntentCategory.LIFE_INSURANCE_EDUCATION,
            "insurance_needs_calculation": IntentCategory.INSURANCE_NEEDS_CALCULATION,
            "portfolio_integration_analysis": IntentCategory.PORTFOLIO_INTEGRATION_ANALYSIS,
            "client_assessment_support": IntentCategory.CLIENT_ASSESSMENT_SUPPORT,
            "product_comparison": IntentCategory.PRODUCT_COMPARISON,
            "scenario_analysis": IntentCategory.SCENARIO_ANALYSIS,
            "general_financial_advice": IntentCategory.GENERAL_FINANCIAL_ADVICE,
            "calculator_selection_choice": IntentCategory.CALCULATOR_SELECTION_CHOICE,
            "calculator_choice_selected": IntentCategory.CALCULATOR_CHOICE_SELECTED
        }
        
        return intent_mapping.get(intent_str, IntentCategory.GENERAL_FINANCIAL_ADVICE)
    
    def _map_calculator_type(self, calc_str: str) -> CalculatorType:
        """Map string calculator type to CalculatorType enum"""
        
        calc_mapping = {
            "quick": CalculatorType.QUICK,
            "detailed": CalculatorType.DETAILED,
            "portfolio": CalculatorType.PORTFOLIO,
            "none": CalculatorType.NONE
        }
        
        return calc_mapping.get(calc_str, CalculatorType.NONE)
    
    def _get_fallback_intent(self, query: str, context: ConversationContext) -> IntentResult:
        """Get fallback intent when semantic analysis fails"""
        
        # Basic fallback logic
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["calculate", "how much", "coverage", "needs", "amount", "calculator", "assessment", "start"]):
            return IntentResult(
                intent=IntentCategory.INSURANCE_NEEDS_CALCULATION,
                semantic_goal="Calculate insurance coverage needs",
                calculator_type=CalculatorType.QUICK,
                confidence=0.8,
                reasoning="Fallback to calculation intent based on calculator keywords",
                follow_up_clarification=[],
                user_knowledge_assessment="beginner",
                priority_level="medium"
            )
        
        elif any(word in query_lower for word in ["explain", "what is", "difference", "compare"]):
            return IntentResult(
                intent=IntentCategory.LIFE_INSURANCE_EDUCATION,
                semantic_goal="Learn about life insurance concepts",
                calculator_type=CalculatorType.NONE,
                confidence=0.6,
                reasoning="Fallback to education intent based on keywords",
                follow_up_clarification=[],
                user_knowledge_assessment="beginner",
                priority_level="medium"
            )
        
        else:
            return IntentResult(
                intent=IntentCategory.GENERAL_FINANCIAL_ADVICE,
                semantic_goal="Get general financial advice",
                calculator_type=CalculatorType.NONE,
                confidence=0.5,
                reasoning="Fallback to general advice intent",
                follow_up_clarification=[],
                user_knowledge_assessment="beginner",
                priority_level="low"
            ) 
import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from .schemas import IntentResult, IntentCategory, CalculatorType, ConversationContext, KnowledgeLevel, FollowUpResult
from .follow_up_detector import FollowUpDetector
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
            "current_topic": "general"
        }

class SemanticIntentClassifier:
    """Uses pure LLM-based semantic understanding for intent classification with follow-up detection"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        self.context_analyzer = ConversationContextAnalyzer()
        self.follow_up_detector = FollowUpDetector(self.llm)
        
        # Structured mapping from referenced_item to intent categories
        self.referenced_item_to_intent_mapping = {
            # Quick calculator follow-ups
            "calculation": IntentCategory.QUICK_CALCULATOR_FOLLOW_UP,
            "quick_calculator": IntentCategory.QUICK_CALCULATOR_FOLLOW_UP,
            "quick_calculation": IntentCategory.QUICK_CALCULATOR_FOLLOW_UP,
            
            # Report follow-ups (portfolio, new client assessment)
            "portfolio_report": IntentCategory.REPORT_QUESTION,
            "analysis": IntentCategory.REPORT_QUESTION,
            "report": IntentCategory.REPORT_QUESTION,
            "pdf": IntentCategory.REPORT_QUESTION,
            "document": IntentCategory.REPORT_QUESTION,
            "coverage_analysis": IntentCategory.QUICK_CALCULATOR_FOLLOW_UP,  # Calculator results follow-ups
            
            # Education follow-ups
            "education": IntentCategory.LIFE_INSURANCE_EDUCATION,
            "concept": IntentCategory.LIFE_INSURANCE_EDUCATION,
            "product": IntentCategory.LIFE_INSURANCE_EDUCATION,
            "feature": IntentCategory.LIFE_INSURANCE_EDUCATION,
            "general_discussion": IntentCategory.LIFE_INSURANCE_EDUCATION,  # Educational follow-ups
            
            # Conversation management follow-ups
            "conversation": IntentCategory.CONVERSATION_MANAGEMENT,
            "discussion": IntentCategory.CONVERSATION_MANAGEMENT,
            "chat": IntentCategory.CONVERSATION_MANAGEMENT,
            
            # File analysis follow-ups
            "file": IntentCategory.FILE_ANALYSIS,
            "upload": IntentCategory.FILE_ANALYSIS,
            "document_analysis": IntentCategory.FILE_ANALYSIS,
            
            # Calculator selection follow-ups
            "calculator_selection": IntentCategory.CALCULATOR_SELECTION_CHOICE,
            "calculator_choice": IntentCategory.CALCULATOR_CHOICE_SELECTED,
        }
    
    async def classify_intent_semantically(self, query: str, context: ConversationContext) -> IntentResult:
        """Classify intent using pure semantic understanding with follow-up detection"""
        
        try:
            logger.info(f"🔍 INTENT CLASSIFIER: Starting semantic classification for query: '{query[:100]}...'")
            
            # STEP 1: Check for follow-up questions first
            follow_up_result = None
            if hasattr(context, 'simple_history') and context.simple_history:
                conversation_history = context.simple_history.get_conversation_turns()
                follow_up_result = await self.follow_up_detector.detect_follow_up(query, conversation_history)
                
                # Store follow-up result in context
                context.follow_up_result = follow_up_result
                context.suggested_context_window = follow_up_result.suggested_context_window
                context.last_follow_up_topics = follow_up_result.related_topics
                
                logger.info(f"🔍 INTENT CLASSIFIER: Follow-up detection result: {follow_up_result.is_follow_up} (confidence: {follow_up_result.confidence})")
                
                # If this is a follow-up question, enhance the classification
                if follow_up_result.is_follow_up:
                    logger.info(f"🔍 INTENT CLASSIFIER: Detected follow-up question with topics: {follow_up_result.related_topics}")
                    return await self._classify_follow_up_intent(query, context, follow_up_result)
            
            # STEP 2: Normal intent classification
            # Build comprehensive semantic analysis prompt
            prompt = self._build_semantic_intent_prompt(query, context)
            
            # Get LLM response
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            logger.info(f"🔍 INTENT CLASSIFIER: Raw LLM response: '{response.choices[0].message.content[:200]}...'")
            
            # Parse semantic intent result
            intent_result = self._parse_semantic_intent(response.choices[0].message.content, query, context)
            
            # Add follow-up metadata if available
            if follow_up_result:
                intent_result.metadata = intent_result.metadata or {}
                intent_result.metadata.update({
                    "follow_up_detected": follow_up_result.is_follow_up,
                    "follow_up_topics": follow_up_result.related_topics,
                    "context_relevance": follow_up_result.context_relevance
                })
            
            logger.info(f"🔍 INTENT CLASSIFIER: Final classification: {intent_result.intent.value} with confidence {intent_result.confidence}")
            logger.info(f"🔍 INTENT CLASSIFIER: Reasoning: {intent_result.reasoning}")
            logger.info(f"🔍 INTENT CLASSIFIER: Semantic goal: {intent_result.semantic_goal}")
            
            return intent_result
            
        except Exception as e:
            logger.error(f"🔍 INTENT CLASSIFIER: Error in semantic intent classification: {e}")
            import traceback
            logger.error(f"🔍 INTENT CLASSIFIER: Full traceback: {traceback.format_exc()}")
            return self._get_fallback_intent(query, context)
    
    async def _classify_follow_up_intent(self, query: str, context: ConversationContext, follow_up_result: FollowUpResult) -> IntentResult:
        """Classify intent for follow-up questions with enhanced context awareness"""
        
        try:
            logger.info(f"🔍 INTENT CLASSIFIER: Classifying follow-up question with topics: {follow_up_result.related_topics}")
            logger.info(f"🔍 INTENT CLASSIFIER: Referenced item: {follow_up_result.referenced_item}")
            
            # STEP 1: Try structured classification based on referenced_item
            structured_result = self._classify_follow_up_structured(query, context, follow_up_result)
            if structured_result:
                logger.info(f"🔍 INTENT CLASSIFIER: Structured classification successful: {structured_result.intent.value}")
                return structured_result
            
            # STEP 2: Fallback to LLM-based classification for ambiguous cases
            logger.info(f"🔍 INTENT CLASSIFIER: Using LLM fallback for ambiguous follow-up")
            return await self._classify_follow_up_with_llm(query, context, follow_up_result)
            
        except Exception as e:
            logger.error(f"🔍 INTENT CLASSIFIER: Error in follow-up intent classification: {e}")
            # Fallback to normal classification
            return await self._classify_intent_semantically(query, context)
    
    def _classify_follow_up_structured(self, query: str, context: ConversationContext, follow_up_result: FollowUpResult) -> Optional[IntentResult]:
        """Classify follow-up intent using structured mapping from referenced_item"""
        
        try:
            referenced_item = follow_up_result.referenced_item
            
            # Check if we have a direct mapping for this referenced_item
            if referenced_item in self.referenced_item_to_intent_mapping:
                intent_category = self.referenced_item_to_intent_mapping[referenced_item]
                
                # Create structured intent result
                intent_result = IntentResult(
                    intent=intent_category,
                    semantic_goal=f"Follow-up question about {referenced_item}",
                    calculator_type=CalculatorType.NONE,
                    confidence=0.95,  # High confidence for structured classification
                    reasoning=f"Structured classification based on referenced_item: {referenced_item}",
                    follow_up_clarification=[],
                    user_knowledge_assessment=context.knowledge_level.value,
                    priority_level="high"
                )
                
                # Add follow-up metadata
                intent_result.metadata = {
                    "follow_up_detected": True,
                    "follow_up_topics": follow_up_result.related_topics,
                    "context_relevance": follow_up_result.context_relevance,
                    "suggested_context_window": follow_up_result.suggested_context_window,
                    "referenced_item": follow_up_result.referenced_item,
                    "structured_classification": True
                }
                
                logger.info(f"🔍 INTENT CLASSIFIER: Structured classification: {referenced_item} → {intent_category.value}")
                return intent_result
            
            # Check for partial matches (e.g., "calculation" in "quick_calculation")
            # But be more precise to avoid false matches like "general_discussion" matching "discussion"
            for mapped_item, intent_category in self.referenced_item_to_intent_mapping.items():
                # Only match if one is a proper substring of the other, not just contains
                if (mapped_item in referenced_item and len(mapped_item) > 3) or (referenced_item in mapped_item and len(referenced_item) > 3):
                    intent_result = IntentResult(
                        intent=intent_category,
                        semantic_goal=f"Follow-up question about {referenced_item}",
                        calculator_type=CalculatorType.NONE,
                        confidence=0.90,  # Slightly lower confidence for partial match
                        reasoning=f"Structured classification based on partial match: {referenced_item} matches {mapped_item}",
                        follow_up_clarification=[],
                        user_knowledge_assessment=context.knowledge_level.value,
                        priority_level="high"
                    )
                    
                    # Add follow-up metadata
                    intent_result.metadata = {
                        "follow_up_detected": True,
                        "follow_up_topics": follow_up_result.related_topics,
                        "context_relevance": follow_up_result.context_relevance,
                        "suggested_context_window": follow_up_result.suggested_context_window,
                        "referenced_item": follow_up_result.referenced_item,
                        "structured_classification": True,
                        "partial_match": True
                    }
                    
                    logger.info(f"🔍 INTENT CLASSIFIER: Partial match classification: {referenced_item} → {intent_category.value}")
                    return intent_result
            
            logger.info(f"🔍 INTENT CLASSIFIER: No structured mapping found for referenced_item: {referenced_item}")
            return None
            
        except Exception as e:
            logger.error(f"🔍 INTENT CLASSIFIER: Error in structured follow-up classification: {e}")
            return None
    
    async def _classify_follow_up_with_llm(self, query: str, context: ConversationContext, follow_up_result: FollowUpResult) -> IntentResult:
        """Classify follow-up intent using LLM when structured classification fails"""
        
        try:
            # Build enhanced prompt for follow-up questions
            prompt = self._build_follow_up_intent_prompt(query, context, follow_up_result)
            
            # Get LLM response
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse follow-up intent result
            intent_result = self._parse_semantic_intent(response.choices[0].message.content, query, context)
            
            # Enhance with follow-up metadata
            intent_result.metadata = intent_result.metadata or {}
            intent_result.metadata.update({
                "follow_up_detected": True,
                "follow_up_topics": follow_up_result.related_topics,
                "context_relevance": follow_up_result.context_relevance,
                "suggested_context_window": follow_up_result.suggested_context_window,
                "referenced_item": follow_up_result.referenced_item,
                "llm_classification": True
            })
            
            # Boost confidence for follow-up questions since we have context
            intent_result.confidence = min(intent_result.confidence + 0.1, 1.0)
            
            # Special handling for report questions - boost confidence even more
            if (intent_result.intent == IntentCategory.REPORT_QUESTION and 
                follow_up_result.referenced_item in ["portfolio_report", "analysis"]):
                intent_result.confidence = min(intent_result.confidence + 0.2, 1.0)
                logger.info(f"🔍 INTENT CLASSIFIER: Boosted confidence for report question follow-up: {intent_result.confidence}")
            
            # Special handling for quick calculator follow-ups - boost confidence even more
            if (intent_result.intent == IntentCategory.QUICK_CALCULATOR_FOLLOW_UP and 
                follow_up_result.referenced_item in ["calculation", "quick_calculator", "coverage_analysis"]):
                intent_result.confidence = min(intent_result.confidence + 0.2, 1.0)
                logger.info(f"🔍 INTENT CLASSIFIER: Boosted confidence for quick calculator follow-up: {intent_result.confidence}")
            
            logger.info(f"🔍 INTENT CLASSIFIER: LLM follow-up classification: {intent_result.intent.value} with enhanced confidence {intent_result.confidence}")
            
            return intent_result
            
        except Exception as e:
            logger.error(f"🔍 INTENT CLASSIFIER: Error in LLM follow-up classification: {e}")
            # Fallback to basic intent
            return self._get_fallback_intent(query, context)
    
    def _build_follow_up_intent_prompt(self, query: str, context: ConversationContext, follow_up_result: FollowUpResult) -> str:
        """Build enhanced prompt for follow-up question analysis"""
        
        return f"""
        You are analyzing a FOLLOW-UP QUESTION that relates to previous conversation topics.
        
        **Current Query:** "{query}"
        
        **CRITICAL: Follow-up Analysis (PRIMARY CLASSIFICATION DRIVER):**
        - Is Follow-up: {follow_up_result.is_follow_up}
        - **Referenced Item: {follow_up_result.referenced_item}** ← **USE THIS FOR CLASSIFICATION**
        - Related Topics: {', '.join(follow_up_result.related_topics)}
        - Context Relevance: {follow_up_result.context_relevance}
        - Reasoning: {follow_up_result.reasoning}
        
        **Conversation Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        - Expressed Goals: {', '.join(context.user_goals) if context.user_goals else 'None'}
        
        **PRIMARY CLASSIFICATION RULES (Based on Referenced Item):**
        - If referenced_item = "calculation" or "quick_calculator" → "quick_calculator_follow_up"
        - If referenced_item = "portfolio_report" or "analysis" or "report" → "report_question"
        - If referenced_item = "education" or "concept" or "product" → "life_insurance_education"
        - If referenced_item = "conversation" or "discussion" → "conversation_management"
        - If referenced_item = "file" or "upload" → "file_analysis"
        - If referenced_item = "calculator_selection" → "calculator_selection_choice"
        - If referenced_item = "calculator_choice" → "calculator_choice_selected"
        
        **Enhanced Intent Analysis for Follow-up Questions:**
        Since this is a follow-up question, the user is likely asking for:
        1. **Clarification** about something previously discussed
        2. **More details** about a previous topic or recommendation
        3. **Explanation** of a specific value, calculation, or result
        4. **Deeper understanding** of a concept or product mentioned before
        
        **Intent Categories (prioritize based on referenced_item):**
        1. quick_calculator_follow_up - Follow-up questions about quick calculator results and responses
        2. report_question - Questions about existing reports, PDFs, or analysis results (portfolio/new client assessment)
        3. life_insurance_education - Learning more about concepts previously mentioned
        4. conversation_management - Managing conversation state, asking about what was discussed
        5. file_analysis - Follow-up questions about uploaded files or document analysis
        6. calculator_selection_choice - Follow-up questions about calculator type selection
        7. calculator_choice_selected - Follow-up questions about chosen calculator type
        8. general_financial_advice - General follow-up questions about financial topics
        9. portfolio_integration_analysis - Follow-up questions about portfolio analysis or investment context
        10. insurance_needs_calculation - Follow-up questions about coverage calculations or needs assessment
        11. client_assessment_support - Follow-up questions about client assessment or detailed analysis
        12. product_comparison - Follow-up questions about comparing different insurance options
        13. scenario_analysis - Follow-up questions about "what if" scenarios or planning
        
        **CRITICAL: Calculator Choice Selection Detection:**
        - If user responds with single words like "quick", "detailed", "portfolio" after calculator selection
        - If user says "I want the quick one", "let's do detailed", "portfolio please"
        - Set intent to "calculator_choice_selected" with appropriate calculator_type
        - Set needs_calculator_selection to false
        
        **Response Format (JSON):**
        {{
            "intent": "intent_category",
            "semantic_goal": "what they really want in detail (considering follow-up context)",
            "calculator_type": "none",
            "confidence": 0.95,
            "reasoning": "detailed explanation considering this is a follow-up question",
            "follow_up_clarification": [],
            "user_knowledge_assessment": "beginner|intermediate|expert",
            "priority_level": "high|medium|low",
            "needs_external_search": false,
            "needs_calculator_selection": false,
            "suggested_calculator": "none"
        }}
        
        **CRITICAL RULES for Follow-up Questions (PRIORITIZE REFERENCED_ITEM):**
        - **PRIMARY RULE: Use the referenced_item to determine intent classification**
        - If referenced_item = "calculation" → "quick_calculator_follow_up" (regardless of query text)
        - If referenced_item = "portfolio_report" or "analysis" → "report_question" (regardless of query text)
        - If referenced_item = "education" or "concept" → "life_insurance_education" (regardless of query text)
        - If referenced_item = "conversation" → "conversation_management" (regardless of query text)
        - If referenced_item = "file" → "file_analysis" (regardless of query text)
        
        **Secondary Rules (only if referenced_item is ambiguous):**
        - If asking about a specific report, PDF, or analysis result (portfolio/new client assessment) → "report_question"
        - If asking about quick calculator results, responses, or calculation details → "quick_calculator_follow_up"
        - If asking for more explanation about a concept → "life_insurance_education" 
        - If asking about conversation state → "conversation_management"
        - If asking about portfolio analysis or investment context → "portfolio_integration_analysis"
        - If asking about coverage calculations or needs assessment → "insurance_needs_calculation"
        - If asking about client assessment or detailed analysis → "client_assessment_support"
        - If asking about comparing different insurance options → "product_comparison"
        - If asking about "what if" scenarios or planning → "scenario_analysis"
        - If asking about uploaded files or document analysis → "file_analysis"
        - If asking about calculator type selection → "calculator_selection_choice"
        - If asking about chosen calculator type → "calculator_choice_selected"
        
        **Examples of Referenced Item Classification:**
        - Query: "Can you expand on this?" + referenced_item: "calculation" → "quick_calculator_follow_up"
        - Query: "Tell me more about this" + referenced_item: "portfolio_report" → "report_question"
        - Query: "What does this mean?" + referenced_item: "education" → "life_insurance_education"
        - Query: "What were we discussing?" + referenced_item: "conversation" → "conversation_management"
        
        **CRITICAL: If user responds with single words like "quick", "detailed", "portfolio" after calculator selection → "calculator_choice_selected"**
        **CRITICAL: If user says "I want the quick one", "let's do detailed", "portfolio please" → "calculator_choice_selected"**
        **CRITICAL: Single word "quick" → calculator_choice_selected with calculator_type="quick"**
        **CRITICAL: Single word "detailed" → calculator_choice_selected with calculator_type="detailed"**
        **CRITICAL: Single word "portfolio" → calculator_choice_selected with calculator_type="portfolio"**
        
        **Follow-up Question Guidelines:**
        - Follow-up questions should NOT trigger new calculations (calculator_type: "none")
        - Follow-up questions should use existing context and conversation history
        - High confidence since we have conversation context
        - For vague follow-ups, prioritize the most recent structured data or analysis
        - **MOST IMPORTANT: Use the referenced_item as the primary classification driver**
        """
    
    def _build_semantic_intent_prompt(self, query: str, context: ConversationContext) -> str:
        """Build comprehensive prompt for semantic intent analysis"""
        
        return f"""
        You are an expert financial advisor assistant. Analyze this query to understand the user's semantic intent and underlying needs.
        
        **User Query:** "{query}"
        
        **Conversation Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        - Expressed Goals: {', '.join(context.user_goals) if context.user_goals else 'None'}
        - Client Context: {context.client_context or 'Personal'}
        - Calculator State: {context.calculator_state or 'None'}
        - Calculator Type: {context.calculator_type or 'None'}
        
        **CRITICAL DETECTION RULES (HIGHEST PRIORITY):**
        
        **1. Calculator Choice Selection (MUST CHECK FIRST):**
        - If user responds with single words like "quick", "detailed", "portfolio" after calculator selection
        - If user says "I want the quick one", "let's do detailed", "portfolio please"
        - Set intent to "calculator_choice_selected" with appropriate calculator_type
        - Set needs_calculator_selection to false
        
        **EXAMPLES of calculator choice selection (calculator_choice_selected):**
        - "quick" → calculator_choice_selected with calculator_type="quick"
        - "detailed" → calculator_choice_selected with calculator_type="detailed"
        - "portfolio" → calculator_choice_selected with calculator_type="portfolio"
        - "I want the quick one" → calculator_choice_selected with calculator_type="quick"
        - "let's do detailed" → calculator_choice_selected with calculator_type="detailed"
        - "portfolio please" → calculator_choice_selected with calculator_type="portfolio"
        
        **CONTEXT AWARENESS FOR CALCULATOR CHOICES:**
        - If Calculator State is "selecting" and user says "quick" → calculator_choice_selected with calculator_type="quick"
        - If Calculator State is "selecting" and user says "detailed" → calculator_choice_selected with calculator_type="detailed"
        - If Calculator State is "selecting" and user says "portfolio" → calculator_choice_selected with calculator_type="portfolio"
        - If previous message was about calculator selection and user says "quick" → calculator_choice_selected with calculator_type="quick"
        - If previous message was about calculator selection and user says "detailed" → calculator_choice_selected with calculator_type="detailed"
        - If previous message was about calculator selection and user says "portfolio" → calculator_choice_selected with calculator_type="portfolio"
        
        **SPECIFIC CALCULATOR TYPE DETECTION:**
        - Single word "quick" → calculator_choice_selected with calculator_type="quick"
        - Single word "detailed" → calculator_choice_selected with calculator_type="detailed"
        - Single word "portfolio" → calculator_choice_selected with calculator_type="portfolio"
        - "I want quick" → calculator_choice_selected with calculator_type="quick"
        - "I want detailed" → calculator_choice_selected with calculator_type="detailed"
        - "I want portfolio" → calculator_choice_selected with calculator_type="portfolio"
        
        **2. Direct Calculator Requests:**
        - "I want to do a quick calculator" → insurance_needs_calculation with calculator_type="quick"
        - "Can you help me get a quick calculation of my life insurance coverage needs?" → insurance_needs_calculation with calculator_type="quick"
        - "I need a quick estimate" → insurance_needs_calculation with calculator_type="quick"
        - "Start a quick calculation" → insurance_needs_calculation with calculator_type="quick"
        - "Do a quick assessment" → insurance_needs_calculation with calculator_type="quick"
        
        **3. Portfolio Analysis Requests:**
        - "portfolio analyzer", "portfolio analysis", "portfolio assessment" → portfolio_integration_analysis with calculator_type="portfolio"
        - "How does life insurance fit into my investment portfolio?" → portfolio_integration_analysis with calculator_type="portfolio"
        - "life insurance in my portfolio", "insurance and investments", "portfolio integration" → portfolio_integration_analysis with calculator_type="portfolio"
        - "analyze my portfolio", "portfolio review", "investment analysis" → portfolio_integration_analysis with calculator_type="portfolio"
        - "life insurance with my investments", "portfolio diversification", "asset allocation" → portfolio_integration_analysis with calculator_type="portfolio"
        
        **4. Generic Follow-up Phrases:**
        - "Can you expand on this" after reports → report_question
        - "Tell me more about this" after reports → report_question
        - "Go deeper into this" after reports → report_question
        
        **Semantic Analysis Required:**
        1. **What is the user REALLY asking for?** (not just surface-level words)
        2. **What is their underlying goal or need?**
        3. **What type of analysis would best serve their intent?**
        4. **Are they looking for education, calculation, analysis, or guidance?**
        5. **What is their semantic intent category?**
        6. **Do they need a calculator, and if so, which type?**
        
        **Portfolio Integration Analysis Semantic Indicators (REVISED):**
        - Queries about life insurance as an **investment vehicle** or **asset class**
        - Questions about **strategic asset allocation** including insurance
        - Requests to analyze insurance **within an existing investment portfolio**
        - Questions about **tax-efficient investment strategies** involving insurance
        - Requests for **comprehensive financial planning** that includes insurance as an investment component
        - Questions about **wealth building strategies** that incorporate insurance products
        - Requests to analyze **retirement income strategies** using insurance products
        
        **Current Market Information Indicators (for life_insurance_education):**
        - Queries asking for **current/real-time data** (rates, pricing, offerings)
        - Questions about **specific companies' current products** or rates
        - Requests for **today's market conditions** or latest information
        - Questions about **what's currently available** in the market
        - Requests for **recent company-specific information** or offerings
        
        **Intent Categories:**
        1. life_insurance_education - Learning about concepts, products, strategies, and current market information
        2. insurance_needs_calculation - Wanting to determine coverage amounts
        3. portfolio_integration_analysis - Understanding insurance as an investment vehicle within financial portfolios
        4. client_assessment_support - Helping assess client situations
        5. product_comparison - Comparing different insurance options
        6. scenario_analysis - "What if" questions and planning
        7. general_financial_advice - General financial planning questions
        8. calculator_selection_choice - User needs calculation but calculator type unclear
        9. calculator_choice_selected - User has chosen calculator type
        10. conversation_management - Managing conversation state, asking about what was discussed
        11. report_question - Questions about existing reports, PDFs, or analysis results (portfolio/new client assessment)
        12. quick_calculator_follow_up - Follow-up questions about quick calculator results and responses
        13. file_analysis - Questions about uploaded files, document analysis, or file content
        
        **Calculator Choice Selection Detection:**
        - If user responds with single words like "quick", "detailed", "portfolio" after calculator selection
        - If user says "I want the quick one", "let's do detailed", "portfolio please"
        - Set intent to "calculator_choice_selected" with appropriate calculator_type
        - Set needs_calculator_selection to false
        
        **Calculator Type Detection (ONLY if calculation is needed):**
        - quick: Simple, fast estimate needed (5 questions, 2-3 minutes)
        - detailed: Comprehensive analysis required (50+ questions, 15-20 minutes) 
        - portfolio: Portfolio-focused insurance analysis (10-15 minutes)
        - none: No calculation needed (use for education, general advice, etc.)

        **Calculator Selection Logic:**
        - If user asks about calculation/coverage but doesn't specify which calculator:
          * Set intent to "calculator_selection_choice"
          * Set calculator_type to "none" (user needs to choose)
          * Set needs_calculator_selection to true
          * Add follow_up_clarification: ["Which type of calculation would you prefer?"]
        
        **EXAMPLES of calculator_selection_choice:**
        - "I want to calculate my insurance needs" → calculator_selection_choice (no specific calculator mentioned)
        - "I need to figure out my coverage" → calculator_selection_choice (no specific calculator mentioned)
        - "How much life insurance do I need?" → calculator_selection_choice (no specific calculator mentioned)
        - "I want to do a quick calculation" → insurance_needs_calculation with calculator_type="quick" (specific calculator mentioned)
        - "I need a detailed assessment" → client_assessment_support with calculator_type="detailed" (specific calculator mentioned)
        
        **EXAMPLES of direct calculator requests (NOT calculator_selection_choice):**
        - "I want to do a quick calculator" → insurance_needs_calculation with calculator_type="quick"
        - "Can you help me get a quick calculation of my life insurance coverage needs?" → insurance_needs_calculation with calculator_type="quick"
        - "I need a quick estimate" → insurance_needs_calculation with calculator_type="quick"
        - "Start a quick calculation" → insurance_needs_calculation with calculator_type="quick"
        - "Do a quick assessment" → insurance_needs_calculation with calculator_type="quick"
        
        **EXAMPLES of calculator choice selection (calculator_choice_selected):**
        - "quick" → calculator_choice_selected with calculator_type="quick"
        - "detailed" → calculator_choice_selected with calculator_type="detailed"
        - "portfolio" → calculator_choice_selected with calculator_type="portfolio"
        - "I want the quick one" → calculator_choice_selected with calculator_type="quick"
        - "let's do detailed" → calculator_choice_selected with calculator_type="detailed"
        - "portfolio please" → calculator_choice_selected with calculator_type="portfolio"
        
        **Specific Calculator Detection:**
        - quick: "quick estimate", "fast calculation", "basic needs", "ballpark figure"
        - detailed: "comprehensive assessment", "detailed analysis", "client assessment", "thorough review"
        - portfolio: "portfolio analysis", "portfolio analyzer", "investment context", "asset allocation", "holistic planning", "portfolio assessment"
        
        **Calculator Selection Intent:**
        - calculator_selection_choice: User needs calculation but calculator type unclear
        - Requires followup to determine: quick, detailed, or portfolio calculator
        
        **Calculator Choice Selection:**
        - calculator_choice_selected: User has chosen a specific calculator type
        - Examples: "quick", "detailed", "portfolio", "I want the quick one", "let's do detailed"
        - Set calculator_type to the chosen type
        - Set needs_calculator_selection to false
        
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

        **CRITICAL RULES (SIMPLIFIED):**
        - **PRIORITY 1: Calculator Choice Selection** - Single words like "quick", "detailed", "portfolio" after calculator selection → calculator_choice_selected
        - **PRIORITY 2: Direct Calculator Requests** - "I want to do a quick calculator" → insurance_needs_calculation with calculator_type="quick"
        - **PRIORITY 3: Current Market Information** - Queries with current/time-sensitive indicators → life_insurance_education with needs_external_search=true
        - **PRIORITY 4: Portfolio Integration** - Queries about insurance as investment vehicle within portfolios → portfolio_integration_analysis with calculator_type="portfolio"
        - **PRIORITY 5: Generic Follow-ups** - "Can you expand on this" after reports → report_question
        - **PRIORITY 6: General Education** - Learning about concepts → life_insurance_education with calculator_type="none"
        - **PRIORITY 7: File Analysis** - "summarize this document", "analyze this file" → file_analysis
        
        **INTENT DISAMBIGUATION RULES:**
        
        **If query contains CURRENT/TIME-SENSITIVE indicators:**
        - "current", "today's", "latest", "now", "recent", "what's available"
        - "what does [company] offer", "what are [company]'s rates"
        - "what's on the market", "what's available now"
        → **ALWAYS classify as life_insurance_education** (regardless of other context)
        
        **If query contains PORTFOLIO/INVESTMENT context indicators:**
        - "portfolio", "asset allocation", "investment strategy"
        - "diversification", "financial planning", "retirement planning"
        - "wealth building", "investment vehicle", "asset class"
        → **Classify as portfolio_integration_analysis** (only if NOT current market info)
        
        **PRIORITY ORDER:**
        1. **Current market information** → life_insurance_education (highest priority)
        2. **Portfolio/investment context** → portfolio_integration_analysis
        3. **General education** → life_insurance_education
        4. **Calculation needs** → appropriate calculator intent
        
        **🎯 Conversation Management vs Follow-up Detection:**
        - **Set intent to "conversation_management" ONLY when users ask about conversation state:**
          * "what did we just talk about" ← **HIGHEST PRIORITY**
          * "what were we discussing"
          * "summarize our conversation"
          * "what have we covered"
          * "what was the main topic"
          * "repeat what you said about X"
          * "how long have we been talking"
          * "what questions have I asked"
          * "can you remind me what we discussed"
          * "what was our conversation about"
        - **These queries should NEVER go to RAG or external search**
        - **They should use the conversation memory system directly**
        
        - **CRITICAL: These are NOT conversation management (they are follow-up questions):**
          * "expand on cash value" → This is life_insurance_education (learning more about a concept)
          * "tell me more about IUL" → This is life_insurance_education (learning more about a product)
          * "go deeper into term life" → This is life_insurance_education (learning more about a topic)
          * "what about the death benefit" → This is life_insurance_education (learning more about a feature)
          * "how does the growth work" → This is life_insurance_education (learning more about mechanics)
          * "can you elaborate on premiums" → This is life_insurance_education (learning more about costs)
          * "explain more about surrender value" → This is life_insurance_education (learning more about features)
        
        - **Rule of thumb:** If the user is asking to learn more about a specific insurance concept, product, or feature, it's NOT conversation management - it's life_insurance_education that should use RAG with context.
        
        **🎯 Intent Classification Examples:**
        
        **life_insurance_education Examples:**
        - "what is term life insurance" → General education about a concept
        - "how does whole life work" → General education about a product
        - "expand on cash value" → Follow-up question about a concept (use RAG with context)
        - "tell me more about IUL" → Follow-up question about a product (use RAG with context)
        - "what about the death benefit" → Follow-up question about a feature (use RAG with context)
        - "go deeper into how premiums work" → Follow-up question about mechanics (use RAG with context)
        - "what are current term life rates?" → Current market information (needs external search)
        - "what does Progressive offer for term life?" → Company-specific current info (needs external search)
        - "what are today's IUL rates?" → Current market pricing (needs external search)
        - "what's the latest on whole life insurance?" → Current market trends (needs external search)
        - "what companies offer the best term life rates?" → Current market comparison (needs external search)
        
        **portfolio_integration_analysis Examples:**
        - "How should I allocate my portfolio between stocks, bonds, and life insurance?" → Strategic asset allocation
        - "Should I include IUL as part of my investment strategy?" → Investment vehicle consideration
        - "How does life insurance fit into my 60/40 portfolio allocation?" → Portfolio integration
        - "What's the role of whole life insurance in my retirement planning?" → Retirement strategy
        - "How can I use life insurance to diversify my investment portfolio?" → Portfolio diversification
        - "Should I consider life insurance as an alternative investment?" → Investment strategy
        - "How does term life affect my portfolio diversification?" → Portfolio impact analysis
        
        **report_question Examples:**
        - "Can you explain to me in that portfolio report what the recommended coverage was?" → Question about existing report
        - "What does the PDF say about my risk level?" → Question about existing PDF
        - "In the analysis, what was my total assets?" → Question about existing analysis
        - "What did the report recommend for my portfolio?" → Question about existing report
        - "Can you tell me more about the coverage amount in the PDF?" → Question about existing PDF
        - "What was the rationale in my portfolio analysis?" → Question about existing analysis
        - "In that report, what was my life insurance need?" → Question about existing report
        
        **quick_calculator_follow_up Examples:**
        - "Can you expand on this" after quick calculator → Follow-up about calculator results
        - "Tell me more about the coverage gap" after quick calculator → Follow-up about calculator results
        - "What does the product recommendation mean?" after quick calculator → Follow-up about calculator results
        - "Explain the cash value projections" after quick calculator → Follow-up about calculator results
        - "Why do I need so much coverage?" after quick calculator → Follow-up about calculator results
        - "What if I can't afford the recommended amount?" after quick calculator → Follow-up about calculator results
        
        **conversation_management Examples:**
        - "what did we just talk about" → Meta-question about conversation state
        - "summarize our conversation" → Meta-question about conversation content
        - "what were we discussing" → Meta-question about conversation focus
        - "how long have we been talking" → Meta-question about conversation duration
        
        **Context Usage Guidelines:**
        - **For follow-up questions** (expand on, tell me more, go deeper): Use the context to enhance RAG responses
        - **For new questions**: Context provides background but doesn't change the core intent
        - **For conversation management**: Context provides conversation history for summaries
        
        **EXTERNAL SEARCH DECISION LOGIC (ENHANCED):**
        - **Set needs_external_search to TRUE for:**
          * **Current market information queries** (life_insurance_education with current indicators)
          * **Company-specific information queries** (life_insurance_education with company names)
          * **Time-sensitive regulatory changes** (any intent with regulatory context)
          * **Breaking industry news** (any intent with news context)
          * **Current rates, pricing, or market conditions** (e.g., "current term life rates", "today's market rates")
          * **Recent company-specific information** (e.g., "Progressive's latest offerings", "Allstate's new products")
          * **What's currently available** (e.g., "what's on the market", "what companies offer")
        - **Set needs_external_search to FALSE for:**
          * **General educational questions** (life_insurance_education without current indicators)
          * **Portfolio integration questions** (portfolio_integration_analysis)
          * **Calculation requests** (all calculator intents)
          * **Product comparisons** (product_comparison)
          * **Scenario analysis** (scenario_analysis)
          * **General financial advice** (general_financial_advice)
        - **PRIORITY: Current market information takes precedence over all other considerations**
        
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
            "calculator_choice_selected": IntentCategory.CALCULATOR_CHOICE_SELECTED,
            "conversation_management": IntentCategory.CONVERSATION_MANAGEMENT,
            "report_question": IntentCategory.REPORT_QUESTION,
            "quick_calculator_follow_up": IntentCategory.QUICK_CALCULATOR_FOLLOW_UP,
            "file_analysis": IntentCategory.FILE_ANALYSIS
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
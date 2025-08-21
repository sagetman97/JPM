import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from .schemas import (
    ChatMessage, ChatResponse, ConversationContext, IntentResult,
    RoutingDecision, RAGResult, SearchResult, QualityScore,
    ComplianceResult, ChatSession, MessageType, RouteType, KnowledgeLevel,
    IntentCategory, CalculatorType
)
from .config import config
from .context_manager import ConversationContextUpdater, ContextPollutionGuard
from .simple_conversation_history import SimpleConversationHistory

logger = logging.getLogger(__name__)

class BaseLLMResponse:
    """Handles base LLM responses for fallback and general knowledge"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
    
    async def generate_safe_response(self, query: str, context: ConversationContext) -> str:
        """Generate safe, educational response using base LLM"""
        
        try:
            prompt = self._build_safe_response_prompt(query, context)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating base LLM response: {e}")
            return self._get_fallback_response(query)
    
    def _build_safe_response_prompt(self, query: str, context: ConversationContext) -> str:
        """Build safe prompt for base LLM"""
        
        return f"""
        You are a knowledgeable financial advisor assistant. Answer this question naturally and helpfully:
        
        **User Question:** "{query}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Focus Area: {context.current_topic or 'General'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Response Guidelines:**
        1. **Natural Conversation**: Write like you're explaining to a friend, not a corporate manual
        2. **Educational Focus**: Provide helpful information about life insurance and financial planning
        3. **Clear and Simple**: Use everyday language that's easy to understand
        4. **Safety First**: Avoid specific financial advice, focus on education and general principles
        5. **Context Aware**: Consider their knowledge level and previous conversation
        6. **Helpful Examples**: Include relevant examples or insights when helpful
        
        **Response Style:**
        - Answer their question directly and naturally
        - Explain concepts in simple, clear terms
        - Use conversational language - avoid corporate jargon
        - Include practical insights or examples when relevant
        - Keep it focused on what they actually asked
        
        **Important:**
        - Focus on being helpful and educational, not formal or robotic
        - Emphasize the importance of working with licensed professionals
        - Provide general information that applies to most situations
        - Encourage further research and professional consultation
        
        Generate a helpful, natural response:
        """
    
    def _get_fallback_response(self, query: str) -> str:
        """Get fallback response when LLM fails"""
        
        return f"""
        I understand you're asking about "{query}" related to life insurance and financial planning.
        
        While I'm experiencing some technical difficulties right now, I can provide some general guidance:
        
        **General Principles:**
        • Life insurance is a key component of comprehensive financial planning
        • Coverage needs vary based on individual circumstances and goals
        • It's important to work with licensed professionals for personalized advice
        • Regular reviews of insurance coverage are essential as life circumstances change
        
        **Next Steps:**
        • Consider scheduling a consultation with a licensed insurance professional
        • Review your current financial situation and protection needs
        • Research different types of life insurance products
        • Evaluate how insurance fits into your overall financial strategy
        
        Would you like to try asking your question again, or would you prefer to explore a different topic?
        """

class QualityEvaluator:
    """Evaluates response quality and provides improvement suggestions"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
    
    async def evaluate_response_quality(self, query: str, response: str, context: ConversationContext) -> QualityScore:
        """Evaluate response quality using semantic understanding"""
        
        try:
            prompt = self._build_quality_evaluation_prompt(query, response, context)
            
            evaluation = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            quality_score = self._parse_quality_evaluation(evaluation.choices[0].message.content)
            return quality_score
            
        except Exception as e:
            logger.error(f"Error evaluating response quality: {e}")
            return QualityScore(
                overall_score=0.7,
                semantic_scores={"relevance": 0.7, "accuracy": 0.7, "completeness": 0.7, "clarity": 0.7},
                improvement_areas=["Quality evaluation unavailable"]
            )
    
    def _build_quality_evaluation_prompt(self, query: str, response: str, context: ConversationContext) -> str:
        """Build prompt for quality evaluation"""
        
        return f"""
        Evaluate the quality of this financial advice response:
        
        **User Question:** "{query}"
        
        **Generated Response:** "{response}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        - Previous Themes: {', '.join(context.semantic_themes) if context.semantic_themes else 'None'}
        
        **Quality Criteria (Rate 0-1 for each):**
        1. **Relevance**: Does the response directly address the question?
        2. **Accuracy**: Is the information correct and reliable?
        3. **Completeness**: Does it cover the full scope of the question?
        4. **Clarity**: Is the response clear and understandable?
        5. **Natural Tone**: Does it sound conversational and helpful, not robotic?
        6. **Appropriate Length**: Is the response length appropriate for the question complexity?
        7. **Context Appropriateness**: Does it match the user's knowledge level?
        
        **Return JSON with scores and improvement areas:**
        {{
            "relevance_score": 0.9,
            "accuracy_score": 0.8,
            "completeness_score": 0.7,
            "clarity_score": 0.9,
            "natural_tone_score": 0.8,
            "appropriate_length_score": 0.9,
            "context_appropriateness_score": 0.9,
            "overall_score": 0.83,
            "improvement_areas": ["Could provide more specific examples", "Consider adding next steps"]
        }}
        """
    
    def _parse_quality_evaluation(self, evaluation: str) -> QualityScore:
        """Parse quality evaluation response"""
        
        try:
            import json
            
            # Try to extract JSON
            start_idx = evaluation.find('{')
            end_idx = evaluation.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = evaluation[start_idx:end_idx]
                eval_data = json.loads(json_str)
                
                return QualityScore(
                    overall_score=float(eval_data.get("overall_score", 0.7)),
                    semantic_scores={
                        "relevance": float(eval_data.get("relevance_score", 0.7)),
                        "accuracy": float(eval_data.get("accuracy_score", 0.7)),
                        "completeness": float(eval_data.get("completeness_score", 0.7)),
                        "clarity": float(eval_data.get("clarity_score", 0.7)),
                        "natural_tone": float(eval_data.get("natural_tone_score", 0.7)),
                        "appropriate_length": float(eval_data.get("appropriate_length_score", 0.7))
                    },
                    improvement_areas=eval_data.get("improvement_areas", [])
                )
            
        except Exception as e:
            logger.error(f"Error parsing quality evaluation: {e}")
        
        # Return default quality score
        return QualityScore(
            overall_score=0.7,
            semantic_scores={"relevance": 0.7, "accuracy": 0.7, "completeness": 0.7, "clarity": 0.7, "natural_tone": 0.7, "appropriate_length": 0.7},
            improvement_areas=["Quality evaluation unavailable"]
        )

class ComplianceAgent:
    """Ensures compliance with financial regulations and legal requirements"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
    
    async def review_response(self, response: str, context: ConversationContext) -> ComplianceResult:
        """Review response for compliance and safety"""
        
        try:
            # Log the response before compliance review to track sources
            has_sources_before = "**Sources Used:**" in response or "**External Search Result Sources:**" in response
            logger.info(f"🔒 COMPLIANCE: Starting review - Response has sources: {has_sources_before}")
            if has_sources_before:
                logger.info(f"🔒 COMPLIANCE: Response length before review: {len(response)} characters")
                if "**Sources Used:**" in response:
                    sources_start = response.find("**Sources Used:**")
                    logger.info(f"🔒 COMPLIANCE: Sources section starts at position: {sources_start}")
                if "**External Search Result Sources:**" in response:
                    external_start = response.find("**External Search Result Sources:**")
                    logger.info(f"🔒 COMPLIANCE: External search section starts at position: {external_start}")
            
            prompt = self._build_compliance_review_prompt(response, context)
            
            review = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            compliance_result = self._parse_compliance_review(review.choices[0].message.content, response)
            
            # Log the result after compliance review
            has_sources_after = "**Sources Used:**" in compliance_result.final_response or "**External Search Result Sources:**" in compliance_result.final_response
            logger.info(f"🔒 COMPLIANCE: Review complete - Final response has sources: {has_sources_after}")
            if compliance_result.was_rewritten:
                logger.info(f"🔒 COMPLIANCE: Response was rewritten - Original: {len(response)} chars, Final: {len(compliance_result.final_response)} chars")
                if has_sources_before and not has_sources_after:
                    logger.warning("🔒 COMPLIANCE: WARNING - Sources were lost during compliance review!")
                elif has_sources_before and has_sources_after:
                    logger.info("🔒 COMPLIANCE: Sources preserved during compliance review")
            
            return compliance_result
            
        except Exception as e:
            logger.error(f"Error in compliance review: {e}")
            # Return safe compliance result
            return ComplianceResult(
                original_response=response,
                final_response=response,
                legal_compliance={"compliant": True, "issues": []},
                risk_assessment={"level": "low", "factors": []},
                disclaimers=["This information is for educational purposes only. Please consult with a licensed professional for personalized advice."],
                was_rewritten=False
            )
    
    def _build_compliance_review_prompt(self, response: str, context: ConversationContext) -> str:
        """Build prompt for compliance review"""
        
        return f"""
        Review this financial advice response for compliance and safety:
        
        **Response:** "{response}"
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Current Focus: {context.current_topic or 'General'}
        
        **Compliance Review Required:**
        1. **Legal Compliance**: Does this meet financial advisory regulations?
        2. **Risk Assessment**: What are the potential risks?
        3. **Disclaimers Needed**: What legal disclaimers should be added?
        4. **Response Safety**: Is this response safe and appropriate?
        
        **CRITICAL REQUIREMENTS:**
        - **PRESERVE ALL SOURCE ATTRIBUTION**: If the response contains "**Sources Used:**" or "**External Search Result Sources:**" sections, these MUST be kept intact
        - **PRESERVE EXTERNAL SEARCH CONTENT**: Any information from external sources should remain in the response
        - **ADD COMPLIANCE ELEMENTS**: Add disclaimers and safety warnings without removing existing content
        - **MAINTAIN RESPONSE QUALITY**: Keep the enhanced response quality from RAG + external search
        
        **Return JSON with compliance assessment:**
        {{
            "legal_compliance": true,
            "risk_assessment": "low|medium|high",
            "disclaimers_needed": ["disclaimer1", "disclaimer2"],
            "response_safe": true,
            "needs_rewriting": false,
            "rewritten_response": "original response if no changes needed"
        }}
        
        **Compliance Guidelines:**
        - Add appropriate disclaimers for financial information
        - Emphasize the need for professional consultation
        - Focus on educational content, not specific advice
        - Include risk warnings where appropriate
        - Use natural, helpful language - not corporate jargon
        - **NEVER remove source attribution or external search results**
        - **NEVER remove the enhanced content from RAG + external search**
        
        **IMPORTANT**: Most financial responses benefit from compliance edits. 
        Consider adding disclaimers, professional consultation reminders, or risk warnings 
        when appropriate. However, keep the language natural and helpful, not overly formal.
        
        **SOURCE PRESERVATION RULE**: If you see "**Sources Used:**" or "**External Search Result Sources:**" in the response, 
        you MUST include these sections in your rewritten response. These are critical for transparency and user trust.
        """
    
    def _parse_compliance_review(self, review: str, original_response: str) -> ComplianceResult:
        """Parse compliance review response"""
        
        try:
            import json
            
            # Try to extract JSON
            start_idx = review.find('{')
            end_idx = review.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = review[start_idx:end_idx]
                review_data = json.loads(json_str)
                
                needs_rewriting = review_data.get("needs_rewriting", False)
                final_response = review_data.get("rewritten_response", original_response) if needs_rewriting else original_response
                
                # CRITICAL: Ensure source attribution is preserved if rewriting occurred
                if needs_rewriting and final_response != original_response:
                    # Check if original had sources that need to be preserved
                    has_sources = "**Sources Used:**" in original_response or "**External Search Result Sources:**" in original_response
                    has_sources_in_final = "**Sources Used:**" in final_response or "**External Search Result Sources:**" in final_response
                    
                    logger.info(f"🔒 COMPLIANCE: Checking source preservation - Original has sources: {has_sources}, Final has sources: {has_sources_in_final}")
                    
                    if has_sources and not has_sources_in_final:
                        logger.warning("🔒 COMPLIANCE: Sources were lost during rewriting - restoring them")
                        # Extract source sections from original
                        source_sections = []
                        if "**Sources Used:**" in original_response:
                            sources_start = original_response.find("**Sources Used:**")
                            sources_end = original_response.find("\n\n", sources_start)
                            if sources_end == -1:
                                sources_end = len(original_response)
                            source_sections.append(original_response[sources_start:sources_end])
                            logger.info(f"🔒 COMPLIANCE: Extracted Sources Used section: {original_response[sources_start:sources_end][:100]}...")
                        
                        if "**External Search Result Sources:**" in original_response:
                            external_start = original_response.find("**External Search Result Sources:**")
                            external_end = original_response.find("\n\n", external_start)
                            if external_end == -1:
                                external_end = len(original_response)
                            source_sections.append(original_response[external_start:external_end])
                            logger.info(f"🔒 COMPLIANCE: Extracted External Search Result Sources section: {original_response[external_start:external_end][:100]}...")
                        
                        # Add sources back to final response
                        if source_sections:
                            final_response += "\n\n" + "\n\n".join(source_sections)
                            logger.info("🔒 COMPLIANCE: Successfully restored source attribution")
                            logger.info(f"🔒 COMPLIANCE: Final response now has sources: {'**Sources Used:**' in final_response or '**External Search Result Sources:**' in final_response}")
                    else:
                        logger.info("🔒 COMPLIANCE: Source preservation check passed - no action needed")
                
                return ComplianceResult(
                    original_response=original_response,
                    final_response=final_response,
                    legal_compliance={"compliant": review_data.get("legal_compliance", True), "issues": []},
                    risk_assessment={"level": review_data.get("risk_assessment", "low"), "factors": []},
                    disclaimers=review_data.get("disclaimers_needed", []),
                    was_rewritten=needs_rewriting
                )
            
        except Exception as e:
            logger.error(f"Error parsing compliance review: {e}")
        
        # Return safe compliance result
        return ComplianceResult(
            original_response=original_response,
            final_response=original_response,
            legal_compliance={"compliant": True, "issues": []},
            risk_assessment={"level": "low", "factors": []},
            disclaimers=["This information is for educational purposes only. Please consult with a licensed professional for personalized advice."],
            was_rewritten=False
        )

class ChatbotOrchestrator:
    """Orchestrates the entire chatbot pipeline"""
    
    def __init__(self, intent_classifier, smart_router, rag_system, external_search, tool_integrator, calculator_selector, quick_calculator, file_processor):
        self.intent_classifier = intent_classifier
        self.smart_router = smart_router
        self.rag_system = rag_system
        self.external_search = external_search
        self.tool_integrator = tool_integrator
        self.calculator_selector = calculator_selector
        self.quick_calculator = quick_calculator
        self.file_processor = file_processor
        
        # Initialize response components
        self.base_llm = BaseLLMResponse()
        self.quality_evaluator = QualityEvaluator()
        self.compliance_agent = ComplianceAgent()
        
        # Initialize NEW conversation memory system
        # self.conversation_memory = ConversationMemory() # REMOVED
        
        # Initialize simple conversation history for conversation management ONLY
        self.simple_history = SimpleConversationHistory(max_history=8, llm_client=self.base_llm.llm)
        logger.info(f"📝 SIMPLE HISTORY: Initialized with max_history={8} and LLM client")
        initial_stats = self.simple_history.get_history_stats()
        logger.info(f"📝 SIMPLE HISTORY: Initial stats: {initial_stats}")
        
        # Initialize context management components (simplified - no complex conversation_memory)
        self.context_updater = ConversationContextUpdater()
        # Remove complex query enhancer that was causing issues
        # self.query_enhancer = ContextAwareQueryEnhancer(conversation_memory=self.conversation_memory)
        self.context_guard = ContextPollutionGuard()
        
        # Initialize LLM context analyzer with LLM client from base_llm
        # self.context_analyzer = LLMContextAnalyzer(llm_client=self.base_llm.llm) # REMOVED
        # Remove complex query enhancer integration
        # self.query_enhancer.set_context_analyzer(self.context_analyzer)
        
        # Session management
        self.sessions: Dict[str, ChatSession] = {}
        
        logger.info("ChatbotOrchestrator initialized successfully")
    
    def disable_context_enhancement(self):
        """Emergency method to disable context enhancement if issues arise"""
        try:
            # self.query_enhancer.disable_enhancement() # This line is removed
            logger.warning("🎼 ORCHESTRATOR: Context enhancement disabled due to issues")
        except Exception as e:
            logger.error(f"🎼 ORCHESTRATOR: Error disabling context enhancement: {e}")
    
    def enable_context_enhancement(self):
        """Re-enable context enhancement"""
        try:
            # self.query_enhancer.enable_enhancement() # This line is removed
            logger.info("🎼 ORCHESTRATOR: Context enhancement re-enabled")
        except Exception as e:
            logger.error(f"🎼 ORCHESTRATOR: Error enabling context enhancement: {e}")
    
    async def process_message(self, message: ChatMessage, session_id: str) -> ChatResponse:
        """Process a chat message through the complete pipeline"""
        
        try:
            # Get or create session
            session = self._get_or_create_session(session_id)
            
            # Add message to session
            session.add_message(message)
            
            # Process through pipeline
            response = await self._process_through_pipeline(message, session)
            
            # Add response to session
            session.add_message(response)
            
            logger.info(f"Message processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    def _get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        
        if session_id not in self.sessions:
            # Create default context for new session
            default_context = ConversationContext(
                session_id=session_id,
                knowledge_level=KnowledgeLevel.BEGINNER,
                semantic_themes=[],
                user_goals=[],
                current_topic=None,
                previous_calculations=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                # REMOVED: Complex conversation_memory that was causing issues
                # conversation_memory=self.conversation_memory,
                simple_history=self.simple_history  # Keep simple history for conversation management
            )
            
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                context=default_context,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow()
            )
        
        # Update last activity
        self.sessions[session_id].last_activity = datetime.utcnow()
        return self.sessions[session_id]
    
    async def _process_through_pipeline(self, message: ChatMessage, session: ChatSession) -> ChatResponse:
        """Process message through the complete chatbot pipeline"""
        
        try:
            context = session.get_context()
            logger.info(f"Processing message through pipeline for session {session.session_id}")
            
            # NEW: Check for active calculator session BEFORE intent classification
            if context.calculator_state == "active" and context.calculator_session:
                logger.info(f"🧮 Active calculator session detected - bypassing main pipeline")
                return await self._handle_calculator_continuation(message, context)
            
            # Intent classification
            # Get intent classification
            logger.info(f"🎼 ORCHESTRATOR: Starting intent classification for message: '{message.content[:100]}...'")
            intent_result = await self.intent_classifier.classify_intent_semantically(message.content, context)
            logger.info(f"🎼 ORCHESTRATOR: Intent classification result: {intent_result.intent.value} with confidence {intent_result.confidence}")
            logger.info(f"Intent classified: {intent_result.intent.value} (confidence: {intent_result.confidence})")
            
            # Store intent in context for search decision logic
            context.current_intent = intent_result
            
            # Smart routing
            # Get routing decision
            logger.info(f"🎼 ORCHESTRATOR: Starting smart routing with intent: {intent_result.intent.value}")
            routing_decision = await self.smart_router.route_query_semantically(intent_result, context)
            logger.info(f"🎼 ORCHESTRATOR: Routing decision: {routing_decision.route_type.value} with confidence {routing_decision.confidence}")
            logger.info(f"Routing decision: {routing_decision.route_type.value} (confidence: {routing_decision.confidence})")
            
            # Generate response content
            response_content = await self._generate_response_content(routing_decision, message.content, context, intent_result)
            
            # Quality evaluation (skip for calculator, tool responses, and conversation management)
            quality_score = QualityScore(overall_score=1.0, ragas_scores={}, semantic_scores={}, satisfaction_score=1.0, improvement_areas=[])
            if routing_decision.route_type not in [RouteType.QUICK_CALCULATOR, RouteType.EXTERNAL_TOOL, RouteType.CONVERSATION_MANAGEMENT]:
                quality_score = await self.quality_evaluator.evaluate_response_quality(message.content, response_content, context)
                logger.info(f"Quality evaluation: {quality_score.overall_score}")
            
            # Compliance review (skip for calculator, tool responses, and conversation management)
            final_response = response_content
            disclaimers = []
            if routing_decision.route_type not in [RouteType.QUICK_CALCULATOR, RouteType.EXTERNAL_TOOL, RouteType.CONVERSATION_MANAGEMENT]:
                compliance_result = await self.compliance_agent.review_response(response_content, context)
                final_response = compliance_result.final_response
                disclaimers = compliance_result.disclaimers
                logger.info(f"Compliance review: {'rewritten' if compliance_result.was_rewritten else 'no changes'}")
            else:
                logger.info(f"Compliance review: Skipped for {routing_decision.route_type.value}")
            
            # Create chat response
            chat_response = ChatResponse(
                content=final_response,
                quality_score=quality_score.overall_score,
                routing_decision=routing_decision,
                disclaimers=disclaimers,
                metadata={"intent": intent_result.intent.value, "calculator_state": context.calculator_state}
            )
            
            # Update session
            session.add_message(message)
            session.add_message(ChatMessage(
                id=str(uuid.uuid4()),
                type=MessageType.ASSISTANT,
                content=final_response,
                timestamp=datetime.utcnow()
            ))
            
            # NEW: Update conversation context after response generation
            try:
                # RESTORED: Original context updater that maintains RAG context (semantic_themes, current_topic, etc.)
                await self.context_updater.update_context(session, message, intent_result, final_response)
                
                # Clean context to prevent pollution
                message_count = len(session.messages)
                session.context = self.context_guard.clean_context(session.context, message_count)
                
                # NEW: Add conversation turn to simple history for conversation management ONLY
                try:
                    logger.info(f"📝 SIMPLE HISTORY: Attempting to add conversation turn - User: '{message.content[:50]}...', Response: '{final_response[:50]}...'")
                    
                    self.simple_history.add_conversation_turn(
                        user_message=message.content,
                        bot_response=final_response
                    )
                    
                    # Log the current state of simple history
                    stats = self.simple_history.get_history_stats()
                    logger.info(f"📝 SIMPLE HISTORY: Successfully added conversation turn. Current stats: {stats}")
                    
                except Exception as e:
                    logger.error(f"📝 SIMPLE HISTORY: Error adding conversation turn: {e}")
                    # Don't fail the pipeline if simple history update fails
                
                logger.info("🔄 CONTEXT: Context updated and cleaned successfully")
            except Exception as e:
                logger.error(f"🔄 CONTEXT: Error updating context: {e}")
                # Don't fail the pipeline if context update fails
            
            return chat_response
            
        except Exception as e:
            logger.error(f"Error in pipeline processing: {e}")
            return self._create_error_response(message, f"Pipeline processing failed: {str(e)}")
    
    async def _generate_response_content(self, routing_decision: RoutingDecision, query: str, context: ConversationContext, intent_result: Optional[IntentResult] = None) -> str:
        """Generate response content based on routing decision"""
        try:
            logger.info(f"🎼 ORCHESTRATOR: Generating response content for route type: {routing_decision.route_type}")
            
            # REMOVED: Complex duplicate RAG prevention that was causing issues
            # The RAG system now handles its own deduplication internally
            
            if routing_decision.route_type == RouteType.RAG:
                logger.info("🎼 ORCHESTRATOR: Routing to RAG system")
                # Pass the needs_external_search flag directly to prevent duplicate logic
                needs_external_search = intent_result.needs_external_search if intent_result else False
                logger.info(f"🎼 ORCHESTRATOR: Passing needs_external_search={needs_external_search} to RAG system")
                
                rag_result = await self.rag_system.get_semantic_response(
                    query, context, intent_result, needs_external_search=needs_external_search
                )
                return rag_result.response
                
            elif routing_decision.route_type == RouteType.EXTERNAL_SEARCH:
                logger.info("🎼 ORCHESTRATOR: Routing to external search")
                search_result = await self.external_search.search_with_evaluation(
                    query, context, needs_external_search=True
                )
                return search_result.response
                
            elif routing_decision.route_type == RouteType.QUICK_CALCULATOR:
                logger.info("🎼 ORCHESTRATOR: Routing to quick calculator")
                return await self._handle_quick_calculator(query, context)
                
            elif routing_decision.route_type == RouteType.EXTERNAL_TOOL:
                logger.info("🎼 ORCHESTRATOR: Routing to external tool")
                tool_response = await self.tool_integrator.route_to_external_tool(
                    routing_decision.tool_type, context
                )
                return tool_response.message
                
            elif routing_decision.route_type == RouteType.BASE_LLM:
                logger.info("🎼 ORCHESTRATOR: Routing to base LLM")
                return await self.base_llm.generate_safe_response(query, context)
                
            elif routing_decision.route_type == RouteType.CALCULATOR_SELECTION:
                logger.info("🎼 ORCHESTRATOR: Routing to calculator selection")
                return await self._handle_calculator_selection(query, context, routing_decision)
                
            elif routing_decision.route_type == RouteType.CONVERSATION_MANAGEMENT:
                logger.info("🎼 ORCHESTRATOR: Routing to conversation management")
                return await self._handle_conversation_management(query, context)
                
            else:
                logger.warning(f"🎼 ORCHESTRATOR: Unknown route type: {routing_decision.route_type}")
                return await self.base_llm.generate_safe_response(query, context)
                
        except Exception as e:
            logger.error(f"🎼 ORCHESTRATOR: Error generating response content: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
        finally:
            # Reset the flag after processing is complete
            context._rag_system_called = False
    
    async def _handle_calculator_selection(self, query: str, context: ConversationContext, routing_decision: RoutingDecision) -> str:
        """Generate calculator selection prompt with descriptions"""
        try:
            suggested_calc = routing_decision.metadata.get("suggested_calculator", "quick") if routing_decision.metadata else "quick"
            
            selection_prompt = f"""
            Great! I can help you calculate your life insurance needs. Let me explain the different options so you can choose what works best for you:

            **🧮 Quick Calculator (Recommended for most people)**
            - **What it is**: 5 simple questions, immediate estimate
            - **Best for**: Quick estimates, basic planning, initial discussions
            - **Questions**: Age, income, dependents, debt, mortgage
            - **Time**: 2-3 minutes
            - **Output**: Basic coverage recommendation

            **📋 Detailed Assessment (New Client Assessment)**
            - **What it is**: 50+ comprehensive questions, thorough analysis
            - **Best for**: Thorough analysis, client assessments, detailed planning
            - **Questions**: Demographics, goals, education, special needs, legacy planning
            - **Time**: 15-20 minutes
            - **Output**: Comprehensive report with multiple scenarios

            **📊 Portfolio Analysis Calculator**
            - **What it is**: Portfolio-focused insurance analysis
            - **Best for**: Investment-focused clients, portfolio integration, holistic planning
            - **Questions**: Asset allocation, risk profile, investment goals, insurance integration
            - **Time**: 10-15 minutes
            - **Output**: Portfolio analysis with insurance recommendations

            **Which type of calculation would you prefer?**
            - Reply with "quick" for the Quick Calculator (fastest)
            - Reply with "detailed" for the Detailed Assessment (most comprehensive)
            - Reply with "portfolio" for the Portfolio Analysis (investment-focused)

            *Based on your query, I'd recommend starting with the **{suggested_calc}** calculator.*
            """
            
            return selection_prompt.strip()
            
        except Exception as e:
            logger.error(f"Error generating calculator selection: {e}")
            return "I can help you calculate your life insurance needs. Would you like to start with a quick calculation?"
    
    async def _handle_conversation_management(self, query: str, context: ConversationContext) -> str:
        """Handle conversation management queries using the simple history system"""
        try:
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Processing query: '{query}'")
            
            # Log the current state of simple history
            stats = self.simple_history.get_history_stats()
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Current simple history stats: {stats}")
            
            # Use the simple conversation history system
            query_lower = query.lower()
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Query type detection - query_lower: '{query_lower}'")
            
            # Check for different types of conversation management queries
            if any(phrase in query_lower for phrase in ["what did we just talk about", "what were we discussing", "what was our conversation about"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'what did we just talk about' query type")
                response = await self.simple_history.get_conversation_summary()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated summary response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["summarize", "summary", "recap", "what have we covered"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'summarize' query type")
                response = await self.simple_history.get_detailed_summary()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated detailed summary response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["what was the main topic", "what topic were we on", "what were we focusing on"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'main topic' query type")
                response = await self.simple_history.get_main_topic()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated main topic response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["repeat", "restate", "say again", "what did you say about"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'repeat' query type")
                response = await self.simple_history.get_last_response()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated repeat response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["how long have we been talking", "how many questions", "conversation length"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'metrics' query type")
                response = await self.simple_history.get_conversation_metrics()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated metrics response: {response[:100]}...")
                
            else:
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected generic query type")
                # Generic conversation management response
                response = await self.simple_history.get_generic_response()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated generic response: {response[:100]}...")
            
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Final response generated successfully: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"🗣️ CONVERSATION MANAGEMENT: Error handling conversation management: {e}")
            import traceback
            logger.error(f"🗣️ CONVERSATION MANAGEMENT: Full traceback: {traceback.format_exc()}")
            return "I'm having trouble accessing our conversation history right now. Could you please rephrase your question?"
    
    async def _handle_quick_calculator(self, query: str, context: ConversationContext) -> str:
        """Handle quick calculator interactions"""
        try:
            logger.info("🧮 Handling quick calculator request")
            
            # ✅ NO KEYWORD CHECK NEEDED - intent classification and smart routing already handled this
            
            # Start new calculation session
            session_id = f"calc_{int(datetime.utcnow().timestamp())}"
            context.calculator_session = {"session_id": session_id, "type": "quick"}
            context.calculator_state = "active"
            context.calculator_type = CalculatorType.QUICK
            
            # Get the string response from the calculator
            calculator_response = await self.quick_calculator.start_calculation_session(session_id, context)
            return calculator_response
            
        except Exception as e:
            logger.error(f"Error handling quick calculator: {e}")
            return f"I encountered an error with the calculator: {str(e)}"

    async def _handle_calculator_continuation(self, message: ChatMessage, context: ConversationContext) -> ChatResponse:
        """Handle messages during active calculator sessions"""
        try:
            logger.info(f"🧮 Handling calculator continuation for {context.calculator_type}")
            
            calculator_type = context.calculator_type
            
            if calculator_type == CalculatorType.QUICK:
                # Get the response from the calculator
                calculator_response = await self.quick_calculator.process_answer(
                    message.content, 
                    context
                )
                
                # Extract the message from the calculator response
                if isinstance(calculator_response, dict):
                    response_message = calculator_response.get("message", "Calculator response")
                    # Check if calculation is complete
                    if calculator_response.get("status") == "completed":
                        context.calculator_state = "completed"
                        context.calculator_session = None
                        logger.info("🧮 Calculator session completed")
                    elif calculator_response.get("status") == "error":
                        # Handle calculation errors
                        logger.error(f"🧮 Calculator error: {calculator_response.get('error', 'Unknown error')}")
                        response_message = f"❌ {calculator_response.get('message', 'Calculation failed')}"
                        context.calculator_state = "error"
                    elif calculator_response.get("status") == "exited":
                        # Handle calculator exit
                        context.calculator_state = None
                        context.calculator_session = None
                        context.calculator_type = None
                        logger.info("🧮 Calculator session exited by user")
                        # Return to normal conversation flow
                        return ChatResponse(
                            content=response_message,
                            quality_score=1.0,
                            routing_decision=RoutingDecision(
                                route_type=RouteType.BASE_LLM,
                                confidence=1.0,
                                reasoning="Calculator exited, returning to normal conversation",
                                tool_type=None,
                                session_id=context.session_id
                            ),
                            disclaimers=[],
                            metadata={"calculator_exited": True}
                        )
                    else:
                        # Continue with next question
                        logger.info(f"🧮 Calculator question: {calculator_response.get('status', 'unknown')}")
                else:
                    response_message = str(calculator_response)
                
            elif calculator_type == CalculatorType.DETAILED:
                # Route to detailed assessment tool
                response_message = "I'll help you with the detailed assessment. Let me route you to the assessment tool."
                context.calculator_state = "completed"
                context.calculator_session = None
                
            elif calculator_type == CalculatorType.PORTFOLIO:
                # Route to portfolio analysis tool
                response_message = "I'll help you with the portfolio analysis. Let me route you to the portfolio analysis tool."
                context.calculator_state = "completed"
                context.calculator_session = None
                
            else:
                response_message = "I'm not sure what type of calculation you need. Let me help you get started."
                context.calculator_state = None
                context.calculator_session = None
            
            # Create routing decision for calculator continuation
            routing_decision = RoutingDecision(
                route_type=RouteType.QUICK_CALCULATOR if calculator_type == CalculatorType.QUICK else RouteType.BASE_LLM,
                confidence=1.0,
                reasoning="Calculator session continuation",
                tool_type=None,
                session_id=context.session_id,
                metadata={"calculator_session": context.calculator_session}
            )
            
            return ChatResponse(
                content=response_message,
                quality_score=1.0,  # Perfect score for calculator responses
                routing_decision=routing_decision,
                disclaimers=[],
                metadata={"calculator_session": context.calculator_session, "calculator_state": context.calculator_state}
            )
            
        except Exception as e:
            logger.error(f"Error in calculator continuation: {e}")
            return self._create_error_response(message, f"Calculator error: {str(e)}")
    
    async def process_file_upload(self, file_data: bytes, filename: str, session_id: str) -> Dict[str, Any]:
        """Process file upload for analysis"""
        
        try:
            session = self._get_or_create_session(session_id)
            context = session.get_context()
            
            # Process file upload
            file_upload = await self.file_processor.process_uploaded_file(file_data, filename, context)
            
            return {
                "status": "success",
                "file_id": file_upload.file_id,
                "filename": file_upload.filename,
                "file_type": file_upload.file_type,
                "message": f"File '{filename}' uploaded successfully and ready for analysis."
            }
            
        except Exception as e:
            logger.error(f"Error processing file upload: {e}")
            return {
                "status": "error",
                "message": f"Error processing file: {str(e)}"
            }
    
    async def analyze_uploaded_file(self, file_id: str, query: str, session_id: str) -> str:
        """Analyze uploaded file in context of conversation"""
        
        try:
            session = self._get_or_create_session(session_id)
            context = session.get_context()
            
            # Analyze file
            analysis = await self.file_processor.analyze_file_in_context(file_id, query, context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            return f"Error analyzing file: {str(e)}"
    
    def get_file_summary(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get summary of uploaded file"""
        
        try:
            return self.file_processor.get_file_summary(file_id)
        except Exception as e:
            logger.error(f"Error getting file summary: {e}")
            return None
    
    def cleanup_files(self, max_age_hours: int = 24) -> int:
        """Clean up old uploaded files"""
        
        try:
            return self.file_processor.cleanup_old_files(max_age_hours)
        except Exception as e:
            logger.error(f"Error cleaning up files: {e}")
            return 0
    
    def _create_error_response(self, original_message: ChatMessage, error_message: str) -> ChatResponse:
        """Create error response when processing fails"""
        
        return ChatResponse(
            content=f"I'm sorry, I encountered an error while processing your message: {error_message}. Please try again or contact support if the problem persists.",
            quality_score=0.0,
            routing_decision=RoutingDecision(
                route_type=RouteType.BASE_LLM,
                confidence=0.0,
                reasoning="System error occurred"
            ),
            disclaimers=["This response indicates a system error. Please try again or contact support."],
            metadata={"error": error_message, "session_id": getattr(original_message, 'session_id', 'unknown')}
        ) 
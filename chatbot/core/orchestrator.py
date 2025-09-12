import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from openai import AsyncOpenAI
from .schemas import (
    ChatMessage, ChatResponse, ConversationContext, IntentResult,
    RoutingDecision, RAGResult, SearchResult, QualityScore,
    ComplianceResult, ChatSession, MessageType, RouteType, KnowledgeLevel,
    IntentCategory, CalculatorType, FollowUpResult
)
from .universal_context_selector import UniversalContextSelector, ContextSelectionResult
from .config import config
from .context_manager import ConversationContextUpdater, ContextPollutionGuard
from .simple_conversation_history import SimpleConversationHistory
from .session_persistence import SessionPersistenceManager

logger = logging.getLogger(__name__)

class BaseLLMResponse:
    """Handles base LLM responses for fallback and general knowledge"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        # Initialize universal context selector for follow-up support
        from .follow_up_detector import FollowUpDetector
        follow_up_detector = FollowUpDetector(self.llm)
        self.context_selector = UniversalContextSelector(follow_up_detector)
    
    async def generate_safe_response(self, query: str, context: ConversationContext) -> str:
        """Generate safe, educational response using base LLM"""
        
        try:
            # Use Universal Context Selector for intelligent context handling
            context_result = await self.context_selector.get_relevant_context(query, context)
            logger.info(f"🤖 BASE LLM: Context selection result: {context_result.context_type}")
            
            prompt = self._build_safe_response_prompt(query, context, context_result)
            
            response = await self.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating base LLM response: {e}")
            # Try fallback with basic context if context selection failed
            try:
                prompt = self._build_safe_response_prompt(query, context, None)
                response = await self.llm.chat.completions.create(
                    model=config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content
            except Exception as fallback_error:
                logger.error(f"Fallback LLM response also failed: {fallback_error}")
                return self._get_fallback_response(query)
    
    def _build_safe_response_prompt(self, query: str, context: ConversationContext, context_result: ContextSelectionResult = None) -> str:
        """Build safe prompt for base LLM"""
        
        # Build conversation context string based on context selection result
        conversation_context = ""
        if context_result and context_result.context_type in ["follow_up", "structured_data"] and context_result.context_selector:
            try:
                conversation_context = context_result.context_selector.get_conversation_context_string(context_result)
            except Exception as e:
                logger.error(f"Error getting conversation context string: {e}")
                conversation_context = f"""
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Focus Area: {context.current_topic or 'General'}
        """
        else:
            conversation_context = f"""
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Focus Area: {context.current_topic or 'General'}
        """
        
        # Check if this is a follow-up about calculator results
        is_calculator_follow_up = (context_result and 
                                 context_result.context_type == "follow_up" and 
                                 context_result.referenced_item in ["calculation", "analysis"])
        
        if is_calculator_follow_up:
            return f"""
        You are a financial advisor assistant. A user is asking a follow-up question about their life insurance calculation results.
        
        **User's Follow-up Question:** "{query}"
        
        {conversation_context}
        
        **Instructions:**
        1. Answer the user's question using the specific data from their calculator results
        2. Be specific and reference actual numbers from their calculation
        3. When explaining coverage needs, use the detailed breakdown to show how the total was calculated
        4. Explain concepts in terms appropriate for their knowledge level
        5. If they ask about something not in the calculation, say so politely
        6. Use a conversational, helpful tone
        7. Focus on being educational and informative
        8. Always provide specific dollar amounts and percentages when available
        9. For follow-up questions, provide MORE detail than the original response
        10. Use the detailed breakdown data to explain HOW calculations were made
        11. Reference specific sections of their calculation when relevant
        12. Provide actionable insights based on their specific situation
        13. If they ask vague questions like "tell me more", focus on the most important aspects of their calculation
        
        **Response Guidelines:**
        - Be specific about their actual numbers and situation
        - Explain the reasoning behind the recommendations
        - Use their actual coverage amounts and gaps
        - Reference their specific product recommendations
        - Explain how the calculation methodology applies to their situation
        
        Generate a helpful response based on their actual calculation data:
        """
        else:
            return f"""
        You are a knowledgeable financial advisor assistant. Answer this question naturally and helpfully:
        
        **User Question:** "{query}"
        
        {conversation_context}
        
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
    
    def __init__(self, intent_classifier, smart_router, rag_system, external_search, tool_integrator, calculator_selector, quick_calculator, file_processor, qdrant_client=None):
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
        # Note: We'll create per-session instances instead of a shared one
        self.simple_history_llm_client = self.base_llm.llm
        logger.info(f"📝 SIMPLE HISTORY: Initialized LLM client for per-session history")
        
        # Initialize context management components (simplified - no complex conversation_memory)
        self.context_updater = ConversationContextUpdater()
        # Remove complex query enhancer that was causing issues
        # self.query_enhancer = ContextAwareQueryEnhancer(conversation_memory=self.conversation_memory)
        self.context_guard = ContextPollutionGuard()
        
        # Initialize LLM context analyzer with LLM client from base_llm
        # self.context_analyzer = LLMContextAnalyzer(llm_client=self.base_llm.llm) # REMOVED
        # Remove complex query enhancer integration
        # self.query_enhancer.set_context_analyzer(self.context_analyzer)
        
        # Session management with persistence
        self.sessions: Dict[str, ChatSession] = {}
        self.session_persistence = SessionPersistenceManager(qdrant_client)
        
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
            session = await self._get_or_create_session(session_id)
            
            # Add message to session
            session.add_message(message)
            
            # Save session after adding message
            try:
                await self.session_persistence.save_session(session)
            except Exception as e:
                logger.warning(f"⚠️ Could not save session after adding message: {e}")
            
            # Process through pipeline
            response = await self._process_through_pipeline(message, session)
            
            # Add response to session
            session.add_message(response)
            
            # Save session after adding response
            try:
                await self.session_persistence.save_session(session)
            except Exception as e:
                logger.warning(f"⚠️ Could not save session after adding response: {e}")
            
            logger.info(f"Message processed successfully for session {session_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    async def _get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one with persistence"""
        
        # First check in-memory cache
        if session_id in self.sessions:
            self.sessions[session_id].last_activity = datetime.utcnow()
            return self.sessions[session_id]
        
        # Try to load from persistent storage
        try:
            session = await self.session_persistence.load_session(session_id)
            if session:
                # Load into memory cache
                self.sessions[session_id] = session
                session.last_activity = datetime.utcnow()
                logger.info(f"✅ Loaded session {session_id} from persistent storage")
                return session
        except Exception as e:
            logger.warning(f"⚠️ Could not load session {session_id} from storage: {e}")
        
        # Create new session if not found
        logger.info(f"🔧 Creating new session {session_id}")
        
        # Create per-session conversation history
        session_simple_history = SimpleConversationHistory(
            max_history=8, 
            llm_client=self.simple_history_llm_client
        )
        
        # Create default context for new session
        default_context = ConversationContext(
            session_id=session_id,
            knowledge_level=KnowledgeLevel.BEGINNER,
            user_goals=[],
            current_topic=None,
            previous_calculations=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            # REMOVED: Complex conversation_memory that was causing issues
            # conversation_memory=self.conversation_memory,
            simple_history=session_simple_history  # Per-session history for conversation management
        )
        
        new_session = ChatSession(
            session_id=session_id,
            context=default_context,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        # Store in memory cache
        self.sessions[session_id] = new_session
        
        # Save to persistent storage
        try:
            await self.session_persistence.save_session(new_session)
            logger.info(f"✅ Saved new session {session_id} to persistent storage")
        except Exception as e:
            logger.warning(f"⚠️ Could not save new session {session_id} to storage: {e}")
        
        return new_session
    
    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions that haven't been active for the specified time"""
        try:
            # Use persistence manager for cleanup
            cleaned_count = await self.session_persistence.cleanup_old_sessions(max_age_hours)
            
            # Also clean up in-memory cache
            current_time = datetime.utcnow()
            cutoff_time = current_time - timedelta(hours=max_age_hours)
            
            sessions_to_remove = []
            for session_id, session in self.sessions.items():
                if session.last_activity < cutoff_time:
                    sessions_to_remove.append(session_id)
            
            # Remove old sessions from memory
            for session_id in sessions_to_remove:
                del self.sessions[session_id]
                logger.info(f"🧹 SESSION CLEANUP: Removed old session {session_id} from memory")
            
            if sessions_to_remove or cleaned_count > 0:
                logger.info(f"🧹 SESSION CLEANUP: Cleaned up {cleaned_count} sessions from storage and {len(sessions_to_remove)} from memory")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
            return 0
    
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
                # RESTORED: Original context updater that maintains RAG context (current_topic, etc.)
                await self.context_updater.update_context(session, message, intent_result, final_response)
                
                # Clean context to prevent pollution
                message_count = len(session.messages)
                session.context = self.context_guard.clean_context(session.context, message_count)
                
                # NEW: Add conversation turn to simple history for conversation management ONLY
                try:
                    logger.info(f"📝 SIMPLE HISTORY: Attempting to add conversation turn - User: '{message.content[:50]}...', Response: '{final_response[:50]}...'")
                    
                    session.context.simple_history.add_conversation_turn(
                        user_message=message.content,
                        bot_response=final_response
                    )
                    
                    # Log the current state of simple history
                    stats = session.context.simple_history.get_history_stats()
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
                
                # Check if this is file analysis
                if routing_decision.metadata and routing_decision.metadata.get("is_file_analysis"):
                    logger.info("🎼 ORCHESTRATOR: Handling file analysis")
                    return await self._handle_file_analysis(query, context, routing_decision)
                else:
                    # Regular external tool handling
                    tool_response = await self.tool_integrator.route_to_external_tool(
                        routing_decision.tool_type, context
                    )
                    # Store the tool URL in the routing decision metadata for frontend access
                    routing_decision.metadata = {
                        "tool_url": tool_response.url,
                        "tool_type": tool_response.tool_type,
                        "action": tool_response.action
                    }
                    return tool_response.message
                
            elif routing_decision.route_type == RouteType.BASE_LLM:
                logger.info("🎼 ORCHESTRATOR: Routing to base LLM")
                
                # Check if this is a report question that needs report context
                if routing_decision.metadata and routing_decision.metadata.get("report_question"):
                    logger.info("🎼 ORCHESTRATOR: Handling report question with context")
                    return await self._handle_report_question(query, context, routing_decision)
                # Check if this is a quick calculator follow-up that needs calculator context
                elif routing_decision.metadata and routing_decision.metadata.get("quick_calculator_follow_up"):
                    logger.info("🎼 ORCHESTRATOR: Handling quick calculator follow-up with context")
                    return await self._handle_quick_calculator_follow_up(query, context, routing_decision)
                else:
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

            **📋 Client Assessment Tool**
            - **What it is**: 50+ comprehensive questions, thorough analysis
            - **Best for**: Thorough analysis, client assessments, detailed planning
            - **Questions**: Demographics, goals, education, special needs, legacy planning
            - **Time**: 15-20 minutes
            - **Output**: Comprehensive PDF report with multiple scenarios

            **📊 Portfolio Analysis Tool**
            - **What it is**: Portfolio-focused insurance analysis
            - **Best for**: Investment-focused clients, portfolio integration, holistic planning
            - **Questions**: Asset allocation, risk profile, investment goals, insurance integration
            - **Time**: 10-15 minutes
            - **Output**: Portfolio analysis PDF report with insurance recommendations

            **Which type of calculation would you prefer?**
            - Reply with "quick" for the Quick Calculator (fastest)
            - Reply with "detailed" for the Client Assessment Tool (most comprehensive)
            - Reply with "portfolio" for the Portfolio Analysis Tool (investment-focused)

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
            stats = context.simple_history.get_history_stats()
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Current simple history stats: {stats}")
            
            # Use the simple conversation history system
            query_lower = query.lower()
            logger.info(f"🗣️ CONVERSATION MANAGEMENT: Query type detection - query_lower: '{query_lower}'")
            
            # Check for different types of conversation management queries
            if any(phrase in query_lower for phrase in ["what did we just talk about", "what were we discussing", "what was our conversation about"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'what did we just talk about' query type")
                response = await context.simple_history.get_conversation_summary()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated summary response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["summarize", "summary", "recap", "what have we covered"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'summarize' query type")
                response = await context.simple_history.get_detailed_summary()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated detailed summary response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["what was the main topic", "what topic were we on", "what were we focusing on"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'main topic' query type")
                response = await context.simple_history.get_main_topic()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated main topic response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["repeat", "restate", "say again", "what did you say about"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'repeat' query type")
                response = await context.simple_history.get_last_response()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated repeat response: {response[:100]}...")
                
            elif any(phrase in query_lower for phrase in ["how long have we been talking", "how many questions", "conversation length"]):
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected 'metrics' query type")
                response = await context.simple_history.get_conversation_metrics()
                logger.info(f"🗣️ CONVERSATION MANAGEMENT: Generated metrics response: {response[:100]}...")
                
            else:
                logger.info("🗣️ CONVERSATION MANAGEMENT: Detected generic query type")
                # Generic conversation management response
                response = await context.simple_history.get_generic_response()
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
                        
                        # CRITICAL FIX: Store the detailed calculator response in conversation history
                        # This ensures follow-up questions can access the calculator data
                        try:
                            if hasattr(context, 'simple_history') and context.simple_history:
                                logger.info("🧮 ORCHESTRATOR: Storing calculator response in conversation history")
                                context.simple_history.add_conversation_turn(
                                    user_message=message.content,
                                    bot_response=response_message
                                )
                                logger.info("🧮 ORCHESTRATOR: Calculator response successfully stored in history")
                            else:
                                logger.warning("🧮 ORCHESTRATOR: No simple_history available to store calculator response")
                        except Exception as e:
                            logger.error(f"🧮 ORCHESTRATOR: Error storing calculator response in history: {e}")
                    
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
                # Route to detailed assessment tool via smart router
                logger.info("🧮 Calculator: Routing to detailed assessment tool")
                context.calculator_state = "completed"
                context.calculator_session = None
                
                # Create intent for detailed assessment
                assessment_intent = IntentResult(
                    intent=IntentCategory.CLIENT_ASSESSMENT_SUPPORT,
                    confidence=1.0,
                    reasoning="User selected detailed assessment from calculator selection",
                    calculator_type=CalculatorType.DETAILED,
                    needs_external_search=False
                )
                
                # Route through smart router to get proper deep link
                routing_decision = await self.smart_router.route_query_semantically(assessment_intent, context)
                response_message = routing_decision.metadata.get("tool_message", "I'll help you with the detailed assessment. Let me route you to the assessment tool.")
                
            elif calculator_type == CalculatorType.PORTFOLIO:
                # Route to portfolio analysis tool via smart router
                logger.info("🧮 Calculator: Routing to portfolio analysis tool")
                context.calculator_state = "completed"
                context.calculator_session = None
                
                # Create intent for portfolio analysis
                portfolio_intent = IntentResult(
                    intent=IntentCategory.PORTFOLIO_INTEGRATION_ANALYSIS,
                    confidence=1.0,
                    reasoning="User selected portfolio analysis from calculator selection",
                    calculator_type=CalculatorType.PORTFOLIO,
                    needs_external_search=False
                )
                
                # Route through smart router to get proper deep link
                routing_decision = await self.smart_router.route_query_semantically(portfolio_intent, context)
                response_message = routing_decision.metadata.get("tool_message", "I'll help you with the portfolio analysis. Let me route you to the portfolio analysis tool.")
                
            else:
                response_message = "I'm not sure what type of calculation you need. Let me help you get started."
                context.calculator_state = None
                context.calculator_session = None
            
            # Create routing decision for calculator continuation
            if calculator_type == CalculatorType.DETAILED:
                # Use the routing decision from smart router for detailed assessment
                pass  # routing_decision already created above
            elif calculator_type == CalculatorType.PORTFOLIO:
                # Use the routing decision from smart router for portfolio analysis
                pass  # routing_decision already created above
            else:
                # Create routing decision for other calculator types
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
            session = await self._get_or_create_session(session_id)
            context = session.get_context()
            
            # Process file upload
            file_upload = await self.file_processor.process_uploaded_file(file_data, filename, context)
            
            # Store file in session
            file_data = {
                "file_id": file_upload.file_id,
                "filename": file_upload.filename,
                "file_type": file_upload.file_type,
                "upload_time": file_upload.upload_time.isoformat(),
                "file_size": file_upload.file_size
            }
            session.add_uploaded_file(file_data)
            
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
            session = await self._get_or_create_session(session_id)
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
    
    async def _handle_report_question(self, query: str, context: ConversationContext, routing_decision: RoutingDecision) -> str:
        """Handle questions about existing reports by retrieving report context from conversation history"""
        
        try:
            logger.info(f"🎼 ORCHESTRATOR: Handling report question: {query[:100]}...")
            
            # Check if we have follow-up detection information
            referenced_item = None
            follow_up_result = None
            if hasattr(context, 'follow_up_result') and context.follow_up_result:
                follow_up_result = context.follow_up_result
                referenced_item = follow_up_result.referenced_item
                logger.info(f"🎼 ORCHESTRATOR: Detected referenced item: {referenced_item}")
            
            # Get conversation history to find the report data
            if not hasattr(context, 'simple_history') or not context.simple_history:
                logger.warning("No conversation history available for report question")
                return await self.base_llm.generate_safe_response(query, context)
            
            conversation_history = context.simple_history.get_conversation_turns()
            if not conversation_history:
                logger.warning("No conversation turns found")
                return await self.base_llm.generate_safe_response(query, context)
            
            # Find the most recent report data in conversation history
            report_data = await self._get_report_data_from_history(conversation_history)
            
            if not report_data:
                logger.warning("No report data found in conversation history, falling back to base LLM")
                return await self.base_llm.generate_safe_response(query, context)
            
            # Generate response using the actual report data from conversation history
            return await self._generate_report_response_with_data(query, context, report_data)
            
        except Exception as e:
            logger.error(f"Error handling report question: {e}")
            return await self.base_llm.generate_safe_response(query, context)
    
    async def _handle_quick_calculator_follow_up(self, query: str, context: ConversationContext, routing_decision: RoutingDecision) -> str:
        """Handle follow-up questions about quick calculator results using conversation context"""
        
        try:
            logger.info(f"🎼 ORCHESTRATOR: Handling quick calculator follow-up: {query[:100]}...")
            
            # Check if we have follow-up detection information
            referenced_item = None
            follow_up_result = None
            if hasattr(context, 'follow_up_result') and context.follow_up_result:
                follow_up_result = context.follow_up_result
                referenced_item = follow_up_result.referenced_item
                logger.info(f"🎼 ORCHESTRATOR: Detected referenced item: {referenced_item}")
            
            # Get conversation history to find the calculator response
            calculator_context = await self._get_calculator_context_from_history(context)
            
            if not calculator_context:
                # Fallback: Check if there's recent calculator data in the session
                if hasattr(context, 'calculator_session') and context.calculator_session:
                    logger.info("🎼 ORCHESTRATOR: No calculator context in history, but found active calculator session")
                    # Try to get the last calculator response from the session
                    calculator_response = await self._get_last_calculator_response_from_session(context)
                    if calculator_response:
                        calculator_context = {
                            "calculator_response": calculator_response,
                            "user_query": "Calculator completion",
                            "turn_data": {}
                        }
                        logger.info("🎼 ORCHESTRATOR: Retrieved calculator response from session")
                    else:
                        logger.warning("No calculator context found in conversation history or session, falling back to base LLM")
                        return await self.base_llm.generate_safe_response(query, context)
                else:
                    logger.warning("No calculator context found in conversation history or session, falling back to base LLM")
                    return await self.base_llm.generate_safe_response(query, context)
            
            # Generate response using calculator context
            return await self._generate_calculator_follow_up_response(query, context, calculator_context)
            
        except Exception as e:
            logger.error(f"Error handling quick calculator follow-up: {e}")
            return await self.base_llm.generate_safe_response(query, context)
    
    async def _get_calculator_context_from_history(self, context: ConversationContext) -> Optional[Dict[str, Any]]:
        """Retrieve calculator context from conversation history"""
        
        try:
            if not hasattr(context, 'simple_history') or not context.simple_history:
                logger.warning("No conversation history available for calculator context")
                return None
            
            # Get recent conversation turns
            conversation_history = context.simple_history.get_conversation_turns()
            if not conversation_history:
                logger.warning("No conversation turns found")
                return None
            
            logger.info(f"🎼 ORCHESTRATOR: Checking {len(conversation_history)} conversation turns for calculator response")
            
            # Look for the most recent calculator response
            for i, turn in enumerate(reversed(conversation_history[-5:])):  # Check last 5 turns
                assistant_response = turn.get('assistant_response', '')
                user_query = turn.get('user_query', '')
                
                logger.info(f"🎼 ORCHESTRATOR: Turn {i+1} - User: '{user_query[:50]}...', Assistant: '{assistant_response[:100]}...'")
                
                # Check if this looks like a calculator response
                if self._is_calculator_response(assistant_response):
                    logger.info(f"🎼 ORCHESTRATOR: Found calculator response in turn {i+1}")
                    return {
                        "calculator_response": assistant_response,
                        "user_query": user_query,
                        "turn_data": turn
                    }
            
            logger.warning("No calculator response found in recent conversation history")
            logger.info(f"🎼 ORCHESTRATOR: Available conversation turns: {[turn.get('user_query', '')[:30] for turn in conversation_history[-3:]]}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving calculator context from history: {e}")
            return None
    
    def _is_calculator_response(self, response: str) -> bool:
        """Check if a response looks like a calculator result"""
        calculator_indicators = [
            "COVERAGE ANALYSIS",
            "Coverage Needed:",
            "Current Coverage:",
            "Coverage Gap:",
            "COVERAGE BREAKDOWN",
            "PRODUCT RECOMMENDATION",
            "CASH VALUE SAVINGS",
            "NEXT STEPS",
            "DISCLAIMERS",
            "Based on your financial profile",
            "life insurance needs analysis",
            "About You:",
            "Cash Value Projections:",
            "Recommended Monthly Savings:",
            "Maximum (MEC Limit):",
            "Illustrated Rate:",
            "Monthly Contribution:",
            "Understanding your life insurance needs",
            "coverage requirements",
            "financial security",
            "JPM TermVest+",
            "IUL Track",
            "Term Track"
        ]
        
        # Check for multiple indicators to be more confident
        matches = [indicator for indicator in calculator_indicators if indicator in response]
        logger.info(f"🎼 ORCHESTRATOR: Calculator response check - Found {len(matches)} indicators: {matches[:3]}")
        
        # Require at least 2 indicators for a calculator response
        return len(matches) >= 2
    
    async def _get_last_calculator_response_from_session(self, context: ConversationContext) -> Optional[str]:
        """Get the last calculator response from the active calculator session"""
        try:
            if not hasattr(context, 'calculator_session') or not context.calculator_session:
                return None
            
            # For now, we'll return a generic message since we don't store the full response
            # In a real implementation, you might want to store the full calculator response
            # in the calculator session for retrieval
            return "Calculator response data not available in session. Please try asking about your calculation again."
            
        except Exception as e:
            logger.error(f"Error getting last calculator response from session: {e}")
            return None
    
    async def _generate_calculator_follow_up_response(self, query: str, context: ConversationContext, calculator_context: Dict[str, Any]) -> str:
        """Generate response using calculator context data"""
        
        try:
            calculator_response = calculator_context.get("calculator_response", "")
            
            # Build context-aware prompt with calculator data
            prompt = f"""
            You are a financial advisor assistant. A user is asking a follow-up question about their life insurance calculation results.
            
            **User's Follow-up Question:** "{query}"
            
            **Calculator Response Context:**
            {calculator_response}
            
            **User Context:**
            - Knowledge Level: {context.knowledge_level.value}
            - Current Topic: {context.current_topic or 'Life Insurance Calculation'}
            
            **Instructions:**
            1. Answer the user's question using the specific data from their calculator results
            2. Be specific and reference actual numbers from their calculation
            3. When explaining coverage needs, use the detailed breakdown to show how the total was calculated
            4. Explain concepts in terms appropriate for their knowledge level
            5. If they ask about something not in the calculation, say so politely
            6. Use a conversational, helpful tone
            7. Focus on being educational and informative
            8. Always provide specific dollar amounts and percentages when available
            9. For follow-up questions, provide MORE detail than the original response
            10. Use the detailed breakdown data to explain HOW calculations were made
            11. Reference specific sections of their calculation when relevant
            12. Provide actionable insights based on their specific situation
            13. If they ask vague questions like "tell me more", focus on the most important aspects of their calculation
            
            **Response Guidelines:**
            - Be specific about their actual numbers and situation
            - Explain the reasoning behind the recommendations
            - Use their actual coverage amounts and gaps
            - Reference their specific product recommendations
            - Explain how the calculation methodology applies to their situation
            
            Generate a helpful response based on their actual calculation data:
            """
            
            response = await self.base_llm.llm.chat.completions.create(
                model=config.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating calculator follow-up response: {e}")
            return f"I can see you're asking about your life insurance calculation, but I'm having trouble accessing the specific details right now. The calculation should contain information about your recommended coverage, current coverage, and coverage gap. Please try asking again or let me know if you need help with something specific from your analysis."
    
    async def _get_report_data_from_history(self, conversation_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract report data from conversation history"""
        
        try:
            logger.info(f"🎼 ORCHESTRATOR: Checking {len(conversation_history)} conversation turns for report data")
            
            # Look for the most recent report data in conversation turns
            for i, turn in enumerate(reversed(conversation_history[-10:])):  # Check last 10 turns
                assistant_response = turn.get('assistant_response', '')
                user_query = turn.get('user_query', '')
                
                # Check if this turn contains report data (portfolio or assessment)
                if self._contains_report_data(assistant_response):
                    logger.info(f"🎼 ORCHESTRATOR: Found report data in turn {len(conversation_history) - i}")
                    
                    # Extract the report data from the response
                    report_data = self._extract_report_data_from_response(assistant_response)
                    if report_data:
                        return {
                            "report_data": report_data,
                            "user_query": user_query,
                            "assistant_response": assistant_response,
                            "turn_data": turn
                        }
            
            logger.warning("No report data found in conversation history")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting report data from history: {e}")
            return None
    
    def _contains_report_data(self, response_content: str) -> bool:
        """Check if response contains report data (portfolio or assessment)"""
        report_indicators = [
            "recommended coverage:", "coverage gap:", "product recommendation:",
            "total assets:", "risk level:", "portfolio analysis completed",
            "assessment completed", "life insurance assessment",
            "coverage breakdown:", "living expenses:", "debts:", "education:",
            "funeral:", "legacy:", "about you", "asset allocation:",
            "portfolio health score:", "financial summary:"
        ]
        return any(indicator.lower() in response_content.lower() for indicator in report_indicators)
    
    def _extract_report_data_from_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """Extract structured report data from response content"""
        try:
            import re
            
            # Determine if this is assessment or portfolio data
            is_portfolio = any(indicator in response_content.lower() for indicator in [
                "portfolio analysis completed", "total assets:", "asset allocation:", 
                "portfolio health score:", "investable portfolio:", "account distribution:"
            ])
            
            if is_portfolio:
                # Extract portfolio data patterns
                total_assets_match = re.search(r'total assets:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                total_assets = float(total_assets_match.group(1).replace(',', '')) if total_assets_match else 0
                
                total_net_worth_match = re.search(r'total net worth:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                total_net_worth = float(total_net_worth_match.group(1).replace(',', '')) if total_net_worth_match else 0
                
                investable_portfolio_match = re.search(r'investable portfolio:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                investable_portfolio = float(investable_portfolio_match.group(1).replace(',', '')) if investable_portfolio_match else 0
                
                liquid_assets_match = re.search(r'liquid assets:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                liquid_assets = float(liquid_assets_match.group(1).replace(',', '')) if liquid_assets_match else 0
                
                # Extract asset allocation
                equity_match = re.search(r'equity:\s*\$?([\d,]+\.?\d*)\s*\(([\d.]+)%\)', response_content, re.IGNORECASE)
                equity_dollars = float(equity_match.group(1).replace(',', '')) if equity_match else 0
                equity_percent = float(equity_match.group(2)) if equity_match else 0
                
                fixed_income_match = re.search(r'fixed income:\s*\$?([\d,]+\.?\d*)\s*\(([\d.]+)%\)', response_content, re.IGNORECASE)
                fixed_income_dollars = float(fixed_income_match.group(1).replace(',', '')) if fixed_income_match else 0
                fixed_income_percent = float(fixed_income_match.group(2)) if fixed_income_match else 0
                
                real_estate_match = re.search(r'real estate:\s*\$?([\d,]+\.?\d*)\s*\(([\d.]+)%\)', response_content, re.IGNORECASE)
                real_estate_dollars = float(real_estate_match.group(1).replace(',', '')) if real_estate_match else 0
                real_estate_percent = float(real_estate_match.group(2)) if real_estate_match else 0
                
                cash_match = re.search(r'cash:\s*\$?([\d,]+\.?\d*)\s*\(([\d.]+)%\)', response_content, re.IGNORECASE)
                cash_dollars = float(cash_match.group(1).replace(',', '')) if cash_match else 0
                cash_percent = float(cash_match.group(2)) if cash_match else 0
                
                # Extract portfolio health metrics
                health_score_match = re.search(r'portfolio health:\s*(\d+)/100', response_content, re.IGNORECASE)
                health_score = int(health_score_match.group(1)) if health_score_match else 0
                
                risk_score_match = re.search(r'risk score:\s*(\d+)/100', response_content, re.IGNORECASE)
                risk_score = int(risk_score_match.group(1)) if risk_score_match else 0
                
                liquidity_ratio_match = re.search(r'liquidity ratio:\s*([\d.]+)x', response_content, re.IGNORECASE)
                liquidity_ratio = float(liquidity_ratio_match.group(1)) if liquidity_ratio_match else 0
                
                # Extract life insurance data
                recommended_coverage_match = re.search(r'recommended coverage:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                recommended_coverage = float(recommended_coverage_match.group(1).replace(',', '')) if recommended_coverage_match else 0
                
                coverage_gap_match = re.search(r'coverage gap:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                coverage_gap = float(coverage_gap_match.group(1).replace(',', '')) if coverage_gap_match else 0
                
                current_coverage_match = re.search(r'current coverage:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                current_coverage = float(current_coverage_match.group(1).replace(',', '')) if current_coverage_match else 0
                
                return {
                    "full_response": response_content,
                    "type": "portfolio_data",
                    "total_assets": total_assets,
                    "total_net_worth": total_net_worth,
                    "investable_portfolio": investable_portfolio,
                    "liquid_assets": liquid_assets,
                    "asset_allocation": {
                        "equity": {"dollars": equity_dollars, "percent": equity_percent},
                        "fixed_income": {"dollars": fixed_income_dollars, "percent": fixed_income_percent},
                        "real_estate": {"dollars": real_estate_dollars, "percent": real_estate_percent},
                        "cash": {"dollars": cash_dollars, "percent": cash_percent}
                    },
                    "portfolio_metrics": {
                        "health_score": health_score,
                        "risk_score": risk_score,
                        "liquidity_ratio": liquidity_ratio
                    },
                    "life_insurance": {
                        "recommended_coverage": recommended_coverage,
                        "coverage_gap": coverage_gap,
                        "current_coverage": current_coverage
                    }
                }
            else:
                # Extract assessment data patterns (existing logic)
                coverage_match = re.search(r'recommended coverage:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                recommended_coverage = float(coverage_match.group(1).replace(',', '')) if coverage_match else 0
                
                gap_match = re.search(r'coverage gap:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                coverage_gap = float(gap_match.group(1).replace(',', '')) if gap_match else 0
                
                product_match = re.search(r'product recommendation:\s*([^.\n]+)', response_content, re.IGNORECASE)
                product_recommendation = product_match.group(1).strip() if product_match else 'N/A'
                
                income_match = re.search(r'monthly income:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                monthly_income = float(income_match.group(1).replace(',', '')) if income_match else 0
                
                expenses_match = re.search(r'monthly expenses:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                monthly_expenses = float(expenses_match.group(1).replace(',', '')) if expenses_match else 0
                
                living_expenses_match = re.search(r'living expenses:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                living_expenses = float(living_expenses_match.group(1).replace(',', '')) if living_expenses_match else 0
                
                debts_match = re.search(r'debts:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                debts = float(debts_match.group(1).replace(',', '')) if debts_match else 0
                
                education_match = re.search(r'education:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                education = float(education_match.group(1).replace(',', '')) if education_match else 0
                
                funeral_match = re.search(r'funeral:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                funeral = float(funeral_match.group(1).replace(',', '')) if funeral_match else 0
                
                legacy_match = re.search(r'legacy:\s*\$?([\d,]+\.?\d*)', response_content, re.IGNORECASE)
                legacy = float(legacy_match.group(1).replace(',', '')) if legacy_match else 0
                
                return {
                    "full_response": response_content,
                    "type": "assessment_data",
                    "recommended_coverage": recommended_coverage,
                    "coverage_gap": coverage_gap,
                    "product_recommendation": product_recommendation,
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "needs_breakdown": {
                        "living_expenses": living_expenses,
                        "debts": debts,
                        "education": education,
                        "funeral": funeral,
                        "legacy": legacy
                    }
                }
        except Exception as e:
            logger.error(f"Error extracting report data: {e}")
            return None
    
    async def _generate_report_response_with_data(self, query: str, context: ConversationContext, report_data: Dict[str, Any]) -> str:
        """Generate response using actual report data from conversation history"""
        
        try:
            # Get the full report content from the conversation history
            full_report_content = report_data.get("report_data", {}).get("full_response", "")
            
            if not full_report_content:
                logger.warning("No report content found in report data")
                return await self.base_llm.generate_safe_response(query, context)
            
            # Create a context-aware prompt that includes the full report content
            prompt = f"""
            You are a financial advisor assistant. A user is asking a follow-up question about their assessment report.
            
            **User Question:** "{query}"
            
            **Assessment Report Data:**
            {full_report_content}
            
            Please provide a helpful response to the user's question using the specific data from their assessment report above. 
            Be precise with numbers and reference the actual values from their report. Do not use any hardcoded templates or generic responses.
            """
            
            # Use the base LLM to generate a response with the report context
            response = await self.base_llm.generate_safe_response(prompt, context)
            
            logger.info(f"🎼 ORCHESTRATOR: Generated report response with {len(full_report_content)} characters of report content")
            return response
            
        except Exception as e:
            logger.error(f"Error generating report response with data: {e}")
            return await self.base_llm.generate_safe_response(query, context)

    async def _get_report_context_for_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve report context for a session from the backend"""
        
        try:
            import httpx
            
            # Try to get report contexts for this session
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.get(f"{config.backend_api_url}/api/report-context/session/{session_id}")
                
                if response.status_code == 200:
                    data = response.json()
                    report_contexts = data.get("report_contexts", [])
                    
                    if report_contexts:
                        # Return the most recent report context
                        latest_context = max(report_contexts, key=lambda x: x.get("timestamp", 0))
                        logger.info(f"Found report context for session {session_id}")
                        return latest_context
                    else:
                        logger.info(f"No report contexts found for session {session_id}")
                        return None
                else:
                    logger.warning(f"Failed to retrieve report context: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error retrieving report context: {e}")
            return None
    
    def _select_relevant_context(self, conversation_history, follow_up_result: Optional[FollowUpResult] = None) -> Optional[Dict[str, Any]]:
        """Select the most relevant context for a follow-up question"""
        
        if not conversation_history:
            return None
        
        # If we have follow-up detection results, use them to guide context selection
        if follow_up_result and follow_up_result.referenced_item:
            logger.info(f"🎼 ORCHESTRATOR: Using referenced item: {follow_up_result.referenced_item}")
            
            # Check most recent bot response first for structured data
            recent_response = conversation_history[-1] if conversation_history else None
            if recent_response and self._contains_structured_data(recent_response.get('assistant_response', '')):
                logger.info(f"🎼 ORCHESTRATOR: Found structured data in most recent response")
                return recent_response
            
            # Look for specific topic matches in recent turns
            for turn in reversed(conversation_history[-3:]):  # Last 3 turns
                if self._topics_match(turn, follow_up_result.related_topics):
                    logger.info(f"🎼 ORCHESTRATOR: Found matching topic in conversation history")
                    return turn
        
        # Fall back to most recent turn
        return conversation_history[-1] if conversation_history else None
    
    def _contains_structured_data(self, response_content: str) -> bool:
        """Check if response contains structured data like portfolio reports"""
        indicators = [
            "total assets:", "risk level:", "life insurance need:",
            "portfolio analysis completed", "report available:",
            "download portfolio_report.pdf", "portfolio health score:",
            "asset allocation:", "recommended coverage:",
            "product recommendation:", "financial summary:"
        ]
        return any(indicator.lower() in response_content.lower() for indicator in indicators)
    
    def _topics_match(self, turn: Dict[str, Any], topics: List[str]) -> bool:
        """Check if a conversation turn matches the given topics"""
        if not topics:
            return False
        
        content = f"{turn.get('user_query', '')} {turn.get('assistant_response', '')}".lower()
        return any(topic.lower() in content for topic in topics)
    
    async def _generate_report_response(self, query: str, context: ConversationContext, report_context: Dict[str, Any]) -> str:
        """Generate response using report context data with enhanced data utilization"""
        
        try:
            # Extract key information from report context
            summary = report_context.get("summary", {})
            analysis_result = report_context.get("analysis_result", {})
            
            # NEW: Extract detailed breakdown data that's available in the logs
            detailed_breakdown = self._extract_detailed_breakdown(analysis_result)
            
            # Build context-aware prompt with enhanced data
            prompt = f"""
            You are a financial advisor assistant. A user is asking a question about their portfolio analysis report.
            
            **User Question:** "{query}"
            
            **Portfolio Analysis Summary:**
            - Total Assets: ${summary.get('total_assets', 0):,.2f}
            - Total Net Worth: ${analysis_result.get('total_net_worth', summary.get('total_net_worth', 0)):,.2f}
            - Risk Level: {summary.get('risk_level', 'N/A')}
            - Portfolio Health Score: {summary.get('portfolio_health_score', 0)}/100
            - Liquid Assets: ${analysis_result.get('liquid_assets', 0):,.2f}
            - Monthly Income: ${analysis_result.get('monthly_income', 0):,.2f}
            - Monthly Expenses: ${analysis_result.get('monthly_expenses', 0):,.2f}
            
            **Life Insurance Analysis:**
            - Life Insurance Need: ${summary.get('life_insurance_need', 0):,.2f}
            - Current Coverage: ${summary.get('current_life_insurance', 0):,.2f}
            - Coverage Gap: ${summary.get('coverage_gap', 0):,.2f}
            - Product Recommendation: {summary.get('product_recommendation', 'N/A')}
            - Rationale: {summary.get('rationale', 'N/A')}
            
            **Detailed Coverage Breakdown:**
            {detailed_breakdown}
            
            **Asset Allocation Details:**
            - Equity: ${summary.get('asset_allocation_dollars', {}).get('equity', 0):,.2f} ({summary.get('asset_allocation_percentages', {}).get('equity', 0):.1f}%)
            - Fixed Income: ${summary.get('asset_allocation_dollars', {}).get('fixed_income', 0):,.2f} ({summary.get('asset_allocation_percentages', {}).get('fixed_income', 0):.1f}%)
            - Real Estate: ${summary.get('asset_allocation_dollars', {}).get('real_estate', 0):,.2f} ({summary.get('asset_allocation_percentages', {}).get('real_estate', 0):.1f}%)
            - Cash: ${summary.get('asset_allocation_dollars', {}).get('cash', 0):,.2f} ({summary.get('asset_allocation_percentages', {}).get('cash', 0):.1f}%)
            
            **Account Breakdown:**
            - Retirement Accounts: ${summary.get('account_breakdown', {}).get('retirement_accounts', 0):,.2f}
            - Taxable Accounts: ${summary.get('account_breakdown', {}).get('taxable_accounts', 0):,.2f}
            - Education Accounts: ${summary.get('account_breakdown', {}).get('education_accounts', 0):,.2f}
            
            **Key Findings:**
            {', '.join(summary.get('key_findings', []))}
            
            **Risk Analysis:**
            {', '.join(summary.get('risk_analysis', []))}
            
            **Recommendations:**
            {', '.join(summary.get('recommendations', []))}
            
            **User Context:**
            - Knowledge Level: {context.knowledge_level.value}
            - Current Topic: {context.current_topic or 'Portfolio Analysis'}
            
            **Instructions:**
            1. Answer the user's question using the specific data from their report
            2. Be specific and reference actual numbers from their analysis
            3. When explaining coverage needs, use the detailed breakdown to show how the total was calculated
            4. Explain concepts in terms appropriate for their knowledge level
            5. If they ask about something not in the report, say so politely
            6. Use a conversational, helpful tone
            7. Focus on being educational and informative
            8. Always provide specific dollar amounts and percentages when available
            9. For follow-up questions, provide MORE detail than the original response
            10. Use the detailed breakdown data to explain HOW calculations were made
            11. Reference specific sections of their analysis when relevant
            12. Provide actionable insights based on their specific situation
            13. If they ask vague questions like "tell me more", focus on the most important aspects of their analysis
            
            Generate a helpful response based on their actual report data:
            """
            
            response = await self.base_llm.generate_safe_response(prompt, context)
            return response
            
        except Exception as e:
            logger.error(f"Error generating report response: {e}")
            return f"I can see you're asking about your portfolio report, but I'm having trouble accessing the specific details right now. The report should contain information about your recommended coverage, risk level, and other key metrics. Please try asking again or let me know if you need help with something specific from your analysis."
    
    def _extract_detailed_breakdown(self, analysis_result: Dict[str, Any]) -> str:
        """Extract detailed breakdown data from analysis result"""
        try:
            breakdown_parts = []
            
            # Extract life insurance needs breakdown
            life_insurance_needs = analysis_result.get('life_insurance_needs', {})
            if life_insurance_needs:
                breakdown_parts.append("**Life Insurance Needs Breakdown:**")
                breakdown_parts.append(f"- Income Replacement: ${life_insurance_needs.get('income_replacement', 0):,.2f}")
                breakdown_parts.append(f"- Debt Payoff: ${life_insurance_needs.get('debt_payoff', 0):,.2f}")
                breakdown_parts.append(f"- Education Funding: ${life_insurance_needs.get('education_funding', 0):,.2f}")
                breakdown_parts.append(f"- Funeral Expenses: ${life_insurance_needs.get('funeral_expenses', 0):,.2f}")
                breakdown_parts.append(f"- Legacy Amount: ${life_insurance_needs.get('legacy_amount', 0):,.2f}")
                breakdown_parts.append(f"- Special Needs: ${life_insurance_needs.get('special_needs', 0):,.2f}")
                breakdown_parts.append(f"- **Total Need: ${life_insurance_needs.get('total_need', 0):,.2f}**")
                
                # Add current coverage information (using pre-calculated data from backend)
                individual_life = analysis_result.get('individual_life', 0)
                group_life = analysis_result.get('group_life', 0)
                
                breakdown_parts.append("")
                breakdown_parts.append("**Current Coverage:**")
                breakdown_parts.append(f"- Individual Life Insurance: ${individual_life:,.2f}")
                breakdown_parts.append(f"- Group Life Insurance: ${group_life:,.2f}")
                breakdown_parts.append(f"- **Total Current Coverage: ${individual_life + group_life:,.2f}**")
                breakdown_parts.append(f"- **Coverage Gap: ${analysis_result.get('gap', 0):,.2f}**")
                breakdown_parts.append("")
            
            # Extract portfolio metrics
            portfolio_metrics = analysis_result.get('portfolio_metrics', {})
            if portfolio_metrics:
                breakdown_parts.append("**Portfolio Metrics:**")
                breakdown_parts.append(f"- Portfolio Health Score: {portfolio_metrics.get('portfolio_health_score', 0)}/100")
                breakdown_parts.append(f"- Risk Score: {portfolio_metrics.get('risk_score', 0)}")
                breakdown_parts.append(f"- Liquidity Ratio: {portfolio_metrics.get('liquidity_ratio', 0):.2f}")
                breakdown_parts.append(f"- Diversification Score: {portfolio_metrics.get('diversification_score', 0)}")
                breakdown_parts.append("")
            
            # Extract concentration risks
            concentration_risks = portfolio_metrics.get('concentration_risks', [])
            if concentration_risks:
                breakdown_parts.append("**Concentration Risks:**")
                for risk in concentration_risks:
                    breakdown_parts.append(f"- {risk}")
                breakdown_parts.append("")
            
            # Extract rebalancing needs
            rebalancing_needs = portfolio_metrics.get('rebalancing_needs', [])
            if rebalancing_needs:
                breakdown_parts.append("**Rebalancing Needs:**")
                for need in rebalancing_needs:
                    breakdown_parts.append(f"- {need}")
                breakdown_parts.append("")
            
            return "\n".join(breakdown_parts)
            
        except Exception as e:
            logger.error(f"Error extracting detailed breakdown: {e}")
            return "Detailed breakdown data not available."

    async def process_tool_completion(self, external_session_id: str, tool_type: str, result_data: Dict[str, Any]) -> str:
        """Process tool completion and return summary response"""
        
        try:
            # Generate a context-aware summary response
            summary_prompt = f"""
            A user has completed a {tool_type} tool with the following results:
            
            {json.dumps(result_data, indent=2)}
            
            Please generate a brief, professional summary (2-3 sentences) of the key findings.
            Focus on the most important insights and recommendations.
            """
            
            response = await self.base_llm.generate_safe_response(
                summary_prompt, 
                ConversationContext(session_id=external_session_id)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing tool completion: {e}")
            if tool_type in ["assessment", "detailed_assessment", "client_assessment"]:
                return "Your assessment has been completed successfully. The results show your insurance needs analysis and recommendations."
            elif tool_type == "portfolio":
                return "Your portfolio analysis has been completed successfully. The results include risk assessment and recommendations for your financial planning."
            else:
                return f"Your {tool_type} analysis has been completed successfully."
    
    async def _handle_file_analysis(self, query: str, context: ConversationContext, routing_decision: RoutingDecision) -> str:
        """Handle file analysis questions"""
        
        try:
            logger.info(f"🎼 ORCHESTRATOR: Handling file analysis for query: '{query[:50]}...'")
            
            # Get the most recent file upload for this session
            session = await self._get_or_create_session(context.session_id)
            uploaded_files = session.get_uploaded_files()
            
            if not uploaded_files:
                return "I don't see any files uploaded in this session. Please upload a file first, then ask me to analyze it."
            
            # Get the most recent file
            latest_file = uploaded_files[-1]
            file_id = latest_file.get('file_id')
            
            if not file_id:
                return "I found an uploaded file but couldn't access its details. Please try uploading the file again."
            
            # Analyze the file
            analysis = await self.file_processor.analyze_file_in_context(file_id, query, context)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error handling file analysis: {e}")
            return f"I encountered an error while analyzing the file: {str(e)}. Please try again."
    
    def _format_asset_allocation(self, summary: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """Format asset allocation with correct percentages"""
        
        try:
            # Get dollar amounts
            equity_dollars = summary.get('asset_allocation_dollars', {}).get('equity', 0)
            fixed_income_dollars = summary.get('asset_allocation_dollars', {}).get('fixed_income', 0)
            real_estate_dollars = summary.get('asset_allocation_dollars', {}).get('real_estate', 0)
            cash_dollars = summary.get('asset_allocation_dollars', {}).get('cash', 0)
            
            # Calculate total for percentage calculation
            total_assets = analysis_result.get('total_assets', 0)
            
            if total_assets > 0:
                equity_pct = (equity_dollars / total_assets) * 100
                fixed_income_pct = (fixed_income_dollars / total_assets) * 100
                real_estate_pct = (real_estate_dollars / total_assets) * 100
                cash_pct = (cash_dollars / total_assets) * 100
            else:
                equity_pct = fixed_income_pct = real_estate_pct = cash_pct = 0
            
            return f"""- Equity: ${equity_dollars:,.2f} ({equity_pct:.1f}%)
- Fixed Income: ${fixed_income_dollars:,.2f} ({fixed_income_pct:.1f}%)
- Real Estate: ${real_estate_dollars:,.2f} ({real_estate_pct:.1f}%)
- Cash: ${cash_dollars:,.2f} ({cash_pct:.1f}%)"""
            
        except Exception as e:
            logger.error(f"Error formatting asset allocation: {e}")
            return "- Asset allocation data unavailable"
    
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
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics for monitoring"""
        try:
            metrics = {
                "sessions": {
                    "total": len(self.sessions),
                    "active": sum(1 for session in self.sessions.values() if session.status == "active")
                },
                "context_selection": {},
                "follow_up_detection": {},
                "routing": {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Get context selection metrics from base LLM
            if hasattr(self.base_llm, 'context_selector'):
                context_metrics = self.base_llm.context_selector.get_context_metrics()
                metrics["context_selection"] = {
                    "selection_accuracy": context_metrics.selection_accuracy,
                    "average_relevance": context_metrics.average_relevance,
                    "average_quality": context_metrics.average_quality,
                    "fallback_usage": context_metrics.fallback_usage,
                    "validation_failures": context_metrics.validation_failures,
                    "total_selections": context_metrics.total_selections
                }
                
                # Get recent validation history
                validation_history = self.base_llm.context_selector.get_validation_history(5)
                metrics["context_selection"]["recent_validations"] = validation_history
            
            # Get follow-up detection metrics
            if hasattr(self.base_llm, 'context_selector') and hasattr(self.base_llm.context_selector, 'follow_up_detector'):
                follow_up_metrics = self.base_llm.context_selector.follow_up_detector.get_metrics()
                metrics["follow_up_detection"] = {
                    "total_detections": follow_up_metrics.get("total_detections", 0),
                    "successful_detections": follow_up_metrics.get("successful_detections", 0),
                    "average_confidence": follow_up_metrics.get("average_confidence", 0.0),
                    "cache_hit_rate": follow_up_metrics.get("cache_hit_rate", 0.0)
                }
            
            # Get routing metrics
            metrics["routing"] = {
                "total_queries": getattr(self, '_total_queries', 0),
                "successful_routes": getattr(self, '_successful_routes', 0),
                "failed_routes": getattr(self, '_failed_routes', 0)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def reset_system_metrics(self) -> None:
        """Reset all system metrics"""
        try:
            # Reset context selection metrics
            if hasattr(self.base_llm, 'context_selector'):
                self.base_llm.context_selector.reset_metrics()
            
            # Reset internal counters
            self._total_queries = 0
            self._successful_routes = 0
            self._failed_routes = 0
            
            logger.info("🎼 ORCHESTRATOR: System metrics reset")
            
        except Exception as e:
            logger.error(f"Error resetting system metrics: {e}") 
"""
Universal Context Selection System

This module provides a unified context selection system that all routing paths can use
to handle follow-up questions and conversation context intelligently.
"""

import logging
import hashlib
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .schemas import ConversationContext, IntentResult, FollowUpResult, ContextValidationResult, ContextSelectionResult
from .follow_up_detector import FollowUpDetector
from .context_validator import ContextValidator
from .error_handler import UnifiedErrorHandler

logger = logging.getLogger(__name__)


class UniversalContextSelector:
    """Unified context selection for all routing paths"""
    
    def __init__(self, follow_up_detector: FollowUpDetector, cache_ttl: int = 300):  # 5 minutes cache
        self.follow_up_detector = follow_up_detector
        self.context_validator = ContextValidator()
        self.error_handler = UnifiedErrorHandler()
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}  # Simple in-memory cache
        logger.info("🌐 UNIVERSAL CONTEXT: Initialized UniversalContextSelector with caching, validation, and error handling")
    
    def _get_cache_key(self, query: str, context: ConversationContext) -> str:
        """Generate cache key for context selection"""
        # Create a hash of the query and context state
        context_str = f"{query}|||{context.knowledge_level.value}|||{context.current_topic or 'none'}"
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[ContextSelectionResult]:
        """Get cached context selection result"""
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                logger.debug(f"🌐 UNIVERSAL CONTEXT: Using cached result for key: {cache_key[:8]}...")
                return cached_data.get('result')
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: ContextSelectionResult):
        """Cache context selection result"""
        self._cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        # Clean up old cache entries periodically
        if len(self._cache) > 50:  # Limit cache size
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Clean up expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, data in self._cache.items()
            if current_time - data.get('timestamp', 0) >= self.cache_ttl
        ]
        for key in expired_keys:
            del self._cache[key]
        logger.debug(f"🌐 UNIVERSAL CONTEXT: Cleaned up {len(expired_keys)} expired cache entries")
    
    async def get_relevant_context(
        self, 
        query: str, 
        context: ConversationContext, 
        intent_result: Optional[IntentResult] = None
    ) -> ContextSelectionResult:
        """
        Get relevant context for any routing path
        
        Args:
            query: The user's current query
            context: The conversation context
            intent_result: The intent classification result
            
        Returns:
            ContextSelectionResult with appropriate context information
        """
        try:
            logger.info(f"🌐 UNIVERSAL CONTEXT: Selecting context for query: '{query[:50]}...'")
            
            # Check cache first for performance optimization
            cache_key = self._get_cache_key(query, context)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info("🌐 UNIVERSAL CONTEXT: Using cached result for performance")
                return cached_result
            
            # PRIORITY 1: Check for uploaded files in context (highest priority for file-related queries)
            if hasattr(context, 'uploaded_files') and context.uploaded_files:
                latest_file = context.uploaded_files[-1]
                if self._is_file_related_query(query, latest_file):
                    logger.info(f"🌐 UNIVERSAL CONTEXT: File-related query detected, using file context: {latest_file.get('filename', 'unknown')}")
                    
                    # Validate file context
                    validation_result = await self.context_validator.validate_context_selection(
                        query, None, None, context
                    )
                    
                    result = ContextSelectionResult(
                        context_type="file_analysis",
                        conversation_history=[],
                        relevant_turn=None,
                        follow_up_result=None,
                        conversation_context=context,
                        intent_result=intent_result,
                        referenced_item="file_upload",
                        context_summary=f"File analysis context for {latest_file.get('filename', 'uploaded file')}",
                        context_selector=self,
                        validation_result=validation_result
                    )
                    
                    # Cache the result for performance optimization
                    self._cache_result(cache_key, result)
                    return result
            
            # 2. Check for follow-up detection if we have conversation history
            if hasattr(context, 'simple_history') and context.simple_history:
                conversation_history = context.simple_history.get_conversation_turns()
                
                if conversation_history:
                    logger.info(f"🌐 UNIVERSAL CONTEXT: Found {len(conversation_history)} conversation turns")
                    
                    # Detect if this is a follow-up question
                    follow_up_result = await self.follow_up_detector.detect_follow_up(query, conversation_history)
                    
                    if follow_up_result.is_follow_up:
                        logger.info(f"🌐 UNIVERSAL CONTEXT: Follow-up detected - {follow_up_result.referenced_item}")
                        
                        # Use suggested context window for better follow-up handling
                        suggested_window = follow_up_result.suggested_context_window
                        if suggested_window > 1:
                            # Use more conversation history for high-relevance follow-ups
                            conversation_history = conversation_history[-suggested_window:] if len(conversation_history) >= suggested_window else conversation_history
                            logger.info(f"🌐 UNIVERSAL CONTEXT: Using context window of {suggested_window} turns for follow-up")
                        
                        # Use smart context selection for follow-ups
                        relevant_turn = self._select_relevant_context(conversation_history, follow_up_result)
                        
                        # Validate context selection with enhanced validation
                        validation_result = await self.context_validator.validate_context_selection(
                            query, relevant_turn, follow_up_result, context
                        )
                        
                        # Use fallback if validation fails
                        if not validation_result.is_valid:
                            logger.warning(f"🌐 UNIVERSAL CONTEXT: Context validation failed: {validation_result.issues}")
                            relevant_turn = conversation_history[-1] if conversation_history else None
                            # Re-validate fallback context
                            validation_result = await self.context_validator.validate_context_selection(
                                query, relevant_turn, follow_up_result, context
                            )
                        
                        context_summary = self._build_context_summary(relevant_turn, follow_up_result)
                        
                        result = ContextSelectionResult(
                            context_type="follow_up",
                            conversation_history=conversation_history,
                            relevant_turn=relevant_turn,
                            follow_up_result=follow_up_result,
                            conversation_context=context,
                            intent_result=intent_result,
                            referenced_item=follow_up_result.referenced_item,
                            context_summary=context_summary,
                            context_selector=self,
                            validation_result=validation_result
                        )
                        
                        # Cache the result for performance optimization
                        self._cache_result(cache_key, result)
                        return result
            
            # 2. Check for structured data in recent conversation
            if hasattr(context, 'simple_history') and context.simple_history:
                conversation_history = context.simple_history.get_conversation_turns()
                if conversation_history:
                    recent_response = conversation_history[-1] if conversation_history else None
                    if recent_response and self._contains_structured_data(recent_response.get('content', '')):
                        logger.info("🌐 UNIVERSAL CONTEXT: Recent structured data detected")
                        context_summary = self._build_structured_data_summary(recent_response)
                        
                        # Validate structured data context
                        validation_result = await self.context_validator.validate_context_selection(
                            query, recent_response, None, context
                        )
                        
                        result = ContextSelectionResult(
                            context_type="structured_data",
                            conversation_history=conversation_history,
                            relevant_turn=recent_response,
                            conversation_context=context,
                            intent_result=intent_result,
                            context_summary=context_summary,
                            context_selector=self,
                            validation_result=validation_result
                        )
                        
                        # Cache the result for performance optimization
                        self._cache_result(cache_key, result)
                        return result
            
            # 3. Fallback to standard context
            logger.info("🌐 UNIVERSAL CONTEXT: Using standard context")
            
            # Validate standard context (minimal validation for fallback)
            validation_result = await self.context_validator.validate_context_selection(
                query, None, None, context
            )
            
            result = ContextSelectionResult(
                context_type="standard",
                conversation_context=context,
                intent_result=intent_result,
                context_summary=self._build_standard_context_summary(context),
                context_selector=self,
                validation_result=validation_result
            )
            
            # Cache the result for performance optimization
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"🌐 UNIVERSAL CONTEXT: Error in context selection: {e}")
            # Use unified error handler for better error recovery
            error_context = self.error_handler.handle_error(
                error=e,
                component="universal_context_selector",
                user_query=query,
                conversation_context=context
            )
            return await self._handle_context_selection_error(e, query, context, intent_result)
    
    def _select_relevant_context(self, conversation_history: List[Dict[str, Any]], follow_up_result: FollowUpResult) -> Optional[Dict[str, Any]]:
        """Select the most relevant conversation turn for follow-up questions - SIMPLIFIED APPROACH"""
        try:
            if not conversation_history:
                return None
            
            # SIMPLIFIED: Just return the most recent turn and let the LLM figure it out
            # The LLM is much better at understanding context than our complex logic
            recent_turn = conversation_history[-1] if conversation_history else None
            logger.info("🌐 UNIVERSAL CONTEXT: Using most recent conversation turn (simplified approach)")
            return recent_turn
            
        except Exception as e:
            logger.error(f"🌐 UNIVERSAL CONTEXT: Error selecting relevant context: {e}")
            return conversation_history[-1] if conversation_history else None
    
    def _contains_structured_data(self, response_content: str) -> bool:
        """Check if response contains structured data like portfolio reports or calculator results"""
        indicators = [
            # Portfolio analysis indicators
            "total assets:", "risk level:", "life insurance need:",
            "portfolio analysis completed", "report available:",
            "download portfolio_report.pdf", "portfolio health score:",
            "asset allocation:", "recommended coverage:",
            "product recommendation:", "financial summary:",
            "calculation completed", "analysis results:",
            "coverage gap:", "monthly contribution:",
            
            # Quick calculator indicators
            "COVERAGE ANALYSIS", "Coverage Needed:", "Current Coverage:",
            "Coverage Gap:", "COVERAGE BREAKDOWN", "PRODUCT RECOMMENDATION",
            "CASH VALUE SAVINGS", "NEXT STEPS", "DISCLAIMERS",
            "About You:", "Cash Value Projections:", "Recommended Monthly Savings:",
            "Maximum (MEC Limit):", "Illustrated Rate:", "Monthly Contribution:",
            "Understanding your life insurance needs", "coverage requirements",
            "financial security", "JPM TermVest+", "IUL Track", "Term Track",
            "Based on your financial profile", "life insurance needs analysis"
        ]
        return any(indicator.lower() in response_content.lower() for indicator in indicators)
    
    def _topics_match(self, turn: Dict[str, Any], topics: List[str]) -> bool:
        """Check if conversation turn matches any of the follow-up topics"""
        if not topics:
            return False
        
        # Get content from both user query and assistant response
        user_query = turn.get('user_query', '').lower()
        assistant_response = turn.get('assistant_response', '').lower()
        content = turn.get('content', '') or turn.get('assistant_response', '').lower()
        
        # Combine all content for matching
        full_content = f"{user_query} {assistant_response} {content}".lower()
        
        # Check for topic matches with better matching logic
        for topic in topics:
            topic_lower = topic.lower()
            
            # Direct topic match
            if topic_lower in full_content:
                return True
            
            # Check for related terms
            if topic_lower == "portfolio analysis":
                if any(term in full_content for term in ['portfolio', 'analysis', 'report', 'coverage', 'assets']):
                    return True
            elif topic_lower == "life insurance":
                if any(term in full_content for term in ['insurance', 'coverage', 'life', 'premium', 'policy']):
                    return True
            elif topic_lower == "calculation":
                if any(term in full_content for term in ['calculate', 'computed', 'result', 'needs', 'coverage']):
                    return True
        
        return False
    
    def _build_context_summary(self, relevant_turn: Optional[Dict[str, Any]], follow_up_result: FollowUpResult) -> str:
        """Build a summary of the relevant context for follow-up questions"""
        if not relevant_turn:
            return f"Follow-up about: {', '.join(follow_up_result.related_topics)}"
        
        content = relevant_turn.get('content', '') or relevant_turn.get('assistant_response', '')
        if self._contains_structured_data(content):
            return f"Previous {follow_up_result.referenced_item or 'analysis'} with detailed results"
        else:
            return f"Previous discussion about: {', '.join(follow_up_result.related_topics)}"
    
    def _build_structured_data_summary(self, turn: Dict[str, Any]) -> str:
        """Build summary for structured data responses"""
        content = turn.get('content', '') or turn.get('assistant_response', '')
        if "portfolio analysis completed" in content.lower():
            return "Recent portfolio analysis with detailed metrics and recommendations"
        elif "calculation" in content.lower():
            return "Recent calculation with specific results and recommendations"
        else:
            return "Recent analysis with structured data and recommendations"
    
    def _build_standard_context_summary(self, context: ConversationContext) -> str:
        """Build summary for standard context"""
        topic = context.current_topic or 'General'
        return f"Knowledge level: {context.knowledge_level.value}, Topic: {topic}"
    
    def get_context_metrics(self):
        """Get context selection metrics"""
        return self.context_validator.get_metrics()
    
    def get_validation_history(self, limit: int = 10):
        """Get recent validation history"""
        return self.context_validator.get_validation_history(limit)
    
    def reset_metrics(self):
        """Reset context selection metrics"""
        self.context_validator.reset_metrics()
    
    def _validate_context_selection(self, relevant_turn: Optional[Dict[str, Any]], follow_up_result: FollowUpResult, query: str) -> bool:
        """Validate that the selected context is appropriate for the follow-up question"""
        try:
            if not relevant_turn:
                logger.warning("🌐 UNIVERSAL CONTEXT: No relevant turn selected for validation")
                return False
            
            # Check if the context matches the referenced item
            referenced_item = follow_up_result.referenced_item
            content = relevant_turn.get('content', '') or relevant_turn.get('assistant_response', '') or relevant_turn.get('assistant_response', '')
            
            if referenced_item == "portfolio_report":
                if not self._contains_structured_data(content):
                    logger.warning("🌐 UNIVERSAL CONTEXT: Selected context doesn't contain portfolio data for portfolio report follow-up")
                    return False
            
            elif referenced_item == "file_upload":
                user_query = relevant_turn.get('user_query', '').lower()
                if not any(keyword in user_query for keyword in ['upload', 'file', 'document', 'pdf']):
                    logger.warning("🌐 UNIVERSAL CONTEXT: Selected context doesn't contain file upload for file follow-up")
                    return False
            
            elif referenced_item == "calculation":
                if not any(keyword in content.lower() for keyword in ['calculated', 'calculation', 'computed', 'result']):
                    logger.warning("🌐 UNIVERSAL CONTEXT: Selected context doesn't contain calculation data for calculation follow-up")
                    return False
            
            # Check if the context is recent enough (within last 5 turns)
            # This is a basic validation - more sophisticated validation could be added
            
            logger.info("🌐 UNIVERSAL CONTEXT: Context validation passed")
            return True
            
        except Exception as e:
            logger.error(f"🌐 UNIVERSAL CONTEXT: Error in context validation: {e}")
            return False
    
    async def _handle_context_selection_error(self, error: Exception, query: str, context: ConversationContext, intent_result: Optional[IntentResult]) -> ContextSelectionResult:
        """Handle context selection errors with multiple fallback strategies"""
        try:
            logger.warning(f"🌐 UNIVERSAL CONTEXT: Implementing error recovery for context selection failure: {error}")
            
            # Strategy 1: Try to get basic conversation history without follow-up detection
            try:
                if hasattr(context, 'simple_history') and context.simple_history:
                    conversation_history = context.simple_history.get_conversation_turns()
                    if conversation_history:
                        # Use the most recent turn as fallback
                        recent_turn = conversation_history[-1]
                        logger.info("🌐 UNIVERSAL CONTEXT: Error recovery - using most recent conversation turn")
                        return ContextSelectionResult(
                            context_type="standard",
                            conversation_history=conversation_history,
                            relevant_turn=recent_turn,
                            conversation_context=context,
                            intent_result=intent_result,
                            context_summary="Error recovery - using most recent context",
                            context_selector=self
                        )
            except Exception as recovery_error:
                logger.error(f"🌐 UNIVERSAL CONTEXT: Error recovery strategy 1 failed: {recovery_error}")
            
            # Strategy 2: Use basic context without conversation history
            logger.info("🌐 UNIVERSAL CONTEXT: Error recovery - using basic context without conversation history")
            return ContextSelectionResult(
                context_type="standard",
                conversation_context=context,
                intent_result=intent_result,
                context_summary="Error recovery - using basic context only",
                context_selector=self
            )
            
        except Exception as recovery_error:
            logger.error(f"🌐 UNIVERSAL CONTEXT: All error recovery strategies failed: {recovery_error}")
            # Final fallback - minimal context
            return ContextSelectionResult(
                context_type="standard",
                conversation_context=context,
                intent_result=intent_result,
                context_summary="Critical error - minimal context available",
                context_selector=self
            )
    
    def get_conversation_context_string(self, result: ContextSelectionResult) -> str:
        """Get a formatted conversation context string for use in prompts - SIMPLIFIED APPROACH"""
        if result.context_type == "follow_up" and result.conversation_history:
            # YOUR APPROACH: Use suggested context window from follow-up detector
            suggested_window = result.follow_up_result.suggested_context_window if result.follow_up_result else 7
            context_turns = min(suggested_window, len(result.conversation_history))
            recent_turns = result.conversation_history[-context_turns:]
            
            logger.info(f"🌐 UNIVERSAL CONTEXT: Using {context_turns} turns as suggested by follow-up detector")
            
            # Build conversation context in the format you described
            conversation_parts = []
            for i, turn in enumerate(recent_turns):
                user_query = turn.get('user_query', '')
                assistant_response = turn.get('assistant_response', '')
                
                if user_query and assistant_response:
                    conversation_parts.append(f"**Query {i+1}:** {user_query}")
                    conversation_parts.append(f"**Response {i+1}:** {assistant_response}")
                    conversation_parts.append("")  # Empty line for readability
            
            return f"""
**Relevant Conversation History ({context_turns} turns):**
{chr(10).join(conversation_parts)}

**Follow-up Context:**
- Referenced Item: {result.referenced_item or 'Previous discussion'}
- Related Topics: {', '.join(result.follow_up_result.related_topics) if result.follow_up_result else 'None'}
"""
        elif result.context_type == "structured_data" and result.conversation_history:
            # Use last 3 turns for structured data
            recent_turns = result.conversation_history[-3:]
            logger.info(f"🌐 UNIVERSAL CONTEXT: Using last 3 turns for structured data")
            
            # Build conversation context
            conversation_parts = []
            for i, turn in enumerate(recent_turns):
                user_query = turn.get('user_query', '')
                assistant_response = turn.get('assistant_response', '')
                
                if user_query and assistant_response:
                    conversation_parts.append(f"**Query {i+1}:** {user_query}")
                    conversation_parts.append(f"**Response {i+1}:** {assistant_response}")
                    conversation_parts.append("")  # Empty line for readability
            
            return f"""
**Recent Conversation History (3 turns):**
{chr(10).join(conversation_parts)}
"""
        else:
            return f"""
**Conversation Context:**
{result.context_summary or 'Standard conversation context'}
"""
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get error handling summary"""
        return self.error_handler.get_error_summary()
    
    def clear_error_history(self) -> None:
        """Clear error history"""
        self.error_handler.clear_error_history()
    
    def _is_file_related_query(self, query: str, file_data: Dict[str, Any]) -> bool:
        """Check if a query is related to uploaded files"""
        query_lower = query.lower()
        
        # Check for explicit file-related keywords
        file_keywords = [
            'file', 'document', 'pdf', 'upload', 'uploaded', 'this file', 'the file',
            'summarize this file', 'analyze this file', 'what does this file say',
            'tell me about this file', 'explain this file', 'break down this file'
        ]
        
        # Check if query contains file-related keywords
        if any(keyword in query_lower for keyword in file_keywords):
            return True
        
        # Check if query is asking about file content
        content_keywords = [
            'what does it say', 'what is in it', 'what does this contain',
            'summarize it', 'explain it', 'break it down', 'tell me about it'
        ]
        
        # If it's a vague follow-up and we have a recent file upload, assume it's about the file
        vague_follow_up_keywords = [
            'can you summarize this', 'tell me more about this', 'what about this',
            'can you elaborate on this', 'explain this better', 'break this down'
        ]
        
        if any(keyword in query_lower for keyword in vague_follow_up_keywords):
            # Check if the file was uploaded recently (within last few minutes)
            import time
            current_time = time.time()
            upload_time = file_data.get('upload_time', '')
            
            if upload_time:
                try:
                    from datetime import datetime
                    if isinstance(upload_time, str):
                        upload_timestamp = datetime.fromisoformat(upload_time.replace('Z', '+00:00')).timestamp()
                    else:
                        upload_timestamp = upload_time.timestamp()
                    
                    # If file was uploaded within last 5 minutes, assume query is about it
                    if current_time - upload_timestamp < 300:  # 5 minutes
                        return True
                except Exception:
                    # If we can't parse the timestamp, assume it's recent
                    return True
        
        return False

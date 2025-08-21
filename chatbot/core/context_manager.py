"""
Context-Aware Conversation Management System

This module provides intelligent conversation context management that enables
follow-up questions and conversation continuity while preventing context pollution.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import re

from .schemas import ConversationContext, ChatMessage, MessageType
from .config import config

logger = logging.getLogger(__name__)


@dataclass
class ContextAnalysisResult:
    """Result of context analysis"""
    semantic_themes: List[str]
    current_topic: Optional[str]
    user_goals: List[str]
    conversation_summary: str
    relevance_score: float


class ConversationContextUpdater:
    """Updates conversation context based on conversation flow"""
    
    def __init__(self):
        self.max_themes = 5  # Maximum themes to maintain
        self.max_goals = 3   # Maximum goals to maintain
        self.context_ttl = 10  # Context items older than 10 messages are pruned
        self.min_relevance_score = 0.3  # Minimum relevance for inclusion
        
    async def update_context(self, session, message: ChatMessage, 
                           intent_result, response: str) -> None:
        """Update context after response generation"""
        try:
            logger.info("🔄 CONTEXT: Starting context update")
            
            # 1. Extract semantic themes from recent conversation
            # Include both user message and assistant response for context
            recent_messages = session.messages[-6:] if len(session.messages) >= 6 else session.messages
            
            # Also extract themes from the current user message and assistant response
            current_themes = []
            
            # Extract themes from user message
            if hasattr(message, 'type') and message.type == MessageType.USER:
                user_themes = self._extract_themes_from_text(message.content)
                current_themes.extend(user_themes)
            elif hasattr(message, 'content'):
                # Fallback: if message doesn't have type but has content, treat as user message
                user_themes = self._extract_themes_from_text(message.content)
                current_themes.extend(user_themes)
            
            # Extract themes from assistant response (if it contains relevant insurance terms)
            if response:
                response_themes = self._extract_themes_from_text(response)
                current_themes.extend(response_themes)
            
            # Combine with recent conversation themes
            all_themes = current_themes + [theme for msg in recent_messages if hasattr(msg, 'type') and msg.type == MessageType.USER 
                                        for theme in self._extract_themes_from_text(msg.content)]
            
            # Remove duplicates and limit
            themes = list(dict.fromkeys(all_themes))[:self.max_themes]
            
            # 2. Update current topic based on conversation flow
            current_topic = await self._identify_current_topic(themes, intent_result)
            
            # 3. Recognize user goals from conversation patterns
            goals = await self._extract_user_goals(session.messages[-10:] if len(session.messages) >= 10 else session.messages)
            
            # 4. Clean and filter context to prevent pollution
            cleaned_themes = self._clean_semantic_themes(themes)
            cleaned_goals = self._clean_user_goals(goals)
            
            # 5. Update context fields
            session.update_context(
                semantic_themes=cleaned_themes,
                current_topic=current_topic,
                user_goals=cleaned_goals,
                updated_at=datetime.utcnow()
            )
            
            logger.info(f"🔄 CONTEXT: Updated - themes: {len(cleaned_themes)}, topic: {current_topic}, goals: {len(cleaned_goals)}")
            
        except Exception as e:
            logger.error(f"🔄 CONTEXT: Error updating context: {e}")
            # Don't fail the entire pipeline if context update fails
    

    
    def _extract_themes_from_text(self, text: str) -> List[str]:
        """Extract themes from text using pattern matching"""
        themes = []
        text_lower = text.lower()
        
        # Insurance-related themes
        insurance_keywords = {
            'term life': 'Term Life Insurance',
            'whole life': 'Whole Life Insurance',
            'universal life': 'Universal Life Insurance',
            'iul': 'Indexed Universal Life',
            'variable life': 'Variable Life Insurance',
            'life insurance': 'Life Insurance',
            'coverage': 'Insurance Coverage',
            'premium': 'Insurance Premiums',
            'death benefit': 'Death Benefit',
            'cash value': 'Cash Value'
        }
        
        for keyword, theme in insurance_keywords.items():
            if keyword in text_lower:
                themes.append(theme)
        
        # Financial planning themes
        financial_keywords = {
            'retirement': 'Retirement Planning',
            'investment': 'Investment Planning',
            'estate': 'Estate Planning',
            'tax': 'Tax Planning',
            'budget': 'Budget Planning',
            'savings': 'Savings Goals'
        }
        
        for keyword, theme in financial_keywords.items():
            if keyword in text_lower:
                themes.append(theme)
        
        # Calculator themes
        if any(word in text_lower for word in ['calculate', 'calculator', 'coverage needs', 'insurance needs']):
            themes.append('Insurance Needs Calculation')
        
        return themes
    
    async def _identify_current_topic(self, themes: List[str], intent_result) -> Optional[str]:
        """Identify current topic based on themes and intent"""
        try:
            if not themes:
                return None
            
            # Use the most recent theme as current topic
            current_topic = themes[-1] if themes else None
            
            # Override with intent-specific topic if available
            if intent_result and hasattr(intent_result, 'intent'):
                intent_value = intent_result.intent.value
                if 'calculator' in intent_value:
                    current_topic = 'Insurance Needs Calculation'
                elif 'education' in intent_value:
                    current_topic = 'Life Insurance Education'
                elif 'comparison' in intent_value:
                    current_topic = 'Product Comparison'
            
            logger.info(f"🔄 CONTEXT: Identified current topic: {current_topic}")
            return current_topic
            
        except Exception as e:
            logger.error(f"🔄 CONTEXT: Error identifying current topic: {e}")
            return None
    
    async def _extract_user_goals(self, messages: List[ChatMessage]) -> List[str]:
        """Extract user goals from conversation patterns"""
        try:
            goals = []
            
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == MessageType.USER:
                    content_lower = msg.content.lower()
                    
                    # Goal patterns
                    if any(word in content_lower for word in ['need', 'want', 'looking for', 'interested in']):
                        if 'life insurance' in content_lower:
                            goals.append('Find Life Insurance Coverage')
                        if 'calculate' in content_lower:
                            goals.append('Calculate Insurance Needs')
                        if 'compare' in content_lower:
                            goals.append('Compare Insurance Products')
                        if 'learn' in content_lower or 'understand' in content_lower:
                            goals.append('Learn About Insurance')
            
            # Remove duplicates and limit
            unique_goals = list(dict.fromkeys(goals))[:self.max_goals]
            logger.info(f"🔄 CONTEXT: Extracted goals: {unique_goals}")
            return unique_goals
            
        except Exception as e:
            logger.error(f"🔄 CONTEXT: Error extracting goals: {e}")
            return []
    
    def _clean_semantic_themes(self, themes: List[str]) -> List[str]:
        """Clean and filter semantic themes to prevent pollution"""
        try:
            if not themes:
                return []
            
            # Remove duplicates while preserving order
            cleaned = list(dict.fromkeys(themes))
            
            # Limit to maximum themes
            cleaned = cleaned[:self.max_themes]
            
            # Filter out very short or generic themes
            cleaned = [theme for theme in cleaned if len(theme) > 3 and theme != 'Insurance']
            
            logger.info(f"🔄 CONTEXT: Cleaned themes: {cleaned}")
            return cleaned
            
        except Exception as e:
            logger.error(f"🔄 CONTEXT: Error cleaning themes: {e}")
            return themes[:self.max_themes] if themes else []
    
    def _clean_user_goals(self, goals: List[str]) -> List[str]:
        """Clean and filter user goals to prevent pollution"""
        try:
            if not goals:
                return []
            
            # Remove duplicates while preserving order
            cleaned = list(dict.fromkeys(goals))
            
            # Limit to maximum goals
            cleaned = cleaned[:self.max_goals]
            
            # Filter out very generic goals
            cleaned = [goal for goal in cleaned if len(goal) > 10]
            
            logger.info(f"🔄 CONTEXT: Cleaned goals: {cleaned}")
            return cleaned
            
        except Exception as e:
            logger.error(f"🔄 CONTEXT: Error cleaning goals: {e}")
            return goals[:self.max_goals] if goals else []


class ContextAwareQueryEnhancer:
    """
    NEW: Completely rewritten context-aware query enhancer that uses:
    - Conversation memory system for true context understanding
    - LLM-based context analysis for natural language understanding
    - Intelligent query enhancement based on conversation history
    """
    
    def __init__(self, conversation_memory=None, context_analyzer=None):
        self.conversation_memory = conversation_memory
        self.context_analyzer = context_analyzer
        self.enhancement_enabled = True
        self.enhancement_attempts = 0
        self.enhancement_successes = 0
        
        logger.info("🔍 CONTEXT: Initialized new ContextAwareQueryEnhancer with conversation memory")
    
    def set_conversation_memory(self, conversation_memory):
        """Set the conversation memory system"""
        self.conversation_memory = conversation_memory
        logger.info("🔍 CONTEXT: Conversation memory system connected")
    
    def set_context_analyzer(self, context_analyzer):
        """Set the LLM context analyzer"""
        self.context_analyzer = context_analyzer
        logger.info("🔍 CONTEXT: LLM context analyzer connected")
    
    async def enhance_query_for_rag(self, query: str, context: ConversationContext) -> str:
        """
        NEW: Intelligently enhance query using conversation memory and LLM analysis.
        
        This method now:
        1. Uses conversation memory to understand context
        2. Uses LLM analysis to understand follow-up questions
        3. Enhances queries based on actual conversation history
        4. Provides ChatGPT-like context awareness
        """
        try:
            if not self.enhancement_enabled:
                logger.info("🔍 CONTEXT: Enhancement disabled, returning original query")
                return query
            
            # Check if we have conversation memory available
            if not self.conversation_memory:
                logger.warning("🔍 CONTEXT: No conversation memory available, returning original query")
                return query
            
            # Check if the context has conversation memory
            if not hasattr(context, 'conversation_memory') or not context.conversation_memory:
                logger.warning("🔍 CONTEXT: Context has no conversation memory, returning original query")
                return query
            
            self.enhancement_attempts += 1
            
            # Use LLM context analyzer if available
            if self.context_analyzer:
                try:
                    context_analysis = await self.context_analyzer.analyze_query_context(query, context.conversation_memory)
                    
                    if context_analysis.get("is_follow_up", False):
                        enhanced_query = self.context_analyzer.suggest_query_enhancement(query, context_analysis)
                        
                        if enhanced_query != query:
                            self.enhancement_successes += 1
                            logger.info(f"🔍 CONTEXT: LLM-enhanced query: '{query[:50]}...' -> '{enhanced_query[:100]}...'")
                            return enhanced_query
                except Exception as e:
                    logger.error(f"🔍 CONTEXT: Error in LLM context analysis: {e}")
                    # Continue with memory-based enhancement
            
            # Fallback to memory-based enhancement
            try:
                enhanced_query = self._enhance_with_memory(query, context.conversation_memory)
                
                if enhanced_query != query:
                    self.enhancement_successes += 1
                    logger.info(f"🔍 CONTEXT: Memory-enhanced query: '{query[:50]}...' -> '{enhanced_query[:100]}...'")
                    return enhanced_query
            except Exception as e:
                logger.error(f"🔍 CONTEXT: Error in memory-based enhancement: {e}")
                # Return original query if enhancement fails
            
            logger.info("🔍 CONTEXT: No enhancement needed for this query")
            return query
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT: Error enhancing query: {e}")
            return query
    
    def _enhance_with_memory(self, query: str, conversation_memory) -> str:
        """Enhance query using conversation memory"""
        try:
            if not conversation_memory:
                return query
            
            # Get conversation context
            context = conversation_memory.get_conversation_context()
            
            # Check if this is a follow-up question
            is_follow_up, main_topic, related_concepts = conversation_memory.understand_follow_up(query)
            
            if not is_follow_up:
                return query
            
            # Build enhanced query
            enhanced_parts = [query]
            
            if main_topic:
                enhanced_parts.append(f"Focus on: {main_topic}")
            
            if related_concepts:
                enhanced_parts.append(f"Related concepts: {', '.join(related_concepts[:3])}")
            
            enhanced_query = " | ".join(enhanced_parts)
            
            # Validate enhancement
            if self._validate_enhancement(query, enhanced_query):
                return enhanced_query
            
            return query
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT: Error in memory-based enhancement: {e}")
            return query
    
    def _validate_enhancement(self, original_query: str, enhanced_query: str) -> bool:
        """Validate that the enhancement is useful"""
        try:
            if enhanced_query == original_query:
                return False
            
            if len(enhanced_query) > len(original_query) * 3:
                return False
            
            if '|' not in enhanced_query:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT: Error validating enhancement: {e}")
            return False
    
    def get_enhancement_metrics(self) -> Dict[str, Any]:
        """Get enhancement performance metrics"""
        try:
            success_rate = 0.0
            if self.enhancement_attempts > 0:
                success_rate = self.enhancement_successes / self.enhancement_attempts
            
            return {
                "enhancement_enabled": self.enhancement_enabled,
                "total_attempts": self.enhancement_attempts,
                "successful_enhancements": self.enhancement_successes,
                "success_rate": success_rate,
                "has_conversation_memory": self.conversation_memory is not None,
                "has_context_analyzer": self.context_analyzer is not None
            }
        except Exception as e:
            logger.error(f"🔍 CONTEXT: Error getting metrics: {e}")
            return {}
    
    def disable_enhancement(self):
        """Disable context enhancement"""
        self.enhancement_enabled = False
        logger.warning("🔍 CONTEXT: Context enhancement disabled")
    
    def enable_enhancement(self):
        """Enable context enhancement"""
        self.enhancement_enabled = True
        logger.info("🔍 CONTEXT: Context enhancement enabled")


class ContextPollutionGuard:
    """Prevents context pollution and maintains relevance"""
    
    def __init__(self):
        self.max_themes = 5  # Maximum themes to maintain
        self.max_goals = 3   # Maximum goals to maintain
        self.context_ttl = 10  # Context items older than 10 messages are pruned
        self.cleanup_threshold = 15  # Cleanup when message count exceeds this
    
    def clean_context(self, context: ConversationContext, message_count: int) -> ConversationContext:
        """Clean and prune context to prevent pollution"""
        try:
            # NEW: Use conversation memory system instead of old context fields
            if hasattr(context, 'conversation_memory') and context.conversation_memory:
                # Let the memory system handle its own cleanup
                logger.info("🧹 CONTEXT: Using conversation memory system for context management")
                return context
            
            # FALLBACK: Old context cleaning logic (kept for backward compatibility)
            # Only cleanup if we have many messages
            if message_count < self.cleanup_threshold:
                return context
            
            logger.info(f"🧹 CONTEXT: Cleaning context (message count: {message_count})")
            
            # Prune old semantic themes
            if hasattr(context, 'semantic_themes') and context.semantic_themes:
                if len(context.semantic_themes) > self.max_themes:
                    context.semantic_themes = context.semantic_themes[-self.max_themes:]
                    logger.info(f"🧹 CONTEXT: Pruned themes to {len(context.semantic_themes)}")
            
            # Prune old user goals
            if hasattr(context, 'user_goals') and context.user_goals:
                if len(context.user_goals) > self.max_goals:
                    context.user_goals = context.user_goals[-self.max_goals:]
                    logger.info(f"🧹 CONTEXT: Pruned goals to {len(context.user_goals)}")
            
            # Reset current topic if it's too old
            if hasattr(context, 'current_topic') and context.current_topic:
                if self._is_topic_stale(context):
                    context.current_topic = None
                    logger.info("🧹 CONTEXT: Reset stale current topic")
            
            logger.info("🧹 CONTEXT: Context cleanup completed")
            return context
            
        except Exception as e:
            logger.error(f"🧹 CONTEXT: Error cleaning context: {e}")
            return context
    
    def _is_topic_stale(self, context: ConversationContext) -> bool:
        """Check if current topic is stale and should be reset"""
        try:
            if not hasattr(context, 'updated_at') or not context.updated_at:
                return True
            
            # Check if topic is older than 5 minutes
            time_diff = datetime.utcnow() - context.updated_at
            return time_diff > timedelta(minutes=5)
            
        except Exception as e:
            logger.error(f"🧹 CONTEXT: Error checking topic staleness: {e}")
            return True

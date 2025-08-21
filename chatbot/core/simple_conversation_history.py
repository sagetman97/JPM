"""
Simple Conversation History System

This module provides a lightweight conversation history system specifically for
conversation management queries (e.g., "what did we just talk about").
It stores the last 8 user messages and 8 bot responses without interfering
with the existing sophisticated memory system.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from openai import AsyncOpenAI
import json

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """A single conversation turn with user message and bot response"""
    user_message: str
    bot_response: str
    timestamp: datetime
    turn_number: int

class SimpleConversationHistory:
    """
    Lightweight conversation history system for conversation management queries.
    
    This system:
    - Stores last 8 user messages + 8 bot responses
    - Only activates for conversation management intent
    - Doesn't interfere with existing RAG conversation history
    - Uses simple data structures for reliability
    - Now uses LLM for better response quality
    """
    
    def __init__(self, max_history: int = 8, llm_client: Optional[AsyncOpenAI] = None):
        self.max_history = max_history
        self.conversation_turns: List[ConversationTurn] = []
        self.turn_counter = 0
        self.llm_client = llm_client
        
        # Fallback responses if LLM is not available
        self._fallback_responses = {
            "summary": "We've been discussing life insurance and financial planning topics. You've asked several questions and I've been providing information to help you understand these concepts better.",
            "detailed": "We've covered various life insurance topics including different types of policies, how they work, and their benefits. I've been answering your questions to help you make informed decisions about your financial planning.",
            "main_topic": "We've been focusing on life insurance education and understanding different products and their features. This has been the main theme of our conversation.",
            "generic": "We've been having a conversation about life insurance and financial planning. I've been providing information and answering your questions to help you understand these important topics."
        }
    
    def set_llm_client(self, llm_client: AsyncOpenAI):
        """Set the LLM client for enhanced responses"""
        self.llm_client = llm_client
        logger.info("📝 SIMPLE HISTORY: LLM client set for enhanced responses")
    
    async def _generate_llm_response(self, prompt: str, conversation_context: str) -> str:
        """Generate an LLM-enhanced response"""
        if not self.llm_client:
            logger.warning("📝 SIMPLE HISTORY: No LLM client available, using fallback")
            return None
            
        try:
            full_prompt = f"""
            {prompt}
            
            **Conversation Context:**
            {conversation_context}
            
            **Instructions:**
            - Provide a natural, conversational summary
            - Be specific about what was discussed
            - Reference the actual topics and questions asked
            - Keep it concise but informative (2-3 sentences)
            - Use a friendly, helpful tone
            - Don't be generic - reference specific content from the conversation
            
            **Response:**
            """
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error generating LLM response: {e}")
            return None
    
    def add_conversation_turn(self, user_message: str, bot_response: str) -> None:
        """Add a new conversation turn to the history"""
        try:
            logger.info(f"📝 SIMPLE HISTORY: Adding conversation turn - Turn #{self.turn_counter + 1}")
            logger.info(f"📝 SIMPLE HISTORY: User message preview: '{user_message[:50]}...'")
            logger.info(f"📝 SIMPLE HISTORY: Bot response preview: '{bot_response[:50]}...'")
            
            # Create new turn
            turn = ConversationTurn(
                user_message=user_message,
                bot_response=bot_response,
                timestamp=datetime.now(),
                turn_number=self.turn_counter + 1
            )
            
            # Add to history
            self.conversation_turns.append(turn)
            self.turn_counter += 1
            
            # Maintain max history size
            if len(self.conversation_turns) > self.max_history:
                removed_turn = self.conversation_turns.pop(0)
                logger.info(f"📝 SIMPLE HISTORY: Removed old turn #{removed_turn.turn_number} to maintain max history size")
            
            logger.info(f"📝 SIMPLE HISTORY: Successfully added conversation turn {turn.turn_number}, total turns: {len(self.conversation_turns)}")
            logger.info(f"📝 SIMPLE HISTORY: Current history size: {len(self.conversation_turns)}/{self.max_history}")
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error adding conversation turn: {e}")
            import traceback
            logger.error(f"📝 SIMPLE HISTORY: Full traceback: {traceback.format_exc()}")
    
    async def get_conversation_summary(self) -> str:
        """Generate a conversation summary using LLM if available, fallback otherwise"""
        try:
            if not self.conversation_turns:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Count turns
            total_turns = len(self.conversation_turns)
            logger.info(f"📝 SIMPLE HISTORY: Processing {total_turns} conversation turns")
            
            # Get recent topics from user messages
            recent_topics = []
            for turn in self.conversation_turns[-3:]:  # Last 3 turns
                topic = self._extract_topic(turn.user_message)
                if topic and topic not in recent_topics:
                    recent_topics.append(topic)
            
            logger.info(f"📝 SIMPLE HISTORY: Extracted recent topics: {recent_topics}")
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = f"Summarize what we've been discussing in our conversation. We've covered {total_turns} topics/questions."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced summary: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based summary if LLM fails or unavailable
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based summary")
            
            # Generate summary based on conversation length
            if total_turns == 1:
                topic = recent_topics[0] if recent_topics else "life insurance topics"
                summary = f"We just talked about {topic}. You asked about {self.conversation_turns[0].user_message[:100]}..."
                logger.info(f"📝 SIMPLE HISTORY: Generated single turn summary: {summary[:100]}...")
                return summary
            
            elif total_turns <= 3:
                topics = ", ".join(recent_topics) if recent_topics else "life insurance and financial planning"
                summary = f"We've been discussing {topics}. You've asked {total_turns} questions so far."
                logger.info(f"📝 SIMPLE HISTORY: Generated few turns summary: {summary[:100]}...")
                return summary
            
            else:
                main_topics = ", ".join(recent_topics[-2:]) if len(recent_topics) >= 2 else (recent_topics[0] if recent_topics else "life insurance topics")
                summary = f"We've been having a conversation about {main_topics}. We've covered several topics and you've asked {total_turns} questions so far."
                logger.info(f"📝 SIMPLE HISTORY: Generated many turns summary: {summary[:100]}...")
                return summary
                
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error generating conversation summary: {e}")
            import traceback
            logger.error(f"📝 SIMPLE HISTORY: Full traceback: {traceback.format_exc()}")
            return self._fallback_responses["summary"]
    
    def _build_conversation_context(self) -> str:
        """Build conversation context for LLM prompts"""
        if not self.conversation_turns:
            return "No conversation history available."
        
        context_parts = []
        for i, turn in enumerate(self.conversation_turns[-4:], 1):  # Last 4 turns
            context_parts.append(f"Turn {i}:")
            context_parts.append(f"  You: {turn.user_message}")
            context_parts.append(f"  Me: {turn.bot_response[:200]}...")  # Truncate long responses
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def get_detailed_summary(self) -> str:
        """Generate a detailed summary of the conversation using LLM if available"""
        try:
            if not self.conversation_turns:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = "Provide a detailed summary of our conversation, highlighting the main topics discussed and key questions asked."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced detailed summary: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based detailed summary
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based detailed summary")
            
            summary_parts = []
            summary_parts.append("Here's a summary of our conversation:")
            
            # Group by topics
            topic_groups = {}
            for turn in self.conversation_turns:
                topic = self._extract_topic(turn.user_message) or "General Discussion"
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(turn)
            
            # Build summary by topics
            for topic, turns in topic_groups.items():
                summary_parts.append(f"\n**{topic}:**")
                for turn in turns:
                    user_q = turn.user_message[:100] + "..." if len(turn.user_message) > 100 else turn.user_message
                    summary_parts.append(f"- You asked: {user_q}")
            
            summary_parts.append(f"\n**Total Questions:** {len(self.conversation_turns)}")
            
            # Get current focus
            if self.conversation_turns:
                current_topic = self._extract_topic(self.conversation_turns[-1].user_message)
                summary_parts.append(f"**Current Focus:** {current_topic or 'Life Insurance Education'}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error generating detailed summary: {e}")
            return self._fallback_responses["detailed"]
    
    async def get_main_topic(self) -> str:
        """Get the main topic of the conversation using LLM if available"""
        try:
            if not self.conversation_turns:
                return "We haven't focused on a specific topic yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = "What is the main topic we've been discussing in our conversation? Provide a clear, specific answer."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced main topic response: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based main topic
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based main topic")
            
            # Find the most common topic
            topic_counts = {}
            for turn in self.conversation_turns:
                topic = self._extract_topic(turn.user_message)
                if topic:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
            if topic_counts:
                main_topic = max(topic_counts, key=topic_counts.get)
                return f"The main topic we've been discussing is **{main_topic}**. This has been the focus of our conversation, and I've been providing information and answering your questions about it."
            else:
                return "We've been discussing life insurance topics, but I'm having trouble identifying the specific focus. What would you like to know more about?"
                
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error getting main topic: {e}")
            return self._fallback_responses["main_topic"]
    
    async def get_last_response(self) -> str:
        """Get the last response using LLM if available"""
        try:
            if not self.conversation_turns:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            last_turn = self.conversation_turns[-1]
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = f"Repeat what I just said about '{self._extract_topic(last_turn.user_message) or 'the topic'}' in a clear, helpful way."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced last response: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based last response
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based last response")
            
            topic = self._extract_topic(last_turn.user_message) or "the topic"
            return f"I just explained about {topic}. Here's what I said: {last_turn.bot_response[:200]}..."
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error getting last response: {e}")
            return "I'm having trouble accessing our last conversation. Could you please rephrase your question?"
    
    async def get_conversation_metrics(self) -> str:
        """Get conversation metrics using LLM if available"""
        try:
            if not self.conversation_turns:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = f"Provide a brief summary of our conversation metrics: {len(self.conversation_turns)} questions asked, topics covered, and conversation flow."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced metrics response: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based metrics
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based metrics")
            
            total_turns = len(self.conversation_turns)
            recent_topics = []
            for turn in self.conversation_turns[-3:]:
                topic = self._extract_topic(turn.user_message)
                if topic and topic not in recent_topics:
                    recent_topics.append(topic)
            
            topics_text = ", ".join(recent_topics) if recent_topics else "life insurance topics"
            return f"We've been talking for a while! You've asked {total_turns} questions, and we've covered {topics_text}. The conversation has been flowing naturally as you explore different aspects of life insurance and financial planning."
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error getting conversation metrics: {e}")
            return self._fallback_responses["generic"]
    
    async def get_generic_response(self) -> str:
        """Get a generic conversation management response using LLM if available"""
        try:
            if not self.conversation_turns:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Try to generate LLM-enhanced response
            if self.llm_client:
                conversation_context = self._build_conversation_context()
                prompt = "Provide a helpful, conversational response about our conversation. Be specific about what we've discussed and offer to help with more questions."
                
                llm_response = await self._generate_llm_response(prompt, conversation_context)
                if llm_response:
                    logger.info(f"📝 SIMPLE HISTORY: Generated LLM-enhanced generic response: {llm_response[:100]}...")
                    return llm_response
            
            # Fallback to rule-based generic response
            logger.info("📝 SIMPLE HISTORY: Using fallback rule-based generic response")
            
            total_turns = len(self.conversation_turns)
            recent_topics = []
            for turn in self.conversation_turns[-2:]:
                topic = self._extract_topic(turn.user_message)
                if topic and topic not in recent_topics:
                    recent_topics.append(topic)
            
            topics_text = ", ".join(recent_topics) if recent_topics else "life insurance topics"
            return f"We've been having a great conversation about {topics_text}! You've asked {total_turns} questions, and I've been providing information to help you understand these important financial topics. Is there something specific you'd like me to clarify or expand on?"
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error getting generic response: {e}")
            return self._fallback_responses["generic"]
    
    def _extract_topic(self, message: str) -> Optional[str]:
        """Extract the main topic from a user message"""
        try:
            message_lower = message.lower()
            
            # Check for insurance product mentions
            insurance_products = [
                'iul', 'indexed universal life', 'universal life', 'whole life', 
                'term life', 'variable life', 'variable universal life'
            ]
            
            for product in insurance_products:
                if product in message_lower:
                    return product.title()
            
            # Check for general insurance concepts
            if any(term in message_lower for term in ['insurance', 'coverage', 'policy', 'premium']):
                return "Life Insurance"
            
            # Check for calculator-related queries
            if any(term in message_lower for term in ['calculate', 'need', 'amount', 'coverage']):
                return "Insurance Calculation"
            
            # Check for financial planning
            if any(term in message_lower for term in ['planning', 'financial', 'investment', 'portfolio']):
                return "Financial Planning"
            
            return None
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error extracting topic: {e}")
            return None
    
    def clear_history(self) -> None:
        """Clear the conversation history (useful for testing or privacy)"""
        try:
            self.conversation_turns.clear()
            self.turn_counter = 0
            logger.info("📝 SIMPLE HISTORY: Conversation history cleared")
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error clearing history: {e}")
    
    def get_history_stats(self) -> Dict[str, Any]:
        """Get statistics about the conversation history"""
        try:
            stats = {
                "total_turns": len(self.conversation_turns),
                "turn_counter": self.turn_counter,
                "max_history": self.max_history,
                "has_history": len(self.conversation_turns) > 0,
                "oldest_turn": self.conversation_turns[0].timestamp if self.conversation_turns else None,
                "newest_turn": self.conversation_turns[-1].timestamp if self.conversation_turns else None
            }
            
            logger.info(f"📝 SIMPLE HISTORY: Generated history stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"📝 SIMPLE HISTORY: Error getting history stats: {e}")
            import traceback
            logger.error(f"📝 SIMPLE HISTORY: Full traceback: {traceback.format_exc()}")
            return {"error": str(e)}

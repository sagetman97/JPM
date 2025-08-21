"""
Conversation Memory System

This module provides true conversation memory and context understanding
for the chatbot system, enabling ChatGPT-like conversational abilities.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """Types of memory items"""
    TOPIC = "topic"
    ENTITY = "entity"
    CONCEPT = "concept"
    RELATIONSHIP = "relationship"
    USER_INTENT = "user_intent"
    SYSTEM_RESPONSE = "system_response"

@dataclass
class MemoryItem:
    """A single memory item"""
    id: str
    type: MemoryType
    content: str
    confidence: float
    created_at: datetime
    accessed_at: datetime
    access_count: int
    related_items: List[str]  # IDs of related memory items
    metadata: Dict[str, Any]

class ConversationMemory:
    """
    True conversation memory system that maintains context across multiple turns.
    
    This system provides:
    - Persistent conversation state
    - Semantic memory of topics and concepts
    - Relationship mapping between concepts
    - Context-aware query understanding
    - Long-term conversation memory
    """
    
    def __init__(self, max_memory_items: int = 100, memory_ttl_hours: int = 24):
        self.max_memory_items = max_memory_items
        self.memory_ttl_hours = memory_ttl_hours
        self.memory_items: Dict[str, MemoryItem] = {}
        self.conversation_flow: List[str] = []  # Ordered list of memory item IDs
        self.current_topic: Optional[str] = None
        self.current_entities: List[str] = []
        
    def add_memory_item(self, memory_type: MemoryType, content: str, 
                        confidence: float = 1.0, metadata: Dict[str, Any] = None) -> str:
        """Add a new memory item"""
        try:
            memory_id = f"{memory_type.value}_{len(self.memory_items)}_{datetime.now().timestamp()}"
            
            memory_item = MemoryItem(
                id=memory_id,
                type=memory_type,
                content=content,
                confidence=confidence,
                created_at=datetime.now(),
                accessed_at=datetime.now(),
                access_count=1,
                related_items=[],
                metadata=metadata or {}
            )
            
            self.memory_items[memory_id] = memory_item
            self.conversation_flow.append(memory_id)
            
            # Update current topic if this is a topic memory
            if memory_type == MemoryType.TOPIC:
                self.current_topic = content
            
            # Cleanup old memory items
            self._cleanup_old_memory()
            
            logger.info(f"🧠 MEMORY: Added {memory_type.value} memory: {content[:50]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error adding memory item: {e}")
            return ""
    
    def find_relevant_memory(self, query: str, memory_types: List[MemoryType] = None, 
                            min_confidence: float = 0.5) -> List[MemoryItem]:
        """Find memory items relevant to a query"""
        try:
            if not memory_types:
                memory_types = list(MemoryType)
            
            relevant_items = []
            query_lower = query.lower()
            
            for memory_item in self.memory_items.values():
                if memory_item.type not in memory_types:
                    continue
                
                if memory_item.confidence < min_confidence:
                    continue
                
                # Check if memory item is relevant to query
                relevance_score = self._calculate_relevance(memory_item, query_lower)
                if relevance_score > 0.3:  # Threshold for relevance
                    memory_item.accessed_at = datetime.now()
                    memory_item.access_count += 1
                    relevant_items.append(memory_item)
            
            # Sort by relevance and recency
            relevant_items.sort(key=lambda x: (x.access_count, x.accessed_at), reverse=True)
            
            logger.info(f"🧠 MEMORY: Found {len(relevant_items)} relevant memory items for query: {query[:50]}...")
            return relevant_items
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error finding relevant memory: {e}")
            return []
    
    def get_conversation_context(self, max_items: int = 10) -> Dict[str, Any]:
        """Get current conversation context for response generation"""
        try:
            # Get recent memory items
            recent_items = self.conversation_flow[-max_items:] if self.conversation_flow else []
            
            context = {
                "current_topic": self.current_topic,
                "current_entities": self.current_entities,
                "recent_topics": [],
                "recent_concepts": [],
                "recent_entities": [],
                "conversation_summary": ""
            }
            
            # Build context from recent memory
            for item_id in recent_items:
                if item_id in self.memory_items:
                    memory_item = self.memory_items[item_id]
                    
                    if memory_item.type == MemoryType.TOPIC:
                        context["recent_topics"].append(memory_item.content)
                    elif memory_item.type == MemoryType.CONCEPT:
                        context["recent_concepts"].append(memory_item.content)
                    elif memory_item.type == MemoryType.ENTITY:
                        context["recent_entities"].append(memory_item.content)
            
            # Generate conversation summary
            context["conversation_summary"] = self._generate_conversation_summary(recent_items)
            
            logger.info(f"🧠 MEMORY: Generated conversation context with {len(recent_items)} recent items")
            return context
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error getting conversation context: {e}")
            return {}
    
    def understand_follow_up(self, query: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Understand if a query is a follow-up and what it refers to.
        
        Returns:
            - is_follow_up: bool
            - main_topic: Optional[str] - what the follow-up refers to
            - related_concepts: List[str] - concepts related to the follow-up
        """
        try:
            # Check for follow-up indicators
            follow_up_indicators = [
                'go deeper', 'tell me more', 'explain', 'how does', 'what about',
                'can you', 'could you', 'expand on', 'elaborate', 'dive into',
                'restate', 'repeat', 'say that again', 'clarify', 'what do you mean',
                'i don\'t understand', 'confused', 'lost me', 'help me understand',
                'more about', 'more on', 'further', 'additional', 'extra',
                'that', 'this', 'it', 'they', 'them', 'those', 'these'
            ]
            
            query_lower = query.lower()
            is_follow_up = any(indicator in query_lower for indicator in follow_up_indicators)
            
            if not is_follow_up:
                return False, None, []
            
            # Find what this follow-up refers to
            main_topic = self.current_topic
            related_concepts = []
            
            if main_topic:
                # Find concepts related to the main topic
                topic_memories = [item for item in self.memory_items.values() 
                                if item.type == MemoryType.CONCEPT and 
                                self._calculate_relevance(item, main_topic.lower()) > 0.5]
                
                related_concepts = [item.content for item in topic_memories[:5]]
            
            logger.info(f"🧠 MEMORY: Follow-up detected - refers to: {main_topic}, concepts: {related_concepts}")
            return True, main_topic, related_concepts
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error understanding follow-up: {e}")
            return False, None, []
    
    def add_conversation_turn(self, user_query: str, system_response: str, 
                             intent: str = None, entities: List[str] = None):
        """Add a complete conversation turn to memory"""
        try:
            # Add user query as concept
            query_memory_id = self.add_memory_item(
                MemoryType.CONCEPT,
                user_query,
                metadata={"intent": intent, "entities": entities}
            )
            
            # Add system response
            response_memory_id = self.add_memory_item(
                MemoryType.SYSTEM_RESPONSE,
                system_response,
                metadata={"in_response_to": query_memory_id}
            )
            
            # Link the memories
            if query_memory_id and response_memory_id:
                self.memory_items[query_memory_id].related_items.append(response_memory_id)
                self.memory_items[response_memory_id].related_items.append(query_memory_id)
            
            # Extract and store entities
            if entities:
                for entity in entities:
                    self.add_memory_item(
                        MemoryType.ENTITY,
                        entity,
                        metadata={"source_query": query_memory_id}
                    )
            
            # NEW: Extract and set current topic from the conversation
            extracted_topic = self._extract_topic_from_conversation(user_query, system_response, intent)
            if extracted_topic:
                self.current_topic = extracted_topic
                # Also add as a topic memory item
                self.add_memory_item(
                    MemoryType.TOPIC,
                    extracted_topic,
                    metadata={"source_query": query_memory_id, "intent": intent}
                )
                logger.info(f"🧠 MEMORY: Set current topic: {extracted_topic}")
            
            logger.info(f"🧠 MEMORY: Added conversation turn - query: {user_query[:50]}..., response: {system_response[:50]}...")
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error adding conversation turn: {e}")
    
    def _extract_topic_from_conversation(self, user_query: str, system_response: str, intent: str = None) -> Optional[str]:
        """Extract the main topic from a conversation turn"""
        try:
            query_lower = user_query.lower()
            
            # Check for insurance product mentions
            insurance_products = [
                'iul', 'indexed universal life', 'universal life', 'whole life', 
                'term life', 'variable life', 'variable universal life'
            ]
            
            for product in insurance_products:
                if product in query_lower:
                    return product.title()
            
            # Check for general insurance concepts
            if any(term in query_lower for term in ['insurance', 'coverage', 'policy', 'premium']):
                if intent and 'education' in intent.lower():
                    return "Life Insurance Education"
                elif intent and 'calculation' in intent.lower():
                    return "Insurance Calculation"
                else:
                    return "Insurance Information"
            
            # Check for calculator-related queries
            if any(term in query_lower for term in ['calculate', 'need', 'amount', 'coverage']):
                return "Insurance Calculation"
            
            # Default topic based on intent
            if intent:
                if 'education' in intent.lower():
                    return "Financial Education"
                elif 'calculation' in intent.lower():
                    return "Financial Calculation"
                else:
                    return intent.replace('_', ' ').title()
            
            return None
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error extracting topic: {e}")
            return None
    
    def _calculate_relevance(self, memory_item: MemoryItem, query: str) -> float:
        """Calculate relevance between a memory item and a query"""
        try:
            # Simple word overlap for now - can be enhanced with embeddings later
            memory_words = set(memory_item.content.lower().split())
            query_words = set(query.split())
            
            if not memory_words or not query_words:
                return 0.0
            
            overlap = len(memory_words.intersection(query_words))
            total = len(memory_words.union(query_words))
            
            return overlap / total if total > 0 else 0.0
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error calculating relevance: {e}")
            return 0.0
    
    def _generate_conversation_summary(self, recent_item_ids: List[str]) -> str:
        """Generate a summary of recent conversation"""
        try:
            if not recent_item_ids:
                return "No recent conversation context."
            
            # Get recent topics and concepts
            topics = []
            concepts = []
            
            for item_id in recent_item_ids[-5:]:  # Last 5 items
                if item_id in self.memory_items:
                    memory_item = self.memory_items[item_id]
                    if memory_item.type == MemoryType.TOPIC:
                        topics.append(memory_item.content)
                    elif memory_item.type == MemoryType.CONCEPT:
                        concepts.append(memory_item.content)
            
            summary_parts = []
            if topics:
                summary_parts.append(f"Recent topics: {', '.join(topics[-3:])}")
            if concepts:
                summary_parts.append(f"Recent concepts: {', '.join(concepts[-3:])}")
            
            return "; ".join(summary_parts) if summary_parts else "Conversation in progress."
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating conversation summary: {e}")
            return "Conversation context available."
    
    def _cleanup_old_memory(self):
        """Remove old memory items to prevent memory overflow"""
        try:
            if len(self.memory_items) <= self.max_memory_items:
                return
            
            # Remove oldest items
            items_to_remove = len(self.memory_items) - self.max_memory_items
            
            # Sort by access count and recency
            sorted_items = sorted(
                self.memory_items.values(),
                key=lambda x: (x.access_count, x.created_at)
            )
            
            for item in sorted_items[:items_to_remove]:
                del self.memory_items[item.id]
                if item.id in self.conversation_flow:
                    self.conversation_flow.remove(item.id)
            
            logger.info(f"🧠 MEMORY: Cleaned up {items_to_remove} old memory items")
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error cleaning up old memory: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        try:
            return {
                "total_memory_items": len(self.memory_items),
                "memory_types": {memory_type.value: len([item for item in self.memory_items.values() if item.memory_type == memory_type]) for memory_type in MemoryType},
                "conversation_flow_length": len(self.conversation_flow),
                "current_topic": self.current_topic,
                "recent_topics": self.recent_topics[-5:] if self.recent_topics else [],
                "conversation_summary": self._generate_conversation_summary()
            }
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error getting memory stats: {e}")
            return {}

    def handle_conversation_management_query(self, query: str) -> str:
        """Handle conversation management queries like 'what did we just talk about'"""
        try:
            query_lower = query.lower()
            
            # Check for different types of conversation management queries
            if any(phrase in query_lower for phrase in ["what did we just talk about", "what were we discussing", "what was our conversation about"]):
                return self._get_conversation_summary_response()
            
            elif any(phrase in query_lower for phrase in ["summarize", "summary", "recap", "what have we covered"]):
                return self._get_detailed_conversation_summary()
            
            elif any(phrase in query_lower for phrase in ["what was the main topic", "what topic were we on", "what were we focusing on"]):
                return self._get_main_topic_response()
            
            elif any(phrase in query_lower for phrase in ["repeat", "restate", "say again", "what did you say about"]):
                return self._get_last_response_repeat(query)
            
            elif any(phrase in query_lower for phrase in ["how long have we been talking", "how many questions", "conversation length"]):
                return self._get_conversation_metrics()
            
            else:
                # Generic conversation management response
                return self._get_generic_conversation_response()
                
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error handling conversation management query: {e}")
            return "I'm having trouble accessing our conversation history right now. Could you please rephrase your question?"
    
    def _get_conversation_summary_response(self) -> str:
        """Generate a natural response about what was discussed"""
        try:
            if not self.conversation_flow:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            # Get the most recent conversation turn
            last_turn = self.conversation_flow[-1]
            current_topic = self.current_topic or "life insurance and financial planning"
            
            # Count conversation turns
            turn_count = len(self.conversation_flow)
            
            # Get recent topics
            recent_topics = self.recent_topics[-3:] if self.recent_topics else []
            
            if turn_count == 1:
                return f"We just talked about {current_topic.lower()}. Specifically, you asked about {last_turn.get('user_query', 'life insurance topics')}."
            
            elif turn_count == 2:
                return f"We've been discussing {current_topic.lower()}. You started by asking about {self.conversation_flow[0].get('user_query', 'life insurance')}, and then we explored {last_turn.get('user_query', 'related topics')}."
            
            else:
                topic_summary = ", ".join(recent_topics[-3:]) if recent_topics else current_topic.lower()
                return f"We've been having a conversation about {topic_summary}. We've covered several topics including {current_topic.lower()}, and you've asked {turn_count} questions so far."
                
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating conversation summary response: {e}")
            return "We've been discussing life insurance and financial planning topics. Is there something specific you'd like me to clarify or expand on?"
    
    def _get_detailed_conversation_summary(self) -> str:
        """Generate a detailed summary of the conversation"""
        try:
            if not self.conversation_flow:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            summary_parts = []
            summary_parts.append("Here's a summary of our conversation:")
            
            # Group by topics
            topic_groups = {}
            for turn in self.conversation_flow:
                topic = turn.get('topic', 'General Discussion')
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(turn)
            
            for topic, turns in topic_groups.items():
                summary_parts.append(f"\n**{topic}:**")
                for turn in turns:
                    user_q = turn.get('user_query', '')[:100] + "..." if len(turn.get('user_query', '')) > 100 else turn.get('user_query', '')
                    summary_parts.append(f"- You asked: {user_q}")
            
            summary_parts.append(f"\n**Total Questions:** {len(self.conversation_flow)}")
            summary_parts.append(f"**Current Focus:** {self.current_topic or 'Life Insurance Education'}")
            
            return "\n".join(summary_parts)
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating detailed conversation summary: {e}")
            return "I'm having trouble generating a detailed summary, but we've been discussing life insurance topics. Is there something specific you'd like me to clarify?"
    
    def _get_main_topic_response(self) -> str:
        """Generate a response about the main topic"""
        try:
            if not self.current_topic:
                return "We haven't focused on a specific topic yet. I'm here to help you with life insurance and financial planning questions!"
            
            return f"The main topic we've been discussing is **{self.current_topic}**. This has been the focus of our conversation, and I've been providing information and answering your questions about it."
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating main topic response: {e}")
            return "We've been discussing life insurance topics, but I'm having trouble identifying the specific focus. What would you like to know more about?"
    
    def _get_last_response_repeat(self, query: str) -> str:
        """Generate a response repeating the last assistant response"""
        try:
            if not self.conversation_flow:
                return "We haven't had a conversation yet, so there's nothing to repeat."
            
            # Find the last assistant response
            for turn in reversed(self.conversation_flow):
                if turn.get('system_response'):
                    return f"Here's what I said about {self.current_topic or 'the topic'}: {turn['system_response']}"
            
            return "I don't have a previous response to repeat. What would you like to know about?"
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating last response repeat: {e}")
            return "I'm having trouble accessing my previous response. Could you please ask your question again?"
    
    def _get_conversation_metrics(self) -> str:
        """Generate a response with conversation metrics"""
        try:
            turn_count = len(self.conversation_flow)
            current_topic = self.current_topic or "life insurance and financial planning"
            
            if turn_count == 0:
                return "We haven't started our conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            elif turn_count == 1:
                return f"We've had 1 question so far, focusing on {current_topic.lower()}."
            
            else:
                return f"We've had {turn_count} questions in our conversation, covering topics related to {current_topic.lower()}. We've been discussing various aspects of life insurance and financial planning."
                
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating conversation metrics: {e}")
            return "We've been discussing life insurance topics, but I'm having trouble counting the exact number of questions. What would you like to know more about?"
    
    def _get_generic_conversation_response(self) -> str:
        """Generate a generic response for conversation management queries"""
        try:
            if not self.conversation_flow:
                return "We haven't had a conversation yet. I'm here to help you with life insurance and financial planning questions!"
            
            current_topic = self.current_topic or "life insurance and financial planning"
            turn_count = len(self.conversation_flow)
            
            return f"We've been discussing {current_topic.lower()}. You've asked {turn_count} question{'s' if turn_count != 1 else ''} so far, and I've been providing information and guidance on various aspects of life insurance and financial planning. Is there something specific you'd like me to clarify or expand on?"
            
        except Exception as e:
            logger.error(f"🧠 MEMORY: Error generating generic conversation response: {e}")
            return "We've been discussing life insurance topics. Is there something specific you'd like to know more about?"

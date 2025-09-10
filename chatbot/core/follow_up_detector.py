"""
Follow-up detection system for identifying when user queries are related to previous conversation turns.
This integrates with the existing SimpleConversationHistory system.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
import hashlib
import time

from .schemas import FollowUpResult

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    user_query: str
    assistant_response: str
    timestamp: float
    intent: Optional[str] = None
    topics: List[str] = None

class FollowUpDetector:
    """Detects follow-up questions by analyzing conversation history"""
    
    def __init__(self, llm_client: AsyncOpenAI, cache_ttl: int = 300):  # 5 minutes cache
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}  # Simple in-memory cache
        
        # Metrics tracking
        self._total_detections = 0
        self._successful_detections = 0
        self._cache_hits = 0
        self._confidence_scores = []
    
    def _get_cache_key(self, query: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Generate cache key for follow-up detection"""
        # Create a hash of the query and recent conversation history
        recent_turns = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        context_str = f"{query}|||{json.dumps(recent_turns, sort_keys=True)}"
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[FollowUpResult]:
        """Get cached follow-up detection result"""
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            # Check if cache is still valid
            if time.time() - cached_data.get('timestamp', 0) < self.cache_ttl:
                self.logger.debug(f"🔍 FOLLOW-UP DETECTOR: Using cached result for key: {cache_key[:8]}...")
                self._cache_hits += 1
                return cached_data.get('result')
            else:
                # Remove expired cache entry
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: FollowUpResult):
        """Cache follow-up detection result"""
        self._cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
        # Clean up old cache entries periodically
        if len(self._cache) > 100:  # Limit cache size
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
        self.logger.debug(f"🔍 FOLLOW-UP DETECTOR: Cleaned up {len(expired_keys)} expired cache entries")
    
    async def detect_follow_up(self, current_query: str, conversation_history: List[Dict[str, Any]]) -> FollowUpResult:
        """
        Detect if current query is a follow-up to previous conversation turns.
        
        Args:
            current_query: The user's current query
            conversation_history: List of conversation turns from SimpleConversationHistory
            
        Returns:
            FollowUpResult with detection results
        """
        try:
            # Track total detections
            self._total_detections += 1
            
            # Check cache first for performance optimization
            cache_key = self._get_cache_key(current_query, conversation_history)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.info("🔍 FOLLOW-UP DETECTOR: Using cached result for performance")
                return cached_result
            
            # If no history, not a follow-up
            if not conversation_history or len(conversation_history) < 1:
                result = FollowUpResult(
                    is_follow_up=False,
                    related_topics=[],
                    context_relevance=0.0,
                    suggested_context_window=1,
                    reasoning="No conversation history available",
                    confidence=0.0
                )
                self._cache_result(cache_key, result)
                return result
            
            # Get recent conversation turns (last 3-4 turns) - optimized for performance
            max_turns = min(4, len(conversation_history))
            recent_turns = conversation_history[-max_turns:] if conversation_history else []
            
            # Build conversation context for LLM analysis
            conversation_context = self._build_conversation_context(recent_turns)
            
            # Let LLM analyze all queries for better semantic understanding
            # No rule-based bypass - rely on LLM to distinguish new vs follow-up requests
            
            # Use LLM to analyze follow-up relationship
            follow_up_analysis = await self._analyze_follow_up_with_llm(current_query, conversation_context)
            
            # Extract topics from recent conversation
            related_topics = self._extract_related_topics(recent_turns, follow_up_analysis.get('related_topics', []))
            
            # Determine suggested context window based on relevance - optimized for performance
            suggested_context_window = self._determine_context_window(follow_up_analysis.get('context_relevance', 0.0), len(conversation_history))
            
            # Detect what the user is referring to using enhanced semantic matching
            referenced_item = await self._semantic_context_matching(current_query, recent_turns)
            
            result = FollowUpResult(
                is_follow_up=follow_up_analysis.get('is_follow_up', False),
                related_topics=related_topics,
                context_relevance=follow_up_analysis.get('context_relevance', 0.0),
                suggested_context_window=suggested_context_window,
                reasoning=follow_up_analysis.get('reasoning', ''),
                confidence=follow_up_analysis.get('confidence', 0.0),
                referenced_item=follow_up_analysis.get('referenced_item', referenced_item)
            )
            
            # Track successful detection and confidence
            if result.is_follow_up:
                self._successful_detections += 1
            self._confidence_scores.append(result.confidence)
            
            # Cache the result for performance optimization
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Error in follow-up detection: {e}")
            # Return a basic follow-up result instead of failing completely
            return FollowUpResult(
                is_follow_up=True,  # Assume it might be a follow-up if we can't determine
                related_topics=[],
                context_relevance=0.5,  # Medium relevance as fallback
                suggested_context_window=2,
                reasoning=f"Error in follow-up detection, assuming follow-up: {str(e)}",
                confidence=0.3,
                referenced_item=None
            )
    
    def _build_conversation_context(self, conversation_turns: List[Dict[str, Any]]) -> str:
        """Build conversation context string for LLM analysis"""
        context_parts = []
        
        for i, turn in enumerate(conversation_turns):
            user_query = turn.get('user_query', '')
            assistant_response = turn.get('assistant_response', '')
            
            if user_query and assistant_response:
                context_parts.append(f"Turn {i+1}:")
                context_parts.append(f"User: {user_query}")
                context_parts.append(f"Assistant: {assistant_response}")
                context_parts.append("")  # Empty line for separation
        
        return "\n".join(context_parts)
    
    async def _analyze_follow_up_with_llm(self, current_query: str, conversation_context: str) -> Dict[str, Any]:
        """Use LLM to analyze if current query is a follow-up"""
        
        prompt = f"""
You are analyzing whether a user's current query is a follow-up question related to previous conversation turns.

CONVERSATION HISTORY (most recent first):
{conversation_context}

CURRENT USER QUERY:
{current_query}

CRITICAL DISTINCTION: 
- FOLLOW-UP: User is asking about, clarifying, or expanding on something previously discussed
- NEW REQUEST: User is asking for something new, even if it relates to a previous topic

Analyze if the current query is a follow-up to any previous conversation turns. Consider:

        **FOLLOW-UP INDICATORS (is_follow_up = true):**
        1. Asking for clarification: "What does that mean?", "Can you explain that?"
        2. Asking for more details: "Tell me more about this", "Can you expand on this?"
        3. Asking about specific results: "What was my risk level?", "How did you calculate that?"
        4. Using pronouns: "this", "that", "it", "the report", "the analysis"
        5. Asking about previous recommendations: "What did you recommend?", "Why did you suggest that?"
        6. Vague follow-up questions: "Can you go more detail into this", "Tell me more about this"
        7. Questions about specific values from previous analysis: "What does that number mean?"
        8. **CRITICAL: Generic expansion requests after reports: "Can you expand on this", "Tell me more about this", "Go deeper into this"**
        9. **CRITICAL: Questions about recent analysis results: "What does this mean?", "Explain this better"**
        10. **CRITICAL: Single-word responses after calculator selection: "quick", "detailed", "portfolio" → NOT follow-up, but calculator choice**
        
        **IMPORTANT: Only classify as follow-up if the user is directly referencing something specific from the previous conversation.**

        **NEW REQUEST INDICATORS (is_follow_up = false):**
        1. Action verbs for new analysis: "I want to do", "I need to", "I would like to", "Can you do", "Please do"
        2. Starting new processes: "start", "begin", "create", "generate", "run", "perform"
        3. Requesting new analysis: "I want to do a portfolio analysis", "I need help with my portfolio"
        4. New questions about topics: "What is life insurance?", "How do I calculate my insurance needs?"
        5. General information requests: "Tell me about term life", "What are the benefits of IUL?"
        6. **CRITICAL: Calculator choice selection: "quick", "detailed", "portfolio" after calculator selection → NOT follow-up, but calculator choice**
        7. **CRITICAL: Single word responses: "quick", "detailed", "portfolio" → NOT follow-up, but calculator choice**
        8. **CRITICAL: Calculator type selection: "I want quick", "I want detailed", "I want portfolio" → NOT follow-up, but calculator choice**
        9. **CRITICAL: General educational questions: "How do death benefits work?", "What is term life?" → NOT follow-up, but new educational requests**

        **REFERENCE IDENTIFICATION:**
        - Look at the MOST RECENT bot response first
        - If it contains structured data (reports, analysis, calculations), that's likely the reference
        - If it's about a specific topic (IUL, term life, etc.), that's the reference
        - For vague follow-up questions, assume they're referring to the MOST RECENT bot response
        
        **CALCULATOR RESULTS IDENTIFICATION:**
        - If the most recent response contains "COVERAGE ANALYSIS", "Coverage Needed", "Product Recommendation", "CASH VALUE SAVINGS", "Coverage Gap", "About You" section → use "calculation"
        - If the most recent response contains "COVERAGE BREAKDOWN", "Living Expenses", "Debts", "Education", "Funeral", "Legacy" → use "calculation"
        - If the most recent response contains "NEXT STEPS", "DISCLAIMERS" with coverage recommendations → use "calculation"
        - If the most recent response contains portfolio data, investment analysis, asset allocation → use "portfolio_report"
        - If the most recent response is general educational content about insurance → use "general_discussion"

Respond with a JSON object containing:
{{
    "is_follow_up": boolean,
    "context_relevance": float (0.0 to 1.0),
    "related_topics": ["topic1", "topic2", ...],
    "reasoning": "explanation of what the user is referring to and why this is or isn't a follow-up",
    "confidence": float (0.0 to 1.0),
    "referenced_item": "portfolio_report|calculation|analysis|general_discussion|etc"
}}

**EXAMPLES OF FOLLOW-UP QUESTIONS (is_follow_up = true):**
- "Can you explain to me in that portfolio report what the recommended coverage was?" (asking about previous analysis)
- "What does that mean?" (asking for clarification about previous response)
- "How did you calculate that?" (asking about previous calculation)
- "What was my risk level?" (asking about previous assessment)
- "Can you tell me more about that product?" (asking about previous recommendation)
- "Can you break this down for me in more detail" (asking about previous report/analysis)
- "What does that number mean?" (asking about specific values from previous analysis)
- "Can you explain the recommendations?" (asking about previous recommendations)
- "Can you go more detail into this?" (vague follow-up - about most recent response)
- "Tell me more about this" (vague follow-up - about most recent response)
- "What about this?" (vague follow-up - about most recent response)
- "Can you elaborate on this?" (vague follow-up - about most recent response)
- "Can you explain this better?" (vague follow-up - about most recent response)

**EXAMPLES OF NEW REQUESTS (is_follow_up = false):**
- "What is life insurance?" (new topic question)
- "I want to do a portfolio analysis" (new analysis request)
- "I need help with my portfolio" (new help request)
- "How do I calculate my insurance needs?" (new calculation question)
- "Can you do a quick assessment?" (new assessment request)
- "I would like to start a detailed analysis" (new analysis request)
- "Please generate a report" (new report request)
- "Tell me about term life insurance" (new information request)
"""

        try:
            import json
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing conversation flow and identifying follow-up questions. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            self.logger.info(f"🔍 FOLLOW-UP DETECTOR: Raw LLM response: {content}")
            
            # Try to parse JSON
            result = json.loads(content)
            self.logger.info(f"🔍 FOLLOW-UP DETECTOR: Parsed result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"🔍 FOLLOW-UP DETECTOR: JSON decode error: {e}")
            self.logger.error(f"🔍 FOLLOW-UP DETECTOR: Raw content: {response.choices[0].message.content}")
            return {
                "is_follow_up": False,
                "context_relevance": 0.0,
                "related_topics": [],
                "reasoning": f"JSON parsing error: {str(e)}",
                "confidence": 0.0,
                "referenced_item": None
            }
        except Exception as e:
            self.logger.error(f"🔍 FOLLOW-UP DETECTOR: Error in LLM follow-up analysis: {e}")
            return {
                "is_follow_up": False,
                "context_relevance": 0.0,
                "related_topics": [],
                "reasoning": f"Error in LLM analysis: {str(e)}",
                "confidence": 0.0,
                "referenced_item": None
            }
    
    def _extract_related_topics(self, conversation_turns: List[Dict[str, Any]], llm_topics: List[str]) -> List[str]:
        """Extract and combine topics from conversation history and LLM analysis"""
        topics = set()
        
        # Add topics from LLM analysis
        topics.update(llm_topics)
        
        # Extract topics from conversation turns
        for turn in conversation_turns:
            user_query = turn.get('user_query', '').lower()
            assistant_response = turn.get('assistant_response', '').lower()
            
            # Look for key financial topics
            financial_keywords = [
                'portfolio', 'insurance', 'coverage', 'life insurance', 'term life', 'whole life',
                'investment', 'retirement', 'savings', 'assets', 'liabilities', 'risk',
                'calculation', 'analysis', 'report', 'recommendation', 'product'
            ]
            
            for keyword in financial_keywords:
                if keyword in user_query or keyword in assistant_response:
                    topics.add(keyword)
        
        return list(topics)
    
    def _determine_context_window(self, context_relevance: float, max_available: int = 10) -> int:
        """Determine suggested context window based on relevance score and follow-up type - optimized for performance"""
        # Enhanced context window selection for better follow-up handling with performance limits
        if context_relevance >= 0.9:
            return min(6, max_available)  # Very high relevance - use extensive context
        elif context_relevance >= 0.8:
            return min(5, max_available)  # High relevance - use more context
        elif context_relevance >= 0.7:
            return min(4, max_available)  # Good relevance - use moderate context
        elif context_relevance >= 0.6:
            return min(3, max_available)  # Medium relevance - use moderate context
        elif context_relevance >= 0.4:
            return min(2, max_available)  # Low relevance - use minimal context
        else:
            return min(1, max_available)  # Very low relevance - use minimal context
    
    def _detect_referenced_item(self, current_query: str, recent_turns: List[Dict[str, Any]]) -> Optional[str]:
        """Detect what the user is referring to in their follow-up question"""
        if not recent_turns:
            return None
        
        # Check for vague follow-up indicators
        vague_indicators = [
            'can you go more detail into this', 'tell me more about this', 'what about this',
            'can you elaborate on this', 'i want to know more about this', 'can you explain this better',
            'go more detail', 'more detail', 'elaborate', 'explain this', 'tell me more',
            'can you summarize this', 'summarize this file', 'break down this', 'explain this better'
        ]
        
        is_vague_follow_up = any(indicator in current_query.lower() for indicator in vague_indicators)
        
        # PRIORITY 1: Check most recent response first (highest priority for vague follow-ups)
        most_recent_response = recent_turns[-1].get('assistant_response', '').lower()
        most_recent_user_query = recent_turns[-1].get('user_query', '').lower()
        
        # For vague follow-ups, prioritize the most recent response
        if is_vague_follow_up:
            # Check if most recent response contains structured data (portfolio reports, etc.)
            if self._contains_structured_data(most_recent_response):
                return "portfolio_report"
            # Check if most recent response contains calculations
            elif any(keyword in most_recent_response for keyword in ['calculated', 'calculation', 'computed', 'result', 'coverage needs']):
                return "calculation"
            # Check if most recent response contains analysis
            elif any(keyword in most_recent_response for keyword in ['analysis', 'analyzed', 'assessment', 'evaluation']):
                return "analysis"
            # Check if most recent user query was about file upload
            elif any(keyword in most_recent_user_query for keyword in ['upload', 'file', 'document', 'pdf', 'estate planning', 'will', 'trust']):
                return "file_upload"
            else:
                return "general_discussion"
        
        # PRIORITY 2: Check for specific query indicators that override recent context
        query_lower = current_query.lower()
        
        # If user explicitly mentions "file", prioritize file context
        if any(keyword in query_lower for keyword in ['file', 'document', 'pdf', 'upload']):
            # Look for file upload in recent turns
            for turn in reversed(recent_turns[-3:]):
                user_query = turn.get('user_query', '').lower()
                if any(keyword in user_query for keyword in ['upload', 'file', 'document', 'pdf', 'estate planning', 'will', 'trust']):
                    return "file_upload"
        
        # If user explicitly mentions "report", "analysis", "portfolio", prioritize portfolio context
        if any(keyword in query_lower for keyword in ['report', 'analysis', 'portfolio', 'coverage', 'recommendation']):
            # Look for portfolio analysis in recent turns
            for turn in reversed(recent_turns[-3:]):
                assistant_response = turn.get('assistant_response', '').lower()
                if self._contains_structured_data(assistant_response):
                    return "portfolio_report"
        
        # PRIORITY 3: Check recent turns in reverse chronological order for context
        for turn in reversed(recent_turns[-3:]):
            user_query = turn.get('user_query', '').lower()
            assistant_response = turn.get('assistant_response', '').lower()
            
            # Check if this turn involved file upload
            if any(keyword in user_query for keyword in ['upload', 'file', 'document', 'pdf', 'estate planning', 'will', 'trust']):
                if 'file' in current_query.lower() or 'this file' in current_query.lower():
                    return "file_upload"
            
            # Check if this turn involved portfolio analysis
            if self._contains_structured_data(assistant_response):
                if (any(keyword in current_query.lower() for keyword in ['report', 'analysis', 'portfolio', 'coverage', 'recommendation']) or 
                    is_vague_follow_up):
                    return "portfolio_report"
            
            # Check if this turn involved calculations
            if any(keyword in assistant_response for keyword in ['calculated', 'calculation', 'computed', 'result', 'coverage needs']):
                if (any(keyword in current_query.lower() for keyword in ['calculate', 'calculation', 'coverage', 'needs', 'breakdown']) or 
                    is_vague_follow_up):
                    return "calculation"
        
        # PRIORITY 4: Fallback to most recent response analysis
        if self._contains_structured_data(most_recent_response):
            return "portfolio_report"
        
        # Check for calculation indicators
        if any(keyword in most_recent_response for keyword in ['calculated', 'calculation', 'computed', 'result']):
            return "calculation"
        
        # Check for analysis indicators
        if any(keyword in most_recent_response for keyword in ['analysis', 'analyzed', 'assessment', 'evaluation']):
            return "analysis"
        
        # Check for general discussion
        if any(keyword in most_recent_response for keyword in ['discussion', 'explanation', 'information', 'details']):
            return "general_discussion"
        
        return None
    
    async def _semantic_context_matching(self, current_query: str, recent_turns: List[Dict[str, Any]]) -> Optional[str]:
        """Use LLM to determine what the user is most likely referring to based on semantic similarity"""
        try:
            if not recent_turns:
                return None
            
            # Build context for LLM analysis
            context_parts = []
            for i, turn in enumerate(recent_turns[-3:]):  # Last 3 turns
                user_query = turn.get('user_query', '')
                assistant_response = turn.get('assistant_response', '')
                
                if user_query and assistant_response:
                    context_parts.append(f"Turn {i+1}:")
                    context_parts.append(f"User: {user_query}")
                    context_parts.append(f"Assistant: {assistant_response[:500]}...")  # Truncate for performance
                    context_parts.append("")
            
            conversation_context = "\n".join(context_parts)
            
            # Use LLM to determine context
            prompt = f"""
            User query: "{current_query}"
            
            Recent conversation context (most recent first):
            {conversation_context}
            
            What is the user most likely referring to? Consider:
            1. The most recent response (highest priority)
            2. Semantic similarity between query and responses
            3. Context relevance and specificity
            4. Order sequence of messages (most recent = highest priority)
            
            Return one of these exact values:
            - portfolio_report (if referring to portfolio analysis, investment analysis, financial reports from portfolio tools)
            - calculation (if referring to life insurance calculations, coverage needs, quick calculator results, "COVERAGE ANALYSIS" sections)
            - analysis (if referring to general analysis, assessments, evaluations)
            - file_upload (if referring to uploaded files, documents, PDFs)
            - general_discussion (if referring to general conversation topics)
            
            Consider these patterns:
            - "can you summarize this file" → likely file_upload if recent file upload, otherwise portfolio_report
            - "tell me more about this" → most recent response type
            - "can you go more detail into this" → most recent response type
            - "what does that mean" → most recent response type
            - "explain this better" → most recent response type
            - "can you expand on this" after calculator results → calculation (if response contains "COVERAGE ANALYSIS", "Coverage Needed", "Product Recommendation", "Coverage Gap", "About You")
            - "can you expand on this" after portfolio analysis → portfolio_report (if response contains portfolio data, investment analysis, asset allocation)
            
            **SPECIFIC EXAMPLES:**
            - Calculator results: "COVERAGE ANALYSIS\nCoverage Needed: $1,800,000\nCurrent Coverage: $1,000,000\nCoverage Gap: $800,000" → calculation
            - Portfolio reports: "Portfolio Analysis\nAsset Allocation: 60% stocks, 40% bonds\nRisk Assessment: Moderate" → portfolio_report
            
            Return only the category name, nothing else.
            """
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing conversation flow and determining what users are referring to. Always respond with only the exact category name."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().lower()
            
            # Validate result
            valid_categories = ['portfolio_report', 'calculation', 'analysis', 'file_upload', 'general_discussion']
            if result in valid_categories:
                self.logger.info(f"🔍 SEMANTIC MATCHING: Determined context: {result}")
                return result
            else:
                self.logger.warning(f"🔍 SEMANTIC MATCHING: Invalid result '{result}', falling back to rule-based detection")
                return self._detect_referenced_item(current_query, recent_turns)
                
        except Exception as e:
            self.logger.error(f"🔍 SEMANTIC MATCHING: Error in semantic context matching: {e}")
            # Fallback to rule-based detection
            return self._detect_referenced_item(current_query, recent_turns)
    
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
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get follow-up detection metrics"""
        try:
            cache_hit_rate = (self._cache_hits / self._total_detections) if self._total_detections > 0 else 0.0
            average_confidence = (sum(self._confidence_scores) / len(self._confidence_scores)) if self._confidence_scores else 0.0
            
            return {
                "total_detections": self._total_detections,
                "successful_detections": self._successful_detections,
                "cache_hits": self._cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "average_confidence": average_confidence,
                "detection_success_rate": (self._successful_detections / self._total_detections) if self._total_detections > 0 else 0.0
            }
        except Exception as e:
            self.logger.error(f"Error getting follow-up detection metrics: {e}")
            return {
                "total_detections": 0,
                "successful_detections": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0.0,
                "average_confidence": 0.0,
                "detection_success_rate": 0.0
            }
    
    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self._total_detections = 0
        self._successful_detections = 0
        self._cache_hits = 0
        self._confidence_scores = []
        self.logger.info("🔍 FOLLOW-UP DETECTOR: Metrics reset")
    

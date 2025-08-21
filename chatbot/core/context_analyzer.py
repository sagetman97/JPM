"""
LLM-Based Context Analyzer

This module provides intelligent context understanding and query enhancement
using LLM capabilities for natural language processing.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from .conversation_memory import ConversationMemory, MemoryType

logger = logging.getLogger(__name__)

class LLMContextAnalyzer:
    """
    LLM-based context analyzer that provides intelligent understanding of:
    - Follow-up questions and their context
    - Natural language references (pronouns, etc.)
    - Query enhancement based on conversation history
    - Semantic relationship understanding
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
    async def analyze_query_context(self, query: str, conversation_memory: ConversationMemory) -> Dict[str, Any]:
        """
        Analyze a query in the context of conversation history.
        
        Returns:
            Dict containing:
            - is_follow_up: bool
            - main_topic: str - what the query refers to
            - context_keywords: List[str] - keywords to enhance the query
            - enhancement_strategy: str - how to enhance the query
            - confidence: float - confidence in the analysis
        """
        try:
            # First, use the memory system's basic follow-up detection
            is_follow_up, main_topic, related_concepts = conversation_memory.understand_follow_up(query)
            
            if not is_follow_up:
                return {
                    "is_follow_up": False,
                    "main_topic": None,
                    "context_keywords": [],
                    "enhancement_strategy": "none",
                    "confidence": 1.0
                }
            
            # Use LLM to get deeper understanding if available
            if self.llm_client:
                try:
                    llm_analysis = await self._analyze_with_llm(query, conversation_memory)
                    return llm_analysis
                except Exception as e:
                    logger.warning(f"🔍 CONTEXT ANALYZER: LLM analysis failed, falling back to rule-based: {e}")
                    return self._rule_based_analysis(query, conversation_memory, main_topic, related_concepts)
            else:
                # Fallback to rule-based analysis
                logger.info("🔍 CONTEXT ANALYZER: No LLM client available, using rule-based analysis")
                return self._rule_based_analysis(query, conversation_memory, main_topic, related_concepts)
                
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error analyzing query context: {e}")
            return {
                "is_follow_up": False,
                "main_topic": None,
                "context_keywords": [],
                "enhancement_strategy": "none",
                "confidence": 0.0
            }
    
    async def _analyze_with_llm(self, query: str, conversation_memory: ConversationMemory) -> Dict[str, Any]:
        """Use LLM to analyze query context"""
        try:
            if not self.llm_client:
                logger.warning("🔍 CONTEXT ANALYZER: No LLM client available, falling back to rule-based analysis")
                return self._rule_based_analysis(query, conversation_memory, None, [])
            
            # Get conversation context
            context = conversation_memory.get_conversation_context()
            
            # Build prompt for LLM analysis
            prompt = self._build_analysis_prompt(query, context)
            
            # Get LLM response
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",  # Use appropriate model
                messages=[
                    {"role": "system", "content": "You are an expert at understanding conversation context and follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            # Parse LLM response
            analysis = self._parse_llm_analysis(response.choices[0].message.content)
            
            logger.info(f"🔍 CONTEXT ANALYZER: LLM analysis completed for query: {query[:50]}...")
            return analysis
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error in LLM analysis: {e}")
            # Fallback to rule-based analysis
            return self._rule_based_analysis(query, conversation_memory, None, [])
    
    def _build_analysis_prompt(self, query: str, context: Dict[str, Any]) -> str:
        """Build prompt for LLM context analysis"""
        return f"""
Analyze this query in the context of the conversation and provide structured analysis.

**Current Query:** {query}

**Conversation Context:**
- Current Topic: {context.get('current_topic', 'None')}
- Recent Topics: {', '.join(context.get('recent_topics', []))}
- Recent Concepts: {', '.join(context.get('recent_concepts', []))}
- Conversation Summary: {context.get('conversation_summary', 'None')}

**Analysis Tasks:**
1. Determine if this is a follow-up question
2. Identify what the query refers to (main topic)
3. Extract context keywords that should enhance the query
4. Suggest an enhancement strategy

**Return your analysis in this exact format:**
```
IS_FOLLOW_UP: [true/false]
MAIN_TOPIC: [topic or "none"]
CONTEXT_KEYWORDS: [keyword1, keyword2, keyword3]
ENHANCEMENT_STRATEGY: [strategy description]
CONFIDENCE: [0.0-1.0]
```

**Example:**
If the query is "How does the cash value work?" and we were discussing IUL:
```
IS_FOLLOW_UP: true
MAIN_TOPIC: Indexed Universal Life (IUL)
CONTEXT_KEYWORDS: IUL, indexed universal life, cash value
ENHANCEMENT_STRATEGY: Enhance query with IUL context to get IUL-specific cash value information
CONFIDENCE: 0.9
```
"""
    
    def _parse_llm_analysis(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into structured analysis"""
        try:
            lines = llm_response.strip().split('\n')
            analysis = {
                "is_follow_up": False,
                "main_topic": None,
                "context_keywords": [],
                "enhancement_strategy": "none",
                "confidence": 0.0
            }
            
            for line in lines:
                if line.startswith('IS_FOLLOW_UP:'):
                    analysis["is_follow_up"] = 'true' in line.lower()
                elif line.startswith('MAIN_TOPIC:'):
                    topic = line.split(':', 1)[1].strip()
                    analysis["main_topic"] = topic if topic.lower() != 'none' else None
                elif line.startswith('CONTEXT_KEYWORDS:'):
                    keywords_str = line.split(':', 1)[1].strip()
                    analysis["context_keywords"] = [k.strip() for k in keywords_str.strip('[]').split(',')]
                elif line.startswith('ENHANCEMENT_STRATEGY:'):
                    strategy = line.split(':', 1)[1].strip()
                    analysis["enhancement_strategy"] = strategy
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                        analysis["confidence"] = confidence
                    except ValueError:
                        analysis["confidence"] = 0.5
            
            return analysis
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error parsing LLM analysis: {e}")
            return {
                "is_follow_up": False,
                "main_topic": None,
                "context_keywords": [],
                "enhancement_strategy": "none",
                "confidence": 0.0
            }
    
    def _rule_based_analysis(self, query: str, conversation_memory: ConversationMemory, 
                            main_topic: Optional[str], related_concepts: List[str]) -> Dict[str, Any]:
        """Fallback rule-based analysis when LLM is not available"""
        try:
            query_lower = query.lower()
            
            # Extract potential keywords from the query
            potential_keywords = []
            
            # Check for insurance-related terms
            insurance_terms = ['cash value', 'premium', 'death benefit', 'policy', 'coverage', 'growth', 'accumulation']
            for term in insurance_terms:
                if term in query_lower:
                    potential_keywords.append(term)
            
            # Check for action words
            action_words = ['explain', 'how', 'what', 'why', 'when', 'where', 'expand', 'elaborate', 'dive']
            for word in action_words:
                if word in query_lower:
                    potential_keywords.append(word)
            
            # Build enhancement strategy
            enhancement_strategy = "none"
            if main_topic and potential_keywords:
                enhancement_strategy = f"Enhance query with {main_topic} context to get {', '.join(potential_keywords)} information"
            
            return {
                "is_follow_up": True,
                "main_topic": main_topic,
                "context_keywords": potential_keywords,
                "enhancement_strategy": enhancement_strategy,
                "confidence": 0.7  # Lower confidence for rule-based analysis
            }
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error in rule-based analysis: {e}")
            return {
                "is_follow_up": False,
                "main_topic": None,
                "context_keywords": [],
                "enhancement_strategy": "none",
                "confidence": 0.0
            }
    
    def extract_entities_from_query(self, query: str, conversation_memory: ConversationMemory) -> List[str]:
        """Extract entities from a query that might be relevant to context"""
        try:
            entities = []
            query_lower = query.lower()
            
            # Check for insurance product mentions
            insurance_products = [
                'iul', 'indexed universal life', 'universal life', 'whole life', 
                'term life', 'variable life', 'variable universal life'
            ]
            
            for product in insurance_products:
                if product in query_lower:
                    entities.append(product)
            
            # Check for financial concepts
            financial_concepts = [
                'cash value', 'premium', 'death benefit', 'policy', 'coverage',
                'growth', 'accumulation', 'surrender', 'loan', 'withdrawal'
            ]
            
            for concept in financial_concepts:
                if concept in query_lower:
                    entities.append(concept)
            
            # Check for action words that might indicate follow-up
            action_words = ['explain', 'how', 'what', 'why', 'expand', 'elaborate', 'dive']
            for word in action_words:
                if word in query_lower:
                    entities.append(word)
            
            logger.info(f"🔍 CONTEXT ANALYZER: Extracted entities: {entities}")
            return entities
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error extracting entities: {e}")
            return []
    
    def suggest_query_enhancement(self, query: str, context_analysis: Dict[str, Any]) -> str:
        """Suggest how to enhance a query based on context analysis"""
        try:
            if not context_analysis.get("is_follow_up", False):
                return query
            
            main_topic = context_analysis.get("main_topic")
            context_keywords = context_analysis.get("context_keywords", [])
            
            if not main_topic or not context_keywords:
                return query
            
            # Build enhanced query
            enhanced_parts = [query]
            
            # Add main topic context
            enhanced_parts.append(f"Focus on: {main_topic}")
            
            # Add relevant keywords
            if context_keywords:
                enhanced_parts.append(f"Related concepts: {', '.join(context_keywords)}")
            
            enhanced_query = " | ".join(enhanced_parts)
            
            logger.info(f"🔍 CONTEXT ANALYZER: Suggested query enhancement: {query[:50]}... -> {enhanced_query[:100]}...")
            return enhanced_query
            
        except Exception as e:
            logger.error(f"🔍 CONTEXT ANALYZER: Error suggesting query enhancement: {e}")
            return query

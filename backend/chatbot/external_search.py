import logging
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from .schemas import SearchResult, ConversationContext
from .config import config

logger = logging.getLogger(__name__)

class SearchQualityEvaluator:
    """Evaluates quality of search results using semantic understanding"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def evaluate_search_quality(self, results: List[Dict[str, Any]], query: str, context: ConversationContext) -> List[float]:
        """Evaluate quality of search results using semantic understanding"""
        
        try:
            quality_scores = []
            
            for result in results:
                prompt = self._build_quality_evaluation_prompt(result, query, context)
                
                response = await self.llm.chat.completions.create(
                    model=config.openai_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                
                quality_score = self._parse_quality_evaluation(response.choices[0].message.content)
                quality_scores.append(quality_score)
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Error evaluating search quality: {e}")
            # Return default scores
            return [0.5] * len(results)
    
    def _build_quality_evaluation_prompt(self, result: Dict[str, Any], query: str, context: ConversationContext) -> str:
        """Build prompt for quality evaluation"""
        
        return f"""
        Evaluate the quality and relevance of this search result:
        
        **Query:** "{query}"
        **Search Result:** "{result.get('content', '')}"
        **Source:** {result.get('url', 'Unknown')}
        
        **Evaluation Criteria:**
        1. **Relevance**: How well does this address the query? (0-1)
        2. **Accuracy**: Is the information likely to be correct? (0-1)
        3. **Completeness**: Does it provide sufficient information? (0-1)
        4. **Timeliness**: Is the information current? (0-1)
        5. **Authority**: Is the source credible? (0-1)
        
        **User Context:**
        - Knowledge Level: {context.knowledge_level.value}
        - Focus Area: {context.current_topic or 'general'}
        
        **Response Format:**
        Return ONLY a JSON object with this structure:
        {{
            "relevance": 0.8,
            "accuracy": 0.9,
            "completeness": 0.7,
            "timeliness": 0.8,
            "authority": 0.9,
            "overall_score": 0.82,
            "reasoning": "brief explanation of scoring"
        }}
        
        **Important:**
        - Score each criterion 0-1 (0 = poor, 1 = excellent)
        - Calculate overall_score as average of all criteria
        - Provide brief reasoning for the overall score
        """
    
    def _parse_quality_evaluation(self, response: str) -> float:
        """Parse quality evaluation response"""
        
        try:
            # Clean response and extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            # Parse JSON
            evaluation_data = json.loads(response)
            return float(evaluation_data.get("overall_score", 0.5))
            
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Error parsing quality evaluation: {e}")
            return 0.5

class ExternalSearchSystem:
    """Handles external search with quality evaluation"""
    
    def __init__(self):
        # For now, external search is disabled
        self.tavily_client = None
        self.quality_evaluator = SearchQualityEvaluator()
        self.llm = OpenAI(
            api_key=config.openai_api_key
        )
    
    async def search_with_evaluation(self, query: str, context: ConversationContext) -> SearchResult:
        """Search external sources with quality evaluation"""
        
        try:
            # For now, return a message that external search is not available
            # In production, you would integrate with Tavily or other search APIs
            
            return SearchResult(
                response="External search is currently not available. I'll rely on my internal knowledge base to help you.",
                quality_score=0.0,
                source_results=[],
                original_query=query,
                confidence=0.0
            )
            
        except Exception as e:
            logger.error(f"Error in external search: {e}")
            return SearchResult(
                response="I encountered an error while searching external sources. Please try rephrasing your question.",
                quality_score=0.0,
                source_results=[],
                original_query=query,
                confidence=0.0
            )
    
    async def _perform_search(self, query: str, context: ConversationContext) -> List[Dict[str, Any]]:
        """Perform search using external search API (placeholder)"""
        
        # This would be implemented when external search is enabled
        logger.info(f"External search requested for: {query}")
        return []
    
    def _enhance_search_query(self, query: str, context: ConversationContext) -> str:
        """Enhance search query with context information"""
        
        enhanced_query = query
        
        # Add context-specific terms
        if context.semantic_themes:
            theme_terms = " ".join(context.semantic_themes)
            enhanced_query += f" {theme_terms}"
        
        # Add knowledge level specific terms
        if context.knowledge_level.value == "beginner":
            enhanced_query += " basic explanation guide"
        elif context.knowledge_level.value == "expert":
            enhanced_query += " advanced strategies analysis"
        
        # Add financial focus
        enhanced_query += " life insurance financial planning"
        
        return enhanced_query
    
    def _filter_by_quality(self, results: List[Dict[str, Any]], quality_scores: List[float], threshold: float) -> List[Dict[str, Any]]:
        """Filter results by quality threshold"""
        
        filtered_results = []
        
        for result, score in zip(results, quality_scores):
            if score >= threshold:
                result["quality_score"] = score
                filtered_results.append(result)
        
        # Sort by quality score
        filtered_results.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return filtered_results
    
    def _calculate_overall_quality(self, quality_scores: List[float], filtered_results: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score"""
        
        if not filtered_results:
            return 0.0
        
        # Calculate weighted average based on result quality
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for i, result in enumerate(filtered_results):
            weight = 1.0 / (i + 1)  # Higher weight for top results
            total_weighted_score += result["quality_score"] * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_weighted_score / total_weight
        else:
            return 0.0
    
    async def _generate_search_response(self, results: List[Dict[str, Any]], query: str, context: ConversationContext) -> str:
        """Generate response from search results"""
        
        try:
            # For now, use a simple template-based approach
            # In production, you'd use an LLM for this
            
            if not results:
                return "I couldn't find reliable information from external sources."
            
            # Create response from top results
            response = f"Based on my search of external sources, here's what I found about {query}:\n\n"
            
            # Include top 3 results
            for i, result in enumerate(results[:3]):
                response += f"{i+1}. **{result['title']}**\n"
                response += f"   {result['content'][:200]}...\n"
                response += f"   Source: {result['source']}\n\n"
            
            if len(results) > 3:
                response += f"I found {len(results)} relevant sources. Would you like me to provide more specific information from any of these sources?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating search response: {e}")
            return "I found some information from external sources, but encountered an error while generating a response."
    
    async def retry_search_with_different_strategy(self, query: str, context: ConversationContext, strategy: str = "advanced") -> SearchResult:
        """Retry search with different strategy if initial search fails"""
        
        # For now, return the same result as regular search
        return await self.search_with_evaluation(query, context) 
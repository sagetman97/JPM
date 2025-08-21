import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from .schemas import SearchResult, ConversationContext
from .config import config
import time

logger = logging.getLogger(__name__)

class SearchQualityEvaluator:
    """Evaluates quality of search results using semantic understanding"""
    
    def __init__(self):
        self.llm = AsyncOpenAI(
            api_key=config.openai_api_key
        )
        self.model = config.openai_model
        self.temperature = config.openai_temperature
    
    async def evaluate_search_quality(self, results: List[Dict[str, Any]], query: str, context: ConversationContext) -> List[float]:
        """Evaluate quality of search results using semantic understanding"""
        
        try:
            quality_scores = []
            
            for result in results:
                score = await self._evaluate_single_result(result, query, context)
                quality_scores.append(score)
            
            return quality_scores
            
        except Exception as e:
            logger.error(f"Error evaluating search quality: {e}")
            # Return default scores
            return [0.5] * len(results)
    
    async def _evaluate_single_result(self, result: Dict[str, Any], query: str, context: ConversationContext) -> float:
        """Evaluate quality of a single search result"""
        
        try:
            prompt = f"""
        Evaluate the quality and relevance of this search result:
        
        **Query:** "{query}"
        **Search Result:** "{result.get('content', '')}"
        
        **Evaluation Criteria:**
            1. **Relevance**: How well does this result answer the query?
            2. **Accuracy**: Is the information factual and reliable?
            3. **Completeness**: Does it provide sufficient detail?
            4. **Currency**: Is the information current and up-to-date?
            5. **Usefulness**: Would this help a financial advisor or client?
            
            **Special Considerations for Financial Information:**
            - Current rates, prices, and market conditions are HIGHLY valuable even if brief
            - Company-specific information (like Progressive rates) is VALUABLE for comparison
            - Recent changes and updates are CRITICAL for financial planning
            - Don't penalize brief responses if they contain current, actionable information
            - Real-time market data is often more valuable than comprehensive historical data
            
            **Return a score from 0.0 to 1.0:**
            - 0.0-0.3: Poor quality, not relevant
            - 0.4-0.6: Moderate quality, somewhat relevant
            - 0.7-0.8: Good quality, relevant
            - 0.9-1.0: Excellent quality, highly relevant
            
            **For current financial information (rates, prices, company info):**
            - If it contains current rates/prices: minimum 0.7 (increased from 0.6)
            - If it mentions specific companies: minimum 0.6 (increased from 0.5)
            - If it's recent/current year: minimum 0.6 (increased from 0.5)
            - If it's about current market conditions: minimum 0.7
            
            **Scoring Guidelines:**
            - Current rates for specific companies: 0.7-0.9
            - Market conditions and trends: 0.6-0.8
            - Company-specific information: 0.6-0.8
            - General financial advice: 0.5-0.7
            
            Score: """
            
            response = await self.llm.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of financial information quality and relevance. Be GENEROUS to current/real-time information as it's highly valuable for financial planning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=100
            )
            
            score_text = response.choices[0].message.content.strip()
            
            # Extract numeric score
            try:
                score = float(score_text)
                # Apply minimum thresholds for valuable current information
                if self._contains_current_financial_info(result.get('content', ''), query):
                    score = max(score, 0.65)  # Minimum 0.65 for current financial info
                return max(0.0, min(1.0, score))  # Clamp between 0 and 1
            except ValueError:
                # If parsing fails, return default score
                return 0.65 if self._contains_current_financial_info(result.get('content', ''), query) else 0.6
                
        except Exception as e:
            logger.error(f"Error evaluating single result: {e}")
            return 0.65 if self._contains_current_financial_info(result.get('content', ''), query) else 0.5
    
    def _contains_current_financial_info(self, content: str, query: str) -> bool:
        """Check if content contains current financial information that should get higher scores"""
        
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Check for current financial indicators
        current_indicators = [
            "current", "latest", "recent", "today", "2024", "2025", "this year",
            "rate", "price", "premium", "quote", "cost"
        ]
        
        # Check for company-specific information
        company_indicators = [
            "progressive", "state farm", "allstate", "geico", "farmers",
            "company", "carrier", "insurer", "provider"
        ]
        
        # Check for market condition indicators
        market_indicators = [
            "market", "trend", "condition", "environment", "climate"
        ]
        
        # If query is about current rates or specific companies, be more lenient
        if any(indicator in query_lower for indicator in ["rate", "price", "progressive", "current"]):
            if any(indicator in content_lower for indicator in current_indicators + company_indicators):
                return True
        
        # If content contains current financial information
        if any(indicator in content_lower for indicator in current_indicators + company_indicators + market_indicators):
            return True
        
        return False

class ExternalSearchSystem:
    """External search system using Tavily API with quality evaluation"""
    
    def __init__(self):
        # Initialize Tavily client if API key is available
        self.tavily_client = None
        self.quality_evaluator = SearchQualityEvaluator()
        
        # Add simple cache to prevent duplicate searches
        self._search_cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        
        try:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=tavily_api_key)
                logger.info("Tavily client initialized successfully")
            else:
                logger.warning("Tavily API key not found - external search will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            self.tavily_client = None
    
    async def search_with_evaluation(self, query: str, context: ConversationContext, needs_external_search: bool = None) -> SearchResult:
        """Perform external search with quality evaluation"""
        try:
            logger.info(f"Starting external search for query: {query}")
            
            # Check cache for duplicate searches
            cache_key = f"{query.lower().strip()}_{context.session_id}"
            current_time = time.time()
            
            if cache_key in self._search_cache:
                cache_entry = self._search_cache[cache_key]
                if current_time - cache_entry["timestamp"] < self._cache_ttl:
                    logger.info(f"Returning cached search result for query: {query[:50]}...")
                    return cache_entry["result"]
                else:
                    # Remove expired cache entry
                    del self._search_cache[cache_key]
            
            # Check if external search is needed - priority: 1) Direct parameter, 2) Context field
            if needs_external_search is not None:
                should_search = needs_external_search
                logger.info(f"External search decision from direct parameter: {should_search}")
            else:
                should_search = getattr(context, 'needs_external_search', False)
                logger.info(f"External search decision from context: {should_search}")
            
            if not should_search:
                logger.info("External search not needed according to decision logic")
                return SearchResult(
                    response="I'll provide information based on my comprehensive knowledge base.",
                    quality_score=0.0,
                    source_results=[],
                    original_query=query,
                    confidence=0.0
                )
            
            logger.info("External search needed according to decision logic")
            
            # Check if we have a Tavily client available
            if not self.tavily_client:
                logger.warning("Tavily client not available, cannot perform external search")
                return SearchResult(
                    response="I'll provide information based on my comprehensive knowledge base.",
                    quality_score=0.0,
                    source_results=[],
                    original_query=query,
                    confidence=0.0
                )
            
            # Perform the search
            search_results = await self._perform_search(query, context)
            
            if not search_results:
                logger.info("No search results found")
                return SearchResult(
                    response="I'll provide information based on my comprehensive knowledge base.",
                    quality_score=0.0,
                    source_results=[],
                    original_query=query,
                    confidence=0.0
                )
            
            # Evaluate search result quality
            quality_scores = await self.quality_evaluator.evaluate_search_quality(search_results, query, context)
            
            # Filter results by quality threshold
            filtered_results = self._filter_by_quality(search_results, quality_scores, config.min_search_confidence)
            
            if not filtered_results:
                logger.info(f"No search results met quality threshold ({config.min_search_confidence})")
                return SearchResult(
                    response="I'll provide information based on my comprehensive knowledge base.",
                    quality_score=0.0,
                    source_results=[],
                    original_query=query,
                    confidence=0.0
                )
            
            # Calculate overall quality
            overall_quality = self._calculate_overall_quality(quality_scores, filtered_results)
            
            # Generate response from search results
            search_response = await self._generate_search_response(filtered_results, query, context)
            
            # Add source attribution to search response
            if filtered_results:
                source_info = self._format_source_attribution(filtered_results)
                search_response += f"\n\n**Sources:**\n{source_info}"
            
            # Create search result
            result = SearchResult(
                response=search_response,
                quality_score=overall_quality,
                source_results=filtered_results,
                original_query=query,
                confidence=overall_quality
            )
            
            # Cache the result
            self._search_cache[cache_key] = {
                "timestamp": current_time,
                "result": result
            }
            
            # Clean up old cache entries
            self._cleanup_cache()
            
            logger.info(f"External search completed successfully:")
            logger.info(f"  Results found: {len(search_results)}")
            logger.info(f"  Quality results: {len(filtered_results)}")
            logger.info(f"  Overall quality: {overall_quality:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in external search: {e}")
            return SearchResult(
                response="I'll provide information based on my comprehensive knowledge base.",
                quality_score=0.0,
                source_results=[],
                original_query=query,
                confidence=0.0
            )
    
    def _cleanup_cache(self):
        """Clean up old cache entries to prevent memory bloat"""
        try:
            current_time = time.time()
            expired_keys = []
            
            for cache_key, cache_entry in self._search_cache.items():
                if current_time - cache_entry["timestamp"] > self._cache_ttl:
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self._search_cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")

    def _should_use_external_search(self, query: str, context: ConversationContext) -> bool:
        """Determine if external search would be valuable for this query"""
        # This method is now deprecated - the decision is made by the intent classifier
        # We keep it for backward compatibility but it should not be used for new queries
        
        logger.info("_should_use_external_search called - this method is deprecated")
        logger.info("External search decisions are now made by the intent classifier")
        
        # For backward compatibility, return False to avoid unexpected behavior
        return False
    
    async def _perform_search(self, query: str, context: ConversationContext) -> List[Dict[str, Any]]:
        """Perform search using external search API"""
        
        try:
            if not self.tavily_client:
                logger.warning("Tavily client not available for external search")
                return []
            
            # Enhance the query with context
            enhanced_query = self._enhance_search_query(query, context)
            
            logger.info(f"Performing external search for: {enhanced_query}")
            
            # Perform Tavily search
            search_response = self.tavily_client.search(
                query=enhanced_query,
                search_depth="basic",
                max_results=5,
                include_answer=True,
                include_raw_content=False
            )
            
            # Extract results
            results = []
            if "results" in search_response:
                for result in search_response["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "url": result.get("url", ""),
                        "score": result.get("score", 0.0)
                    })
            
            logger.info(f"External search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error performing external search: {e}")
            return []
    
    def _enhance_search_query(self, query: str, context: ConversationContext) -> str:
        """Enhance search query with context information - ULTRA CONSERVATIVE approach to prevent duplication"""
        
        # Start with the original query - minimal enhancement to prevent duplication
        enhanced_query = query
        
        # ONLY add essential context if the query is very short (less than 50 characters)
        # This prevents over-enhancement that could create different queries
        if len(query) < 50:
            # Add minimal financial context only if not already present
            if "life insurance" not in query.lower():
                enhanced_query += " life insurance"
        
        # NO additional enhancements - keep it minimal to prevent query variations
        # This ensures our deduplication logic works properly
        
        # Special case: only add year if explicitly asking for current information
        query_lower = query.lower()
        current_info_needed = any(term in query_lower for term in ["rate", "price", "current", "today", "latest", "recent"])
        
        if current_info_needed and "2024" not in query_lower and "2025" not in query_lower:
            # Only add year if it's a very short query asking for current info
            if len(query) < 60:
                enhanced_query += " 2025"
        
        # CRITICAL: Limit total enhancement to prevent query variations
        # If enhancement would make query too different, revert to original
        if len(enhanced_query) > len(query) * 1.2:  # Don't increase by more than 20%
            enhanced_query = query  # Revert to original to prevent duplication
        
        logger.info(f"🔍 Query enhancement: '{query}' -> '{enhanced_query}' (minimal enhancement)")
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
            if not results:
                return "I couldn't find relevant external information for your query."
            
            # Build response from top results
            response = f"Based on my search of current external sources, here's what I found about {query}:\n\n"
            
            for i, result in enumerate(results[:3]):  # Top 3 results
                response += f"**{result.get('title', 'Source')}**\n"
                response += f"{result.get('content', '')[:200]}...\n\n"
                
                if result.get('url'):
                    response += f"Source: {result.get('url')}\n\n"
            
            response += "\n*Note: This information comes from external sources and may be more current than my internal knowledge base.*"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating search response: {e}")
            return "I found external information but couldn't format it properly. Please try rephrasing your question."
    
    async def retry_search_with_different_strategy(self, query: str, context: ConversationContext, strategy: str = "advanced", needs_external_search: bool = None) -> SearchResult:
        """Retry search with different strategy if initial search fails"""
        
        # For now, return the same result as regular search
        # This can be enhanced later with different search strategies
        return await self.search_with_evaluation(query, context, needs_external_search=needs_external_search) 

    def _format_source_attribution(self, results: List[Dict[str, Any]]) -> str:
        """Format source attribution for search results"""
        try:
            source_lines = []
            for i, result in enumerate(results[:3], 1):  # Show top 3 sources
                title = result.get('title', 'Unknown Source')
                url = result.get('url', '')
                if url:
                    source_lines.append(f"{i}. [{title}]({url})")
                else:
                    source_lines.append(f"{i}. {title}")
            
            if source_lines:
                return "\n".join(source_lines)
            else:
                return "External search sources"
                
        except Exception as e:
            logger.error(f"Error formatting source attribution: {e}")
            return "External search sources" 
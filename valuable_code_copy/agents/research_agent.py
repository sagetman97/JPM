"""
Research Agent for Financial Advisor Assistant

This agent handles queries requiring external search and current information,
combining Tavily search results with RAG knowledge for comprehensive responses.
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import MessagesPlaceholder
from langchain_community.tools import TavilySearchResults
import json
import re

from utils.confidence import assess_confidence_score
from utils.rate_limiter import api_rate_limiter
from config.settings import settings

class ResearchAgent:
    """
    Research agent that combines RAG knowledge with external search for comprehensive responses.
    """
    
    def __init__(self, llm: ChatOpenAI, rag_agent, tavily_api_key: str):
        self.llm = llm
        self.rag_agent = rag_agent
        
        # Initialize Tavily search tool
        self.search_tool = TavilySearchResults(
            api_key=tavily_api_key,
            max_results=5,
            search_depth="advanced"
        )
        
        # Create research prompt
        self.research_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert financial research assistant specializing in life insurance and financial planning.

Your role is to provide comprehensive, accurate, and up-to-date information by combining:
1. Your knowledge base (RAG context)
2. Current market information (search results)
3. Industry best practices

When researching, follow these guidelines:

**Information Integration:**
- Start with your knowledge base for foundational information
- Use search results for current market data, rates, and recent developments
- Cross-reference information for accuracy
- Prioritize authoritative sources (financial institutions, regulatory bodies, industry reports)

**Response Structure:**
1. **Executive Summary**: Key findings and recommendations
2. **Current Market Context**: Latest rates, trends, and market conditions
3. **Detailed Analysis**: Comprehensive explanation with supporting evidence
4. **Practical Recommendations**: Actionable advice for financial advisors
5. **Sources**: Cite your information sources

**Quality Standards:**
- Always verify information from multiple sources when possible
- Distinguish between facts and opinions
- Highlight any conflicting information
- Provide context for market data (time period, conditions)
- Focus on information relevant to financial advisors and their clients

**Life Insurance Focus:**
- Emphasize life insurance as part of holistic financial planning
- Highlight risk management and portfolio diversification benefits
- Provide specific, actionable advice for advisors
- Include current market rates and product availability
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the research chain
        self.research_chain = self.research_prompt | self.llm | StrOutputParser()
    
    def search_current_information(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for current information using Tavily.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # Wait for rate limiter before making API calls
            api_rate_limiter.wait_if_needed()
            
            # Enhance query for financial context
            enhanced_query = f"life insurance {query} current rates market conditions financial planning 2024"
            search_results = self.search_tool.invoke(enhanced_query)
            return search_results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def combine_rag_and_search(self, query: str, rag_response: str, search_results: List[Dict]) -> str:
        """
        Combine RAG knowledge with search results for comprehensive response.
        
        Args:
            query: Original user query
            rag_response: Response from RAG system
            search_results: Results from external search
            
        Returns:
            Combined comprehensive response
        """
        # Format search results
        search_context = ""
        if search_results:
            search_context = "\n\n**Current Market Information:**\n"
            for i, result in enumerate(search_results[:3], 1):  # Top 3 results
                search_context += f"{i}. **{result.get('title', 'No title')}**\n"
                search_context += f"   Source: {result.get('url', 'Unknown')}\n"
                search_context += f"   {result.get('content', 'No content')[:300]}...\n\n"
        
        # Create combined context
        combined_context = f"""
**Query:** {query}

**Knowledge Base Information:**
{rag_response}

{search_context}

**Instructions:** Provide a comprehensive response that integrates both the knowledge base information and current market data. Focus on practical advice for financial advisors.
"""
        
        # Wait for rate limiter before making API calls
        api_rate_limiter.wait_if_needed()
        
        # Generate combined response
        response = self.research_chain.invoke({
            "messages": [HumanMessage(content=combined_context)]
        })
        
        return response
    
    def research_query(self, query: str, session_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a research query by combining RAG and external search.
        
        Args:
            query: User's research query
            session_context: Current session context
            
        Returns:
            Dict with research results and metadata
        """
        # Wait for rate limiter before making API calls
        api_rate_limiter.wait_if_needed()
        
        # Step 1: Get RAG response
        rag_result = self.rag_agent.query(query)
        rag_response = rag_result.get("response", "")
        rag_confidence = rag_result.get("confidence", 0.5)
        
        # Step 2: Search for current information
        search_results = self.search_current_information(query)
        
        # Step 3: Combine information
        if search_results:
            combined_response = self.combine_rag_and_search(query, rag_response, search_results)
            used_external_search = True
        else:
            combined_response = rag_response
            used_external_search = False
        
        # Step 4: Assess final confidence
        final_confidence = assess_confidence_score(combined_response, query, [])  # Empty list for retrieved_docs
        
        # Step 5: Prepare metadata
        metadata = {
            "rag_confidence": rag_confidence,
            "final_confidence": final_confidence,
            "used_external_search": used_external_search,
            "search_results_count": len(search_results),
            "search_sources": [result.get("url", "") for result in search_results[:3]],
            "agent_type": "RESEARCH"
        }
        
        return {
            "response": combined_response,
            "confidence": final_confidence,
            "metadata": metadata,
            "search_results": search_results
        }
    
    def get_research_feedback(self, research_result: Dict[str, Any]) -> str:
        """
        Generate user-friendly feedback about the research process.
        
        Args:
            research_result: Result from research_query
            
        Returns:
            Feedback message for the user
        """
        metadata = research_result.get("metadata", {})
        used_external_search = metadata.get("used_external_search", False)
        search_count = metadata.get("search_results_count", 0)
        confidence = research_result.get("confidence", 0.5)
        
        if used_external_search and search_count > 0:
            feedback = f"I've researched your question using {search_count} current sources and combined them with our knowledge base for a comprehensive answer."
        elif used_external_search:
            feedback = "I've searched for current information to supplement our knowledge base."
        else:
            feedback = "I've provided information from our comprehensive knowledge base."
        
        if confidence < 0.7:
            feedback += " (Note: Some information may require verification with current market conditions.)"
        
        return feedback 
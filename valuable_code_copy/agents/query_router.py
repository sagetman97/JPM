"""
Query Router Agent for Financial Advisor Assistant

This agent determines which specialized agent should handle a user query based on:
- Query intent (calculator, portfolio analysis, general RAG, external search)
- Confidence level of RAG response
- User context and session state
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.tools import BaseTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import MessagesPlaceholder
import json
import re

from utils.confidence import assess_confidence_score, should_use_external_search
from utils.rate_limiter import api_rate_limiter
from config.settings import settings

class QueryRouterAgent:
    """
    Routes queries to appropriate specialized agents based on intent and confidence.
    """
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.parser = JsonOutputParser()
        
        # Define the routing prompt
        self.routing_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent query router for a Financial Advisor Life Insurance Assistant.
            
Your job is to analyze user queries and determine which specialized agent should handle them:

1. **CALCULATOR** - For life insurance needs analysis, coverage amount calculations, policy type recommendations
   - Keywords: "calculate", "how much", "coverage amount", "needs analysis", "policy type", "term vs whole"
   - Examples: "How much life insurance do I need?", "Calculate my coverage needs", "What type of policy should I get?"

2. **PORTFOLIO** - For portfolio analysis, financial planning, investment integration
   - Keywords: "portfolio", "investment", "financial plan", "asset allocation", "risk assessment"
   - Examples: "Analyze my portfolio", "How does life insurance fit my investments?", "Financial planning"

3. **EXTERNAL_SEARCH** - For queries requiring current information, market data, or specific company policies
   - Keywords: "current rates", "market conditions", "specific company", "latest", "recent changes"
   - Examples: "What are current term life rates?", "Latest market trends", "Company X policies"

4. **RAG** - For general life insurance knowledge, policy explanations, industry information
   - Keywords: "what is", "explain", "how does", "types of", "benefits of"
   - Examples: "What is whole life insurance?", "Explain term vs permanent", "Benefits of life insurance"

5. **RESEARCH** - For complex queries requiring multiple sources or detailed analysis
   - Keywords: "research", "compare", "analysis", "detailed", "comprehensive"
   - Examples: "Research different policy types", "Compare companies", "Detailed analysis"

Analyze the query and return the appropriate agent type. Consider:
- Query intent and keywords
- User's current session context
- Complexity of the request
- Whether external information might be needed

Return a JSON object with:
- "agent_type": One of CALCULATOR, PORTFOLIO, EXTERNAL_SEARCH, RAG, RESEARCH
- "confidence": 0-1 score indicating confidence in the routing decision
- "reasoning": Brief explanation of why this agent was chosen
- "requires_external_search": Boolean indicating if external search might be needed
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the routing function
        self.routing_chain = self.routing_prompt | self.llm | self.parser
    
    def route_query(self, query: str, session_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Route a query to the appropriate agent.
        
        Args:
            query: User's query
            session_context: Current session context (uploaded files, previous interactions, etc.)
            
        Returns:
            Dict with routing decision and metadata
        """
        # Check for simple greetings first
        simple_greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy"]
        query_lower = query.lower().strip()
        
        if query_lower in simple_greetings or len(query_lower.split()) <= 2:
            return {
                "agent_type": "GREETING",
                "confidence": 0.9,
                "reasoning": "Simple greeting detected",
                "requires_external_search": False
            }
        
        # Prepare context for routing
        context = {
            "query": query,
            "session_context": session_context or {},
            "has_uploaded_files": bool(session_context and session_context.get("uploaded_files")),
            "previous_interactions": session_context.get("previous_interactions", []) if session_context else []
        }
        
        # Wait for rate limiter before making API calls
        api_rate_limiter.wait_if_needed()
        
        # Get routing decision
        routing_result = self.routing_chain.invoke({
            "messages": [HumanMessage(content=f"Query: {query}\nContext: {json.dumps(context, default=str)}")]
        })
        
        # Validate routing result
        valid_agents = ["CALCULATOR", "PORTFOLIO", "EXTERNAL_SEARCH", "RAG", "RESEARCH"]
        if routing_result.get("agent_type") not in valid_agents:
            routing_result["agent_type"] = "RAG"  # Default fallback
            routing_result["confidence"] = 0.5
            routing_result["reasoning"] = "Defaulting to RAG due to unclear routing"
        
        return routing_result
    
    def should_escalate_to_external_search(self, rag_response: str, query: str) -> bool:
        """
        Determine if a RAG response should be escalated to external search.
        
        Args:
            rag_response: Response from RAG system
            query: Original user query
            
        Returns:
            Boolean indicating if external search should be used
        """
        # Simple confidence-based external search escalation
        # If RAG response is short or contains uncertainty indicators, escalate
        if len(rag_response) < 200 or any(word in rag_response.lower() for word in ["i don't know", "not sure", "may vary", "consult"]):
            return True
        return False
    
    def get_routing_feedback(self, routing_decision: Dict[str, Any]) -> str:
        """
        Generate user-friendly feedback about the routing decision.
        
        Args:
            routing_decision: Result from route_query
            
        Returns:
            Feedback message for the user
        """
        agent_type = routing_decision.get("agent_type", "RAG")
        confidence = routing_decision.get("confidence", 0.5)
        reasoning = routing_decision.get("reasoning", "")
        
        feedback_messages = {
            "CALCULATOR": "I'll help you calculate your life insurance needs and recommend the right coverage amount.",
            "PORTFOLIO": "I'll analyze your portfolio and show how life insurance fits into your overall financial plan.",
            "EXTERNAL_SEARCH": "I'll search for the most current information to give you an accurate answer.",
            "RAG": "I'll provide you with comprehensive information from our knowledge base.",
            "RESEARCH": "I'll conduct a thorough analysis using multiple sources to answer your question."
        }
        
        base_message = feedback_messages.get(agent_type, "I'll help you with that.")
        
        if confidence < 0.7:
            base_message += " (I'm using my best judgment based on your query.)"
        
        return base_message 
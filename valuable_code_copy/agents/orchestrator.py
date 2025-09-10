"""
Multi-Agent Orchestrator for Financial Advisor Assistant

This orchestrator coordinates all specialized agents and manages the overall
conversation flow, routing queries to appropriate agents and combining responses.
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import MessagesPlaceholder
import json
import re

from .query_router import QueryRouterAgent
from .research_agent import ResearchAgent
from .calculator_agent import CalculatorAgent
from .portfolio_agent import PortfolioAgent
from .rag_agent import EnhancedRAGAgent as RAGAgent
from utils.confidence import assess_confidence_score
from config.settings import settings

class MultiAgentOrchestrator:
    """
    Orchestrates multiple specialized agents for comprehensive financial advisory services.
    """
    
    def __init__(self, llm: ChatOpenAI, rag_agent: RAGAgent, tavily_api_key: str):
        self.llm = llm
        self.rag_agent = rag_agent
        
        # Initialize all specialized agents
        self.query_router = QueryRouterAgent(llm)
        self.research_agent = ResearchAgent(llm, rag_agent, tavily_api_key)
        self.calculator_agent = CalculatorAgent(llm)
        self.portfolio_agent = PortfolioAgent(llm, self.calculator_agent)
        
        # Conversation state management
        self.session_context = {}
        self.conversation_history = []
        
        # Create orchestrator prompt for final response synthesis
        self.orchestrator_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the final response synthesizer for a Financial Advisor Life Insurance Assistant.

Your role is to combine responses from multiple specialized agents into a coherent, comprehensive response that:

1. **Addresses the user's query completely** - Ensure all aspects of the question are answered
2. **Provides actionable advice** - Give specific, implementable recommendations
3. **Maintains professional tone** - Use appropriate financial advisory language
4. **Integrates multiple perspectives** - Combine RAG knowledge, research, calculations, and portfolio analysis
5. **Prioritizes information** - Present most important information first
6. **Provides context** - Explain why recommendations are made
7. **Suggests next steps** - Guide the user on what to do next

**Response Structure:**
1. **Executive Summary**: Key findings and primary recommendations
2. **Detailed Analysis**: Comprehensive explanation with supporting evidence
3. **Specific Recommendations**: Actionable advice with rationale
4. **Implementation Steps**: Clear next steps for the user
5. **Follow-up Questions**: Relevant questions to gather more information if needed

**Integration Guidelines:**
- If multiple agents provided information, synthesize the best insights from each
- If there are conflicting recommendations, explain the trade-offs
- If information is incomplete, acknowledge limitations and suggest gathering more data
- Always emphasize life insurance as part of holistic financial planning
- Focus on practical advice for financial advisors and their clients

**Quality Standards:**
- Professional and educational tone
- Specific and actionable recommendations
- Clear rationale for all suggestions
- Appropriate level of detail for the user's expertise
- Balanced perspective on different options
"""),
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Create the orchestrator chain
        self.orchestrator_chain = self.orchestrator_prompt | self.llm | StrOutputParser()
    
    def process_query(self, query: str, session_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User's query
            session_context: Current session context
            
        Returns:
            Comprehensive response from the multi-agent system
        """
        # Update session context
        if session_context:
            self.session_context.update(session_context)
        
        # Step 1: Route the query to determine which agent(s) should handle it
        # Simple keyword-based routing to avoid LLM calls
        query_lower = query.lower().strip()
        
        # Greeting detection
        if query_lower in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy"]:
            agent_type = "GREETING"
        
        # Calculator detection
        elif any(word in query_lower for word in ["calculate", "how much", "coverage amount", "needs analysis", "policy type", "term vs whole", "coverage needs"]):
            agent_type = "CALCULATOR"
        
        # Portfolio detection
        elif any(word in query_lower for word in ["portfolio", "investment", "financial plan", "asset allocation", "risk assessment", "analyze my"]):
            agent_type = "PORTFOLIO"
        
        # Research/External search detection
        elif any(word in query_lower for word in ["current rates", "market conditions", "specific company", "latest", "recent changes", "current term", "market trends"]):
            agent_type = "RESEARCH"
        
        # Default to RAG for general knowledge questions
        else:
            agent_type = "RAG"
        
        # Step 2: Get response from appropriate agent(s)
        agent_responses = {}
        
        if agent_type == "RAG":
            # Basic RAG response
            rag_result = self.rag_agent.query(query)
            agent_responses["RAG"] = rag_result
            
            # Check if we should escalate to external search
            if self.query_router.should_escalate_to_external_search(rag_result.get("response", ""), query):
                research_result = self.research_agent.research_query(query, self.session_context)
                agent_responses["RESEARCH"] = research_result
                agent_type = "RESEARCH"
        
        elif agent_type == "CALCULATOR":
            # Calculator agent response
            calculator_result = self.calculator_agent.interactive_calculation(query, self.session_context)
            agent_responses["CALCULATOR"] = {
                "response": calculator_result,
                "agent_type": "CALCULATOR"
            }
        
        elif agent_type == "PORTFOLIO":
            # Portfolio analysis (requires uploaded data)
            if self.session_context.get("uploaded_files"):
                # This would be handled by file upload processing
                # For now, provide guidance
                agent_responses["PORTFOLIO"] = {
                    "response": "I can help analyze your portfolio for life insurance integration. Please upload your financial data (Excel, CSV, or PDF) to get started.",
                    "agent_type": "PORTFOLIO"
                }
            else:
                agent_responses["PORTFOLIO"] = {
                    "response": "To provide portfolio analysis, I'll need you to upload your financial data. You can upload Excel files, CSV files, or PDF statements.",
                    "agent_type": "PORTFOLIO"
                }
        
        elif agent_type == "EXTERNAL_SEARCH":
            # Research agent with external search
            research_result = self.research_agent.research_query(query, self.session_context)
            agent_responses["RESEARCH"] = research_result
        
        elif agent_type == "RESEARCH":
            # Comprehensive research combining RAG and external search
            research_result = self.research_agent.research_query(query, self.session_context)
            agent_responses["RESEARCH"] = research_result
        
        elif agent_type == "GREETING":
            # Simple greeting response
            greeting_responses = [
                "Hello! I'm your Financial Advisor Life Insurance Assistant. I'm here to help you with life insurance questions, coverage calculations, portfolio analysis, and more. How can I assist you today?",
                "Hi there! I'm ready to help you with life insurance and financial planning questions. What would you like to know?",
                "Hello! I'm your AI assistant specializing in life insurance and financial planning. I can help you calculate coverage needs, analyze portfolios, and provide comprehensive information. What can I help you with?"
            ]
            import random
            agent_responses["GREETING"] = {
                "response": random.choice(greeting_responses),
                "agent_type": "GREETING"
            }
        
        # Step 3: Synthesize responses from multiple agents if needed
        if len(agent_responses) > 1:
            final_response = self._synthesize_responses(query, agent_responses)
        else:
            # Single agent response
            agent_key = list(agent_responses.keys())[0]
            agent_response = agent_responses[agent_key]
            final_response = agent_response.get("response", "I'm unable to provide a response at this time.")
        
        # Step 4: Update conversation history
        self.conversation_history.append({
            "query": query,
            "agent_type": agent_type,
            "agent_responses": agent_responses,
            "final_response": final_response,
            "timestamp": self._get_timestamp()
        })
        
        # Step 5: Prepare response metadata
        response_metadata = {
            "agent_type": agent_type,
            "agents_used": list(agent_responses.keys()),
            "routing_decision": {"agent_type": agent_type, "confidence": 0.8},
            "confidence": self._calculate_overall_confidence(agent_responses),
            "session_context": self.session_context
        }
        
        return {
            "response": final_response,
            "metadata": response_metadata,
            "agent_responses": agent_responses
        }
    
    def _synthesize_responses(self, query: str, agent_responses: Dict[str, Any]) -> str:
        """
        Synthesize responses from multiple agents into a coherent response.
        
        Args:
            query: Original user query
            agent_responses: Responses from different agents
            
        Returns:
            Synthesized response
        """
        # Prepare synthesis context
        synthesis_context = {
            "query": query,
            "agent_responses": agent_responses,
            "session_context": self.session_context
        }
        
        # Generate synthesized response
        synthesized_response = self.orchestrator_chain.invoke({
            "messages": [HumanMessage(content=f"Synthesize responses for query: {json.dumps(synthesis_context)}")]
        })
        
        return synthesized_response
    
    def handle_file_upload(self, file_data: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """
        Handle uploaded file and route to appropriate agent for analysis.
        
        Args:
            file_data: Extracted data from uploaded file
            file_type: Type of uploaded file
            
        Returns:
            Analysis results from appropriate agent
        """
        if file_type in ["excel", "csv"]:
            # Portfolio analysis
            portfolio_result = self.portfolio_agent.analyze_uploaded_portfolio(file_data, self.session_context)
            
            # Update session context with portfolio data
            self.session_context["portfolio_data"] = portfolio_result.get("portfolio_data", {})
            self.session_context["uploaded_files"] = self.session_context.get("uploaded_files", []) + [file_type]
            
            return {
                "response": portfolio_result,
                "agent_type": "PORTFOLIO",
                "metadata": {
                    "file_type": file_type,
                    "analysis_type": "portfolio_analysis"
                }
            }
        
        elif file_type in ["pdf", "txt", "docx"]:
            # Add to RAG for session-specific knowledge
            # This would be handled by the file processing utilities
            return {
                "response": "Document uploaded and added to session knowledge base.",
                "agent_type": "RAG",
                "metadata": {
                    "file_type": file_type,
                    "action": "added_to_rag"
                }
            }
        
        else:
            return {
                "response": "File type not supported for analysis.",
                "agent_type": "SYSTEM",
                "metadata": {
                    "file_type": file_type,
                    "error": "unsupported_file_type"
                }
            }
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current conversation session.
        
        Returns:
            Conversation summary and insights
        """
        if not self.conversation_history:
            return {"summary": "No conversation history available."}
        
        # Analyze conversation patterns
        agent_usage = {}
        query_types = []
        
        for entry in self.conversation_history:
            agent_type = entry.get("agent_type", "UNKNOWN")
            agent_usage[agent_type] = agent_usage.get(agent_type, 0) + 1
            
            # Simple query type classification
            query = entry.get("query", "").lower()
            if any(word in query for word in ["calculate", "how much", "coverage"]):
                query_types.append("calculator")
            elif any(word in query for word in ["portfolio", "investment", "financial"]):
                query_types.append("portfolio")
            elif any(word in query for word in ["current", "rates", "market"]):
                query_types.append("research")
            else:
                query_types.append("general")
        
        return {
            "total_queries": len(self.conversation_history),
            "agent_usage": agent_usage,
            "query_types": query_types,
            "session_context": self.session_context,
            "conversation_history": self.conversation_history
        }
    
    def update_session_context(self, context_updates: Dict[str, Any]):
        """
        Update the session context with new information.
        
        Args:
            context_updates: New context information to add
        """
        self.session_context.update(context_updates)
    
    def clear_session(self):
        """
        Clear the current session context and conversation history.
        """
        self.session_context = {}
        self.conversation_history = []
    
    def _calculate_overall_confidence(self, agent_responses: Dict[str, Any]) -> float:
        """
        Calculate overall confidence score from multiple agent responses.
        
        Args:
            agent_responses: Responses from different agents
            
        Returns:
            Overall confidence score
        """
        confidence_scores = []
        
        for agent_name, response in agent_responses.items():
            if isinstance(response, dict):
                confidence = response.get("confidence", 0.5)
                confidence_scores.append(confidence)
            else:
                confidence_scores.append(0.5)  # Default confidence
        
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.5
    
    def _get_timestamp(self) -> str:
        """
        Get current timestamp for conversation history.
        
        Returns:
            Timestamp string
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """
        Get information about available agent capabilities.
        
        Returns:
            Dictionary describing agent capabilities
        """
        return {
            "RAG": {
                "description": "Knowledge base queries and general life insurance information",
                "capabilities": ["Policy explanations", "Industry knowledge", "Basic Q&A"],
                "best_for": "General questions about life insurance concepts and policies"
            },
            "CALCULATOR": {
                "description": "Life insurance needs analysis and coverage calculations",
                "capabilities": ["Needs analysis", "Coverage calculations", "Policy recommendations"],
                "best_for": "Determining how much life insurance coverage is needed"
            },
            "PORTFOLIO": {
                "description": "Portfolio analysis and life insurance integration",
                "capabilities": ["Portfolio analysis", "Risk assessment", "Integration planning"],
                "best_for": "Understanding how life insurance fits into overall financial planning"
            },
            "RESEARCH": {
                "description": "Current market research and external information",
                "capabilities": ["Market research", "Current rates", "External data"],
                "best_for": "Questions requiring current market information or external data"
            },
            "EXTERNAL_SEARCH": {
                "description": "External search for current information",
                "capabilities": ["Web search", "Current data", "Market updates"],
                "best_for": "Questions about current rates, market conditions, or specific companies"
            }
        } 
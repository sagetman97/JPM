"""
LLM-based supervisors for Financial Advisor LangGraph system.
Based on AIE7 course patterns with function calling and JSON output parsing.
"""

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage
import json


def create_main_supervisor(llm: ChatOpenAI) -> Any:
    """
    Create the main supervisor that routes queries to appropriate teams.
    Based on AIE7 course patterns for team supervision.
    """
    
    # Define routing options
    options = ["RESEARCH_TEAM", "ANALYSIS_TEAM", "GREETING", "FINISH"]
    
    function_def = {
        "name": "route",
        "description": "Select the next team or action to handle the user query.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [{"enum": options}],
                },
                "reasoning": {
                    "title": "Reasoning",
                    "type": "string",
                    "description": "Brief explanation of routing decision"
                }
            },
            "required": ["next", "reasoning"],
        },
    }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the main supervisor for a Financial Advisor Life Insurance Assistant.

Your job is to route user queries to the appropriate specialized team:

1. **RESEARCH_TEAM** - For questions about life insurance knowledge, current market information, and external research
   - Keywords: "what is", "explain", "current rates", "market conditions", "research", "latest"
   - Examples: "What is whole life insurance?", "Current term life rates", "Research different policies"

2. **ANALYSIS_TEAM** - For calculations, portfolio analysis, and financial planning
   - Keywords: "calculate", "how much", "portfolio", "coverage needs", "analyze", "financial plan"
   - Examples: "Calculate my coverage needs", "Analyze my portfolio", "How much insurance do I need?"

3. **GREETING** - For simple greetings and introductions
   - Keywords: "hi", "hello", "hey", "good morning", "good afternoon"
   - Examples: "Hello", "Hi there", "Good morning"

4. **FINISH** - When the query has been fully addressed

Analyze the user's query and route to the most appropriate team. Consider:
- Query intent and keywords
- User's current session context
- Whether the query requires research vs. analysis
- Whether it's a simple greeting

Return the appropriate team and reasoning for your decision."""),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, which team should handle this query? Select one of: {options}"),
    ]).partial(options=str(options))
    
    return (
        prompt
        | llm.bind_tools(tools=[function_def], tool_choice="route")
        | JsonOutputParser()
    )


def create_research_team_supervisor(llm: ChatOpenAI) -> Any:
    """
    Create the research team supervisor that routes between RAG and Search agents.
    Based on AIE7 course patterns for team supervision.
    """
    
    options = ["RAG_AGENT", "SEARCH_AGENT", "FINISH"]
    
    function_def = {
        "name": "route",
        "description": "Select the next research agent to handle the query.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [{"enum": options}],
                },
                "reasoning": {
                    "title": "Reasoning",
                    "type": "string",
                    "description": "Brief explanation of routing decision"
                }
            },
            "required": ["next", "reasoning"],
        },
    }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the supervisor for the Research Team of a Financial Advisor Life Insurance Assistant.

Your team has two agents:

1. **RAG_AGENT** - Access to comprehensive life insurance knowledge base
   - Use for: General knowledge questions, policy explanations, industry information
   - Keywords: "what is", "explain", "how does", "types of", "benefits of"
   - Examples: "What is whole life insurance?", "Explain term vs permanent"

2. **SEARCH_AGENT** - Current market information and external data
   - Use for: Current rates, market conditions, specific company information
   - Keywords: "current rates", "market conditions", "latest", "recent", "specific company"
   - Examples: "Current term life rates", "Latest market trends"

3. **FINISH** - When the research is complete

Route the query to the most appropriate research agent. Consider:
- Whether the query needs current market data vs. general knowledge
- Whether external search would provide more value than knowledge base
- The specificity and timeliness requirements of the query

Return the appropriate agent and reasoning for your decision."""),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, which research agent should handle this? Select one of: {options}"),
    ]).partial(options=str(options))
    
    return (
        prompt
        | llm.bind_tools(tools=[function_def], tool_choice="route")
        | JsonOutputParser()
    )


def create_analysis_team_supervisor(llm: ChatOpenAI) -> Any:
    """
    Create the analysis team supervisor that routes between Calculator and Portfolio agents.
    Based on AIE7 course patterns for team supervision.
    """
    
    options = ["CALCULATOR_AGENT", "PORTFOLIO_AGENT", "FINISH"]
    
    function_def = {
        "name": "route",
        "description": "Select the next analysis agent to handle the query.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next",
                    "anyOf": [{"enum": options}],
                },
                "reasoning": {
                    "title": "Reasoning",
                    "type": "string",
                    "description": "Brief explanation of routing decision"
                }
            },
            "required": ["next", "reasoning"],
        },
    }
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the supervisor for the Analysis Team of a Financial Advisor Life Insurance Assistant.

Your team has two agents:

1. **CALCULATOR_AGENT** - Life insurance needs analysis and coverage calculations
   - Use for: Coverage amount calculations, needs analysis, policy recommendations
   - Keywords: "calculate", "how much", "coverage needs", "needs analysis", "policy type"
   - Examples: "Calculate my coverage needs", "How much insurance do I need?"

2. **PORTFOLIO_AGENT** - Portfolio analysis and life insurance integration
   - Use for: Portfolio analysis, financial planning integration, uploaded data analysis
   - Keywords: "portfolio", "investment", "financial plan", "analyze my", "uploaded data"
   - Examples: "Analyze my portfolio", "How does insurance fit my investments?"

3. **FINISH** - When the analysis is complete

Route the query to the most appropriate analysis agent. Consider:
- Whether the query is about calculations vs. portfolio analysis
- Whether uploaded data is available for portfolio analysis
- Whether the query requires financial planning integration

Return the appropriate agent and reasoning for your decision."""),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Given the conversation above, which analysis agent should handle this? Select one of: {options}"),
    ]).partial(options=str(options))
    
    return (
        prompt
        | llm.bind_tools(tools=[function_def], tool_choice="route")
        | JsonOutputParser()
    ) 
"""
Research Team for Financial Advisor LangGraph system.
Based on AIE7 course patterns with function-calling agents and agent nodes.
"""

import functools
from typing import Any, Dict, List
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END
from .tools import (
    retrieve_life_insurance_knowledge,
    search_current_market_info,
    assess_confidence_and_escalate
)
from ..graph.supervisors import create_research_team_supervisor
from ..graph.state import FinancialAdvisorState


def create_agent(
    llm: ChatOpenAI,
    tools: List[BaseTool],
    system_prompt: str,
) -> AgentExecutor:
    """
    Create a function-calling agent following AIE7 course patterns.
    """
    system_prompt += (
        "\nWork autonomously according to your specialty, using the tools available to you."
        " Do not ask for clarification."
        " Your other team members will collaborate with you with their own specialties."
        " You are chosen for a reason!"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_functions_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools)
    return executor


def agent_node(state: FinancialAdvisorState, agent: AgentExecutor, name: str) -> Dict[str, Any]:
    """
    Agent node function following AIE7 course patterns.
    """
    result = agent.invoke(state)
    return {"messages": [HumanMessage(content=result["output"], name=name)]}


def create_research_team_graph(llm: ChatOpenAI) -> Any:
    """
    Create the research team LangGraph with RAG and Search agents.
    Based on AIE7 course patterns for team graphs.
    """
    
    # Create agents with their tools
    rag_agent = create_agent(
        llm,
        [retrieve_life_insurance_knowledge, assess_confidence_and_escalate],
        "You are a RAG agent specializing in life insurance knowledge. Use the knowledge base to answer questions about life insurance products, policies, and best practices."
    )
    
    search_agent = create_agent(
        llm,
        [search_current_market_info, assess_confidence_and_escalate],
        "You are a search agent specializing in current market information. Use external search to find current rates, market conditions, and industry trends."
    )
    
    # Create agent nodes
    rag_node = functools.partial(agent_node, agent=rag_agent, name="RAG_AGENT")
    search_node = functools.partial(agent_node, agent=search_agent, name="SEARCH_AGENT")
    
    # Create supervisor
    supervisor = create_research_team_supervisor(llm)
    
    # Build the graph
    research_graph = StateGraph(FinancialAdvisorState)
    
    # Add nodes
    research_graph.add_node("RAG_AGENT", rag_node)
    research_graph.add_node("SEARCH_AGENT", search_node)
    research_graph.add_node("supervisor", supervisor)
    
    # Add edges
    research_graph.add_edge("RAG_AGENT", "supervisor")
    research_graph.add_edge("SEARCH_AGENT", "supervisor")
    
    # Add conditional edges from supervisor
    research_graph.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "RAG_AGENT": "RAG_AGENT",
            "SEARCH_AGENT": "SEARCH_AGENT", 
            "FINISH": END
        }
    )
    
    # Set entry point
    research_graph.set_entry_point("supervisor")
    
    return research_graph.compile()


def create_research_chain(llm: ChatOpenAI) -> Any:
    """
    Create the research team chain for integration with main graph.
    Based on AIE7 course patterns for chain integration.
    """
    
    def enter_chain(message: str):
        """Enter the research team with a message."""
        return {
            "messages": [HumanMessage(content=message)],
            "team_members": ["RAG_AGENT", "SEARCH_AGENT"],
            "next": "",
            "session_context": {},
            "uploaded_files": [],
            "current_team": "RESEARCH_TEAM",
            "query": message,
            "final_response": None
        }
    
    research_graph = create_research_team_graph(llm)
    research_chain = enter_chain | research_graph
    
    return research_chain 
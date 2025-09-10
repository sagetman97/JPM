"""
Analysis Team for Financial Advisor LangGraph system.
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
    calculate_coverage_needs,
    analyze_portfolio_for_insurance,
    assess_confidence_and_escalate
)
from ..graph.supervisors import create_analysis_team_supervisor
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


def create_analysis_team_graph(llm: ChatOpenAI) -> Any:
    """
    Create the analysis team LangGraph with Calculator and Portfolio agents.
    Based on AIE7 course patterns for team graphs.
    """
    
    # Create agents with their tools
    calculator_agent = create_agent(
        llm,
        [calculate_coverage_needs, assess_confidence_and_escalate],
        "You are a calculator agent specializing in life insurance needs analysis. Use calculation tools to determine coverage amounts, policy recommendations, and financial planning needs."
    )
    
    portfolio_agent = create_agent(
        llm,
        [analyze_portfolio_for_insurance, assess_confidence_and_escalate],
        "You are a portfolio agent specializing in financial planning integration. Use portfolio analysis tools to understand how life insurance fits into overall financial planning."
    )
    
    # Create agent nodes
    calculator_node = functools.partial(agent_node, agent=calculator_agent, name="CALCULATOR_AGENT")
    portfolio_node = functools.partial(agent_node, agent=portfolio_agent, name="PORTFOLIO_AGENT")
    
    # Create supervisor
    supervisor = create_analysis_team_supervisor(llm)
    
    # Build the graph
    analysis_graph = StateGraph(FinancialAdvisorState)
    
    # Add nodes
    analysis_graph.add_node("CALCULATOR_AGENT", calculator_node)
    analysis_graph.add_node("PORTFOLIO_AGENT", portfolio_node)
    analysis_graph.add_node("supervisor", supervisor)
    
    # Add edges
    analysis_graph.add_edge("CALCULATOR_AGENT", "supervisor")
    analysis_graph.add_edge("PORTFOLIO_AGENT", "supervisor")
    
    # Add conditional edges from supervisor
    analysis_graph.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "CALCULATOR_AGENT": "CALCULATOR_AGENT",
            "PORTFOLIO_AGENT": "PORTFOLIO_AGENT", 
            "FINISH": END
        }
    )
    
    # Set entry point
    analysis_graph.set_entry_point("supervisor")
    
    return analysis_graph.compile()


def create_analysis_chain(llm: ChatOpenAI) -> Any:
    """
    Create the analysis team chain for integration with main graph.
    Based on AIE7 course patterns for chain integration.
    """
    
    def enter_chain(message: str):
        """Enter the analysis team with a message."""
        return {
            "messages": [HumanMessage(content=message)],
            "team_members": ["CALCULATOR_AGENT", "PORTFOLIO_AGENT"],
            "next": "",
            "session_context": {},
            "uploaded_files": [],
            "current_team": "ANALYSIS_TEAM",
            "query": message,
            "final_response": None
        }
    
    analysis_graph = create_analysis_team_graph(llm)
    analysis_chain = enter_chain | analysis_graph
    
    return analysis_chain 
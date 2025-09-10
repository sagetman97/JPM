"""
State management for Financial Advisor LangGraph system.
Based on AIE7 course patterns with TypedDict and operator.add for message accumulation.
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
import operator
from langgraph.graph.message import add_messages


class FinancialAdvisorState(TypedDict):
    """
    State management for the Financial Advisor LangGraph system.
    
    Based on patterns from AIE7 course materials:
    - messages: Accumulated conversation messages
    - team_members: Available agents in current team
    - next: Next agent to execute
    - session_context: User session data
    - uploaded_files: Files uploaded for analysis
    - current_team: Which team is currently active
    """
    messages: Annotated[List[BaseMessage], add_messages]
    team_members: List[str]
    next: str
    session_context: Dict[str, Any]
    uploaded_files: List[str]
    current_team: str
    query: str
    final_response: Optional[str] 
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    """Types of chat messages"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class IntentCategory(str, Enum):
    """Categories of user intent"""
    LIFE_INSURANCE_EDUCATION = "life_insurance_education"
    INSURANCE_NEEDS_CALCULATION = "insurance_needs_calculation"
    PORTFOLIO_INTEGRATION_ANALYSIS = "portfolio_integration_analysis"
    CLIENT_ASSESSMENT_SUPPORT = "client_assessment_support"
    PRODUCT_COMPARISON = "product_comparison"
    SCENARIO_ANALYSIS = "scenario_analysis"
    GENERAL_FINANCIAL_ADVICE = "general_financial_advice"
    CALCULATOR_SELECTION_CHOICE = "calculator_selection_choice"
    CALCULATOR_CHOICE_SELECTED = "calculator_choice_selected"

class CalculatorType(str, Enum):
    """Types of insurance calculators"""
    QUICK = "quick"
    DETAILED = "detailed"
    PORTFOLIO = "portfolio"
    NONE = "none"

class RouteType(str, Enum):
    """Types of routing decisions"""
    RAG = "rag"
    EXTERNAL_SEARCH = "external_search"
    QUICK_CALCULATOR = "quick_calculator"
    EXTERNAL_TOOL = "external_tool"
    BASE_LLM = "base_llm"
    CALCULATOR_SELECTION = "calculator_selection"

class KnowledgeLevel(str, Enum):
    """User knowledge levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class ChatMessage(BaseModel):
    """Individual chat message"""
    id: str = Field(..., description="Unique message ID")
    type: MessageType = Field(..., description="Type of message")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    files: Optional[List[str]] = Field(default=[], description="Associated file IDs")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class IntentResult(BaseModel):
    """Result of intent classification"""
    intent: IntentCategory = Field(..., description="Classified intent category")
    semantic_goal: str = Field(..., description="What the user really wants")
    calculator_type: Optional[CalculatorType] = Field(None, description="Type of calculator needed")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field(..., description="Reasoning for classification")
    follow_up_clarification: Optional[List[str]] = Field(None, description="Questions to confirm understanding")
    needs_external_search: bool = Field(False, description="Whether this query needs external search supplementation")
    needs_calculator_selection: bool = Field(False, description="Whether user needs to choose calculator type")
    suggested_calculator: Optional[str] = Field(None, description="Suggested calculator type based on semantic analysis")

class RoutingDecision(BaseModel):
    """Routing decision for a query"""
    route_type: RouteType = Field(..., description="Type of route to take")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in routing decision")
    reasoning: str = Field(..., description="Reasoning for routing decision")
    tool_type: Optional[str] = Field(None, description="Type of tool if external tool route")
    session_id: Optional[str] = Field(None, description="Session ID for tool integration")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata for routing decisions")

class ConversationContext(BaseModel):
    """Context for conversation understanding"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    knowledge_level: KnowledgeLevel = Field(default=KnowledgeLevel.BEGINNER, description="User's knowledge level")
    semantic_themes: List[str] = Field(default=[], description="Themes from conversation")
    user_goals: List[str] = Field(default=[], description="User's expressed goals")
    current_topic: Optional[str] = Field(default=None, description="Current conversation topic")
    previous_calculations: List[Dict[str, Any]] = Field(default=[], description="Previous calculation results")
    client_context: Optional[str] = Field(default="personal", description="Whether this is personal or client assessment")
    needs_external_search: bool = Field(default=False, description="Whether external search is needed for current query")
    current_intent: Optional[IntentResult] = Field(default=None, description="Current intent for search decision logic")
    
    # NEW: Calculator session management
    calculator_session: Optional[Dict[str, Any]] = Field(default=None, description="Active calculator session state")
    calculator_type: Optional[CalculatorType] = Field(default=None, description="Selected calculator type")
    calculator_state: Optional[str] = Field(default=None, description="Current calculator state: 'selecting', 'active', 'completed'")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Context creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")

class RAGResult(BaseModel):
    """Result from RAG system"""
    response: str = Field(..., description="Generated response")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score of response")
    source_documents: List[Dict[str, Any]] = Field(default=[], description="Source documents used")
    semantic_queries: List[str] = Field(default=[], description="Semantic queries used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in RAG response")

class SearchResult(BaseModel):
    """Result from external search"""
    response: str = Field(..., description="Generated response from search")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score of search results")
    source_results: List[Dict[str, Any]] = Field(default=[], description="Source search results")
    original_query: str = Field(..., description="Original search query")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in search response")

class CalculatorSelection(BaseModel):
    """Result of calculator selection"""
    selected_calculator: CalculatorType = Field(..., description="Selected calculator type")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in selection")
    semantic_reasoning: str = Field(..., description="Semantic reasoning for selection")
    clarification_questions: List[str] = Field(default=[], description="Questions to confirm understanding")
    expected_outcome: str = Field(..., description="What they'll get from this calculator")

class ToolResponse(BaseModel):
    """Response from tool integration"""
    tool_type: str = Field(..., description="Type of tool used")
    action: str = Field(..., description="Action to take")
    url: Optional[str] = Field(None, description="URL for external tools")
    message: str = Field(..., description="Message explaining the action")
    session_id: Optional[str] = Field(None, description="Session ID for context preservation")

class QualityScore(BaseModel):
    """Quality evaluation scores"""
    overall_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality score")
    ragas_scores: Optional[Dict[str, float]] = Field(None, description="RAGAS evaluation scores")
    semantic_scores: Optional[Dict[str, float]] = Field(None, description="Semantic quality scores")
    satisfaction_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Predicted user satisfaction")
    improvement_areas: List[str] = Field(default=[], description="Areas for improvement")

class ComplianceResult(BaseModel):
    """Result of compliance review"""
    original_response: str = Field(..., description="Original response before compliance review")
    final_response: str = Field(..., description="Final response after compliance review")
    legal_compliance: Dict[str, Any] = Field(default={}, description="Legal compliance details")
    risk_assessment: Dict[str, Any] = Field(default={}, description="Risk assessment results")
    disclaimers: List[str] = Field(default=[], description="Required disclaimers")
    was_rewritten: bool = Field(default=False, description="Whether response was rewritten")

class ChatResponse(BaseModel):
    """Final chat response"""
    content: str = Field(..., description="Response content")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    routing_decision: RoutingDecision = Field(..., description="Routing decision made")
    disclaimers: List[str] = Field(default=[], description="Required disclaimers")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

class FileUpload(BaseModel):
    """File upload information"""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type/extension")
    file_size: int = Field(..., description="File size in bytes")
    upload_time: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    content_hash: str = Field(..., description="Content hash for deduplication")

class ChatSession(BaseModel):
    """Chat session information"""
    session_id: str = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    messages: List[ChatMessage] = Field(default=[], description="Session messages")
    context: ConversationContext = Field(..., description="Session context")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity time")
    status: str = Field(default="active", description="Session status")
    
    def add_message(self, message: ChatMessage):
        """Add a message to the session"""
        self.messages.append(message)
        self.last_activity = datetime.utcnow()
    
    def get_context(self) -> ConversationContext:
        """Get the session context"""
        return self.context
    
    def update_context(self, **kwargs):
        """Update the session context"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        self.context.updated_at = datetime.utcnow()
        self.last_activity = datetime.utcnow() 
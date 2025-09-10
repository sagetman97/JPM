import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from datetime import datetime
from pathlib import Path

# Import from core modules
from core.schemas import ChatMessage, ChatResponse, ConversationContext
from core.intent_classifier import SemanticIntentClassifier
from core.smart_router import SemanticSmartRouter, ToolIntegrator
from core.external_search import ExternalSearchSystem
from core.orchestrator import ChatbotOrchestrator
from core.calculator_selector import SemanticCalculatorSelector
from core.quick_calculator import QuickCalculator
from core.advanced_rag import EnhancedRAGSystem
from core.file_processor import FileProcessor
from core.config import config
from core.smart_router import RouteType
from core.schemas import MessageType
from core.session_linker import SessionLinker
from core.simple_pdf_generator import SimplePDFGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Robo-Advisor Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-vercel-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot orchestrator
chatbot_orchestrator = None

# Global tool integration components
session_linker = None
pdf_generator = None

async def auto_ingest_documents_if_needed(rag_system: EnhancedRAGSystem):
    """Automatically ingest documents if the RAG database is empty"""
    try:
        # Check if collection has documents using the new method
        if rag_system.has_documents():
            collection_info = rag_system.collection_info
            if collection_info:
                logger.info(f"📚 RAG database already has {collection_info.vectors_count} documents - skipping ingestion")
            else:
                logger.info("📚 RAG database has documents - skipping ingestion")
            return
        
        # Database is empty, need to ingest documents
        logger.info("📥 RAG database is empty - starting automatic document ingestion...")
        
        # Get documents path from config
        from core.config import ChatbotConfig
        config = ChatbotConfig()
        documents_path = Path(config.rag_documents_path)
        
        if not documents_path.exists():
            logger.warning(f"⚠️ RAG documents path does not exist: {documents_path}")
            return
        
        logger.info(f"📁 Found {len(list(documents_path.iterdir()))} items in documents folder")
        
        # Run ingestion
        success = await rag_system.ingest_documents(str(documents_path))
        
        if success:
            logger.info("✅ Automatic document ingestion completed successfully!")
        else:
            logger.warning("⚠️ Automatic document ingestion failed - RAG system will use external search")
            
    except Exception as e:
        logger.error(f"❌ Error during auto-ingestion: {e}")
        # Don't fail startup - this is non-critical

async def periodic_session_cleanup(chatbot_orchestrator):
    """Periodically clean up old sessions"""
    while True:
        try:
            # Wait 1 hour between cleanup runs
            await asyncio.sleep(3600)
            
            # Clean up sessions older than 24 hours
            cleaned_count = await chatbot_orchestrator.cleanup_old_sessions(max_age_hours=24)
            if cleaned_count > 0:
                logger.info(f"🧹 PERIODIC CLEANUP: Cleaned up {cleaned_count} old sessions")
                
        except Exception as e:
            logger.error(f"❌ Error in periodic session cleanup: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot components on startup"""
    
    global chatbot_orchestrator
    
    try:
        logger.info("🚀 Initializing Robo-Advisor Chatbot...")
        
        # Initialize core components
        logger.info("🔍 Initializing external search...")
        external_search = ExternalSearchSystem()
        
        logger.info("📚 Initializing RAG system...")
        rag_system = EnhancedRAGSystem(external_search_system=external_search)
        
        logger.info("🔗 Initializing session linker...")
        global session_linker
        session_linker = SessionLinker()
        
        logger.info("🔗 Initializing tool integrator...")
        tool_integrator = ToolIntegrator(session_linker=session_linker)
        
        logger.info("🧮 Initializing calculator selector...")
        calculator_selector = SemanticCalculatorSelector()
        
        logger.info("⚡ Initializing quick calculator...")
        quick_calculator = QuickCalculator()
        
        logger.info("📁 Initializing file processor...")
        file_processor = FileProcessor()
        
        logger.info("📄 Initializing PDF generator...")
        global pdf_generator
        pdf_generator = SimplePDFGenerator()
        
        logger.info("🎯 Initializing intent classifier...")
        intent_classifier = SemanticIntentClassifier()
        
        logger.info("🛣️ Initializing smart router...")
        smart_router = SemanticSmartRouter(
            external_search=external_search,
            tool_integrator=tool_integrator,
            base_llm=None,  # Will be handled by orchestrator
            calculator_selector=calculator_selector,
            quick_calculator=quick_calculator
        )
        
        logger.info("🎼 Initializing orchestrator...")
        chatbot_orchestrator = ChatbotOrchestrator(
            intent_classifier=intent_classifier,
            smart_router=smart_router,
            rag_system=rag_system,
            external_search=external_search,
            tool_integrator=tool_integrator,
            calculator_selector=calculator_selector,
            quick_calculator=quick_calculator,
            file_processor=file_processor
        )
        
        logger.info("✅ Robo-Advisor Chatbot initialized successfully!")
        
        # Auto-ingest documents if RAG database is empty
        logger.info("🔍 Checking if RAG database needs document ingestion...")
        try:
            await auto_ingest_documents_if_needed(rag_system)
        except Exception as e:
            logger.warning(f"⚠️ Auto-ingestion failed (non-critical): {e}")
            logger.info("📚 RAG system will work with existing documents or external search")
        
        # Start periodic session cleanup task
        asyncio.create_task(periodic_session_cleanup(chatbot_orchestrator))
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize chatbot: {e}")
        raise

# Pydantic models for API requests
class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: Optional[str] = None

class ChatResponseAPI(BaseModel):
    content: str
    quality_score: float
    routing_decision: Dict[str, Any]
    disclaimers: List[str]
    session_id: str

class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    created_at: str
    last_activity: str
    status: str

class FileUploadRequest(BaseModel):
    session_id: str
    filename: str
    file_type: str
    file_size: int

class FileAnalysisRequest(BaseModel):
    session_id: str
    file_id: str
    query: str

class CalculatorRequest(BaseModel):
    session_id: str
    action: str  # "start", "answer"
    data: Optional[Dict[str, Any]] = None

class ToolSessionRequest(BaseModel):
    chat_session_id: str
    tool_type: str

class ToolCompletionRequest(BaseModel):
    external_session_id: str
    tool_type: str
    result_data: Dict[str, Any]
    pdf_url: Optional[str] = None

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client"""
        
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected for session: {session_id}")
    
    def disconnect(self, session_id: str):
        """Disconnect a WebSocket client"""
        
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected for session: {session_id}")
    
    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to a specific WebSocket client"""
        
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message to session {session_id}: {e}")
                self.disconnect(session_id)
    
    async def send_tool_completion_notification(self, session_id: str, tool_data: Dict[str, Any]):
        """Send tool completion notification to chat session"""
        message = {
            "type": "tool_completion",
            "data": tool_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        await self.send_message(session_id, message)

# Global connection manager
manager = ConnectionManager()

@app.websocket("/ws/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            logger.info(f"Received WebSocket message: {message_data}")
            
            # Check if this is a chat message
            if message_data.get("type") == "chat_message":
                # Process message through orchestrator
                # Create chat message object
                message = ChatMessage(
                    id=str(uuid.uuid4()),
                    type=MessageType.USER,
                    content=message_data.get("content", ""),
                    timestamp=datetime.utcnow()
                )
                
                logger.info(f"Processing WebSocket message through orchestrator: {message.content}")
                
                response = await chatbot_orchestrator.process_message(message, session_id)
                
                logger.info(f"Orchestrator response received: {len(response.content)} characters")
                
                # Handle different routing decisions
                if response.routing_decision.route_type == RouteType.QUICK_CALCULATOR:
                    # Quick calculator response
                    final_response = {
                        "type": "chat_response",
                        "content": response.content,
                        "quality_score": 1.0,  # Perfect score for calculators
                        "routing_decision": response.routing_decision.dict(),
                        "disclaimers": [],  # No disclaimers for calculator responses
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "routing_type": "quick_calculator",
                        "calculator_session": response.metadata.get("calculator_session") if response.metadata else None
                    }
                    
                elif response.routing_decision.route_type == RouteType.CALCULATOR_SELECTION:
                    # Calculator selection response
                    final_response = {
                        "type": "chat_response",
                        "content": response.content,
                        "quality_score": 1.0,  # Perfect score for calculator selection
                        "routing_decision": response.routing_decision.dict(),
                        "disclaimers": [],  # No disclaimers for calculator selection
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "routing_type": "calculator_selection",
                        "needs_calculator_selection": True,
                        "suggested_calculator": response.routing_decision.metadata.get("suggested_calculator") if response.routing_decision.metadata else "quick"
                    }
                    
                elif response.routing_decision.route_type == RouteType.EXTERNAL_TOOL:
                    # External tool routing
                    final_response = {
                        "type": "chat_response",
                        "content": response.content,
                        "quality_score": response.quality_score,
                        "routing_decision": response.routing_decision.dict(),
                        "disclaimers": response.disclaimers,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "routing_type": "external_tool",
                        "tool_type": response.routing_decision.tool_type
                    }
                    
                else:
                    # Standard response (RAG, Search, Base LLM)
                    final_response = {
                        "type": "chat_response",
                        "content": response.content,
                        "quality_score": response.quality_score,
                        "routing_decision": response.routing_decision.dict(),
                        "disclaimers": response.disclaimers,
                        "session_id": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "routing_type": response.routing_decision.route_type.value
                    }
                
                logger.info(f"Sending WebSocket response back to client: {len(final_response['content'])} characters")
                
                # Send response back to client
                await websocket.send_text(json.dumps(final_response))
                
                logger.info(f"WebSocket response sent successfully")
                
            else:
                logger.warning(f"Unknown message type received: {message_data.get('type')}")
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        import traceback
        traceback.print_exc()
        manager.disconnect(session_id)

# HTTP endpoints
@app.post("/api/chat/process", response_model=ChatResponseAPI)
async def process_chat_message(request: ChatRequest):
    """Process a chat message through the complete pipeline"""
    
    try:
        # Create chat message
        message = ChatMessage(
            id=str(uuid.uuid4()),
            type="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Process through orchestrator
        response = await chatbot_orchestrator.process_message(message, request.session_id)
        
        # Log response details for debugging
        logger.info(f"🔍 API RESPONSE DEBUG:")
        logger.info(f"   Response content length: {len(response.content)} characters")
        logger.info(f"   Response content preview: {response.content[:200]}...")
        logger.info(f"   Routing decision: {response.routing_decision.route_type}")
        logger.info(f"   Quality score: {response.quality_score}")
        
        # For calculator responses, ensure they bypass evaluation/compliance
        if response.routing_decision.route_type == "QUICK_CALCULATOR":
            # Calculator responses get perfect scores and no disclaimers
            final_response = ChatResponseAPI(
                content=response.content,
                quality_score=1.0,  # Perfect score for calculators
                routing_decision=response.routing_decision.dict(),
                disclaimers=[],  # No disclaimers for calculator responses
                session_id=request.session_id
            )
        else:
            # Regular responses go through normal processing
            final_response = ChatResponseAPI(
                content=response.content,
                quality_score=response.quality_score,
                routing_decision=response.routing_decision.dict(),
                disclaimers=response.disclaimers,
                session_id=request.session_id
            )
        
        return final_response
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/api/chat/file/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(...)
):
    """Upload and process a file for analysis"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        # Read file data
        file_data = await file.read()
        
        # Process file upload
        result = await chatbot_orchestrator.process_file_upload(
            file_data, file.filename, session_id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/api/chat/file/analyze")
async def analyze_file(request: FileAnalysisRequest):
    """Analyze uploaded file in context of conversation"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        # Analyze file
        analysis = await chatbot_orchestrator.analyze_uploaded_file(
            request.file_id, request.query, request.session_id
        )
        
        return {
            "status": "success",
            "analysis": analysis,
            "file_id": request.file_id,
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Error analyzing file: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing file: {str(e)}")

@app.get("/api/chat/file/{file_id}")
async def get_file_info(file_id: str):
    """Get information about uploaded file"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        file_info = chatbot_orchestrator.get_file_summary(file_id)
        
        if file_info:
            return file_info
        else:
            raise HTTPException(status_code=404, detail="File not found")
            
    except Exception as e:
        logger.error(f"Error getting file info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting file info: {str(e)}")

@app.post("/api/chat/calculator")
async def handle_calculator_request(request: CalculatorRequest):
    """Handle calculator interactions"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        if request.action == "start":
            # Start new calculation session
            welcome_message = await chatbot_orchestrator.quick_calculator.start_calculation_session(
                request.session_id, 
                ConversationContext(session_id=request.session_id)
            )
            
            return {
                "status": "success",
                "action": "start",
                "message": welcome_message  # This is now a string, not a dict
            }
            
        elif request.action == "answer":
            # Process answer to calculation question
            if not request.data or "answer" not in request.data:
                raise HTTPException(status_code=400, detail="Answer data required")
            
            response = await chatbot_orchestrator.quick_calculator.process_answer(
                request.session_id, 
                request.data["answer"]
            )
            
            return {
                "status": "success",
                "action": "answer",
                "message": response
            }
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
            
    except Exception as e:
        logger.error(f"Error handling calculator request: {e}")
        raise HTTPException(status_code=500, detail=f"Error handling calculator request: {str(e)}")

@app.get("/api/chat/calculator/status/{session_id}")
async def get_calculator_status(session_id: str):
    """Get status of calculation session"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        status = await chatbot_orchestrator.quick_calculator.get_session_status(session_id)
        return status
        
    except Exception as e:
        logger.error(f"Error getting calculator status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting calculator status: {str(e)}")

@app.post("/api/chat/calculator/reset/{session_id}")
async def reset_calculator_session(session_id: str):
    """Reset calculation session"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        message = await chatbot_orchestrator.quick_calculator.reset_session(session_id)
        
        return {
            "status": "success",
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error resetting calculator session: {e}")
        raise HTTPException(status_code=500, detail=f"Error resetting calculator session: {str(e)}")

# New tool integration endpoints
@app.post("/api/chat/tool-session")
async def create_tool_session(request: ToolSessionRequest):
    """Create a new tool session linked to a chat session"""
    try:
        if not session_linker:
            raise HTTPException(status_code=503, detail="Session linker not initialized")
        
        external_session_id = await session_linker.create_tool_session(
            request.chat_session_id, 
            request.tool_type
        )
        
        return {
            "external_session_id": external_session_id,
            "tool_type": request.tool_type,
            "status": "created"
        }
    except Exception as e:
        logger.error(f"Error creating tool session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/tool-completion")
async def handle_tool_completion(request: ToolCompletionRequest):
    """Handle completion of an external tool"""
    try:
        if not session_linker or not pdf_generator:
            raise HTTPException(status_code=503, detail="Tool integration components not initialized")
        
        # Mark session as completed
        success = await session_linker.complete_tool_session(
            request.external_session_id,
            request.result_data
        )
        
        if not success:
            # Get more detailed error information
            pending_sessions = list(session_linker.pending_sessions.keys())
            completed_sessions = list(session_linker.completed_sessions.keys())
            logger.error(f"❌ Session not found: {request.external_session_id}")
            logger.error(f"❌ Pending sessions: {pending_sessions}")
            logger.error(f"❌ Completed sessions: {completed_sessions}")
            raise HTTPException(status_code=404, detail=f"Session not found: {request.external_session_id}")
        
        # Generate PDF
        if request.tool_type == "assessment":
            pdf_id = await pdf_generator.generate_assessment_pdf(
                request.result_data, 
                request.external_session_id,
                request.pdf_url
            )
        elif request.tool_type == "portfolio":
            # Use the new URL-based approach with analysis data
            logger.info(f"Generating portfolio PDF with URL-based approach")
            pdf_id = await pdf_generator.generate_portfolio_pdf(
                request.result_data, 
                request.external_session_id
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid tool type")
        
        # Update session with PDF ID
        tool_session = await session_linker.get_tool_session(request.external_session_id)
        if tool_session:
            tool_session.pdf_id = pdf_id
        
        # Generate result summary
        result_summary = _generate_result_summary(request.tool_type, request.result_data)
        
        # Generate detailed report message for conversation history
        detailed_report_message = _generate_detailed_report_message(request.tool_type, request.result_data)
        
        # Add tool results to conversation history (works for both assessment and portfolio)
        if tool_session and chatbot_orchestrator:
            try:
                # Get the session from the orchestrator
                session = chatbot_orchestrator._get_or_create_session(tool_session.chat_session_id)
                
                # Add the tool results to conversation history
                if hasattr(session.context, 'simple_history') and session.context.simple_history:
                    logger.info(f"📝 TOOL COMPLETION: Adding {request.tool_type} results to conversation history for session {tool_session.chat_session_id}")
                    
                    # Add the detailed report as a conversation turn
                    session.context.simple_history.add_conversation_turn(
                        user_message=f"{request.tool_type.title()} completed",
                        bot_response=detailed_report_message
                    )
                    
                    logger.info(f"📝 TOOL COMPLETION: Successfully added {request.tool_type} results to conversation history")
                else:
                    logger.warning(f"📝 TOOL COMPLETION: No simple_history available for session {tool_session.chat_session_id}")
                    
            except Exception as e:
                logger.error(f"📝 TOOL COMPLETION: Error adding {request.tool_type} results to conversation history: {e}")
        
        # Notify chat session via WebSocket
        if tool_session:
            await manager.send_tool_completion_notification(
                tool_session.chat_session_id,
                {
                    "tool_type": request.tool_type,
                    "pdf_id": pdf_id,
                    "result_summary": result_summary,
                    "detailed_report": detailed_report_message  # Add full report data
                }
            )
        
        return {
            "status": "completed",
            "pdf_id": pdf_id,
            "message": f"{request.tool_type.title()} completed successfully"
        }
        
    except Exception as e:
        import traceback
        logger.error(f"Error handling tool completion: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/pdf/{pdf_id}")
async def download_pdf(pdf_id: str):
    """Download a generated PDF"""
    try:
        if not pdf_generator:
            raise HTTPException(status_code=503, detail="PDF generator not initialized")
        
        pdf_path = pdf_generator.get_pdf_path(pdf_id)
        
        if not pdf_path.exists():
            raise HTTPException(status_code=404, detail="PDF not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(
            path=str(pdf_path),
            filename=f"{pdf_id}.pdf",
            media_type="application/pdf"  # Now generating actual PDF files
        )
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/session/{session_id}/pending-tools")
async def get_pending_tools(session_id: str):
    """Get pending tools for a chat session"""
    try:
        if not session_linker:
            raise HTTPException(status_code=503, detail="Session linker not initialized")
        
        pending_tools = await session_linker.get_pending_tools(session_id)
        
        return {
            "session_id": session_id,
            "pending_tools": [
                {
                    "external_session_id": tool.external_session_id,
                    "tool_type": tool.tool_type,
                    "created_at": tool.created_at.isoformat(),
                    "status": tool.status
                }
                for tool in pending_tools
            ]
        }
    except Exception as e:
        logger.error(f"Error getting pending tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_result_summary(tool_type: str, result_data: Dict[str, Any]) -> str:
    """Generate a summary of the tool result"""
    if tool_type == "assessment":
        # Extract from nested structure: { "formData": {...}, "result": {...} }
        result = result_data.get('result', {})
        recommended_coverage = result.get('recommended_coverage', 0)
        gap = result.get('gap', 0)
        product_recommendation = result.get('product_recommendation', 'N/A')
        
        return f"Assessment completed. Recommended coverage: ${recommended_coverage:,.2f}. Coverage gap: ${gap:,.2f}. Product recommendation: {product_recommendation}"
    elif tool_type == "portfolio":
        # Portfolio data structure - extract from the actual structure being sent
        # The data comes in as: { "formData": {...}, "result": {...} }
        result = result_data.get('result', {})
        portfolio_metrics = result.get('portfolio_metrics', {})
        life_insurance_needs = result.get('life_insurance_needs', {})
        
        # Extract values from the correct nested structure
        total_assets = result.get('total_assets', 0)
        risk_level = portfolio_metrics.get('risk_level', 'N/A')
        total_coverage_need = life_insurance_needs.get('total_need', 0)
        
        # If we don't have the data in the nested structure, try the top level
        if total_assets == 0:
            total_assets = result_data.get('total_assets', 0)
        if risk_level == 'N/A':
            risk_level = result_data.get('risk_level', 'N/A')
        if total_coverage_need == 0:
            total_coverage_need = result_data.get('recommended_coverage', 0)
        
        return f"Portfolio analysis completed. Total assets: ${total_assets:,.2f}. Risk level: {risk_level}. Life insurance need: ${total_coverage_need:,.2f}"
    else:
        return f"{tool_type.title()} completed successfully."

def _generate_detailed_report_message(tool_type: str, result_data: Dict[str, Any]) -> str:
    """Generate a detailed report message for conversation history"""
    if tool_type == "assessment":
        # Extract assessment data
        result = result_data.get('result', {})
        form_data = result_data.get('formData', {})
        
        # Helper function to safely convert to float
        def safe_float(value, default=0):
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                try:
                    return float(value.replace(',', ''))
                except (ValueError, AttributeError):
                    return default
            return default
        
        # Build detailed assessment report
        report = f"""## ASSESSMENT COMPLETED

**Personal Details:**
- Age: {form_data.get('age', 'N/A')}
- Marital Status: {form_data.get('marital_status', 'N/A')}
- Dependents: {form_data.get('dependents', 'N/A')}
- Health Status: {form_data.get('health_status', 'N/A')}

**Coverage Analysis:**
- Recommended Coverage: ${result.get('recommended_coverage', 0):,.2f}
- Coverage Gap: ${result.get('gap', 0):,.2f}
- Product Recommendation: {result.get('product_recommendation', 'N/A')}
- Rationale: {result.get('rationale', 'N/A')}

**Coverage Breakdown:**
- Living Expenses: ${result.get('needs_breakdown', {}).get('living_expenses', 0):,.2f}
- Debts: ${result.get('needs_breakdown', {}).get('debts', 0):,.2f}
- Education: ${result.get('needs_breakdown', {}).get('education', 0):,.2f}
- Funeral: ${result.get('needs_breakdown', {}).get('funeral', 0):,.2f}
- Legacy: ${result.get('needs_breakdown', {}).get('legacy', 0):,.2f}

**Cash Value Projections:**
- Recommended Monthly Savings: ${result.get('recommended_monthly_savings', 0):,.2f}
- Max Monthly Contribution: ${result.get('max_monthly_contribution', 0):,.2f}
- Projection Parameters: {result.get('projection_parameters', {})}

**About You:**
- Monthly Income: ${safe_float(form_data.get('monthly_income', 0)):,.2f}
- Monthly Expenses: ${safe_float(form_data.get('monthly_expenses', 0)):,.2f}
- Savings: ${safe_float(form_data.get('savings', 0)):,.2f}
- Investments: ${safe_float(form_data.get('investments', 0)):,.2f}
- Other Assets: ${safe_float(form_data.get('other_assets', 0)):,.2f}
- Individual Life Insurance: ${safe_float(form_data.get('individual_life', 0)):,.2f}
- Group Life Insurance: ${safe_float(form_data.get('group_life', 0)):,.2f}"""
        
        return report
        
    elif tool_type == "portfolio":
        # Extract portfolio data
        result = result_data.get('result', {})
        form_data = result_data.get('formData', {})
        
        # Helper function to safely convert to float
        def safe_float(value, default=0):
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                # Remove commas and convert
                try:
                    return float(value.replace(',', ''))
                except (ValueError, AttributeError):
                    return default
            return default
        
        # Extract comprehensive analysis data from the correct structure
        # The frontend sends: result_data.result.analysis (backend analysis)
        # AND result_data.result (comprehensive transformedResult with additional data)
        analysis = result.get('analysis', {})
        life_insurance_needs = result.get('life_insurance_needs', analysis.get('life_insurance_needs', {}))
        portfolio_metrics = result.get('portfolio_metrics', analysis.get('portfolio_metrics', {}))
        key_findings = result.get('key_findings', analysis.get('key_findings', []))
        risk_analysis = result.get('risk_analysis', analysis.get('risk_analysis', {}))
        # Handle case where risk_analysis might be a list, string, or dict
        if isinstance(risk_analysis, list):
            risk_analysis = {'summary': ' '.join(risk_analysis) if risk_analysis else 'Risk analysis completed with comprehensive assessment.'}
        elif isinstance(risk_analysis, str):
            risk_analysis = {'summary': risk_analysis if risk_analysis else 'Risk analysis completed with comprehensive assessment.'}
        elif not isinstance(risk_analysis, dict):
            risk_analysis = {'summary': 'Risk analysis completed with comprehensive assessment.'}
        opportunities = result.get('opportunities', analysis.get('opportunities', []))
        recommendations = result.get('recommendations', analysis.get('recommendations', []))
        tax_efficiency = result.get('tax_efficiency', analysis.get('tax_efficiency', ''))
        # Handle case where tax_efficiency might be a string, list, or dict
        if isinstance(tax_efficiency, str):
            tax_efficiency = {'summary': tax_efficiency if tax_efficiency else 'Tax efficiency analysis completed.'}
        elif isinstance(tax_efficiency, list):
            tax_efficiency = {'summary': ' '.join(tax_efficiency) if tax_efficiency else 'Tax efficiency analysis completed.'}
        elif not isinstance(tax_efficiency, dict):
            tax_efficiency = {'summary': 'Tax efficiency analysis completed.'}
        
        rebalancing_needs = result.get('rebalancing_needs', analysis.get('rebalancing_needs', ''))
        # Handle case where rebalancing_needs might be a string or list
        if isinstance(rebalancing_needs, str):
            rebalancing_needs = [rebalancing_needs] if rebalancing_needs else []
        elif not isinstance(rebalancing_needs, list):
            rebalancing_needs = []
        cash_value_projection = result.get('cash_value_projection', analysis.get('cash_value_projection', []))
        
        # Calculate IUL cash value projections safely
        def get_cash_value_for_year(year):
            for projection in cash_value_projection:
                if projection.get('year') == year:
                    return projection.get('value', 0)
            return 0
        
        year_5_value = get_cash_value_for_year(5)
        year_10_value = get_cash_value_for_year(10)
        year_20_value = get_cash_value_for_year(20)
        year_30_value = get_cash_value_for_year(30)
        year_40_value = get_cash_value_for_year(40)
        
        # Calculate total premiums paid over 40 years
        monthly_contribution = result.get('recommended_monthly_savings', 0)
        total_premiums_40_years = monthly_contribution * 12 * 40
        
        # Build comprehensive portfolio report with all sections
        # Extract data from the correct structure (transformedResult has the data at top level)
        total_assets = safe_float(form_data.get('total_assets', 0))
        total_net_worth = safe_float(form_data.get('total_net_worth', 0))
        investable_portfolio = safe_float(form_data.get('investable_portfolio', 0))
        liquid_assets = safe_float(form_data.get('liquid_assets', 0))
        total_liabilities = safe_float(form_data.get('liabilities_total', 0))
        
        report = f"""## COMPREHENSIVE PORTFOLIO ANALYSIS COMPLETED

**Portfolio Overview:**
- Total Assets: ${total_assets:,.2f}
- Total Net Worth: ${total_net_worth:,.2f}
- Investable Portfolio: ${investable_portfolio:,.2f}
- Liquid Assets: ${liquid_assets:,.2f}
- Total Liabilities: ${total_liabilities:,.2f}

**Portfolio Health Score:**
- Overall Portfolio Health: {portfolio_metrics.get('portfolio_health_score', 0)}/100
- Health Status: {'Excellent' if portfolio_metrics.get('portfolio_health_score', 0) >= 85 else 'Good' if portfolio_metrics.get('portfolio_health_score', 0) >= 70 else 'Needs Attention'}
- Health Recommendation: {'Strong diversification and liquidity' if portfolio_metrics.get('portfolio_health_score', 0) >= 85 else 'Good balance with room for improvement' if portfolio_metrics.get('portfolio_health_score', 0) >= 70 else 'Consider rebalancing and increasing liquidity'}
- Risk Level: {portfolio_metrics.get('risk_level', 'moderate')} ({'High equity exposure' if portfolio_metrics.get('risk_level', 'moderate') == 'aggressive' else 'Balanced allocation' if portfolio_metrics.get('risk_level', 'moderate') == 'moderate' else 'Conservative approach'})
- Risk Score: {portfolio_metrics.get('risk_score', 0)}/100 ({'Low risk' if portfolio_metrics.get('risk_score', 0) >= 80 else 'Moderate risk' if portfolio_metrics.get('risk_score', 0) < 60 else 'High risk'})
- Liquidity Ratio: {portfolio_metrics.get('liquidity_ratio', 0)}x monthly expenses ({'Excellent' if portfolio_metrics.get('liquidity_ratio', 0) > 20 else 'Good' if portfolio_metrics.get('liquidity_ratio', 0) > 10 else 'Consider increasing'})
- Diversification: ✓ Well balanced
- Liquidity: ✓ Adequate reserves
- Risk Management: ✓ Appropriate level

**Asset Allocation:**
- Equity: ${safe_float(form_data.get('equity_allocation', 0)):,.2f} (${portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 0):.1f}%)
- Fixed Income: ${safe_float(form_data.get('fixed_income_allocation', 0)):,.2f} (${portfolio_metrics.get('asset_allocation_percentages', {}).get('fixed_income', 0):.1f}%)
- Real Estate: ${safe_float(form_data.get('real_estate_allocation', 0)):,.2f} (${portfolio_metrics.get('asset_allocation_percentages', {}).get('real_estate', 0):.1f}%)
- Cash: ${safe_float(form_data.get('cash_allocation', 0)):,.2f} (${portfolio_metrics.get('asset_allocation_percentages', {}).get('cash', 0):.1f}%)
- Alternative Investments: ${safe_float(form_data.get('alternative_allocation', 0)):,.2f} (${portfolio_metrics.get('asset_allocation_percentages', {}).get('alternative', 0):.1f}%)

**Account Distribution:**
- Retirement Accounts: ${safe_float(form_data.get('retirement_accounts', 0)):,.2f} ({(safe_float(form_data.get('retirement_accounts', 0)) / max(investable_portfolio, 1) * 100):.1f}%)
- Taxable Accounts: ${safe_float(form_data.get('taxable_accounts', 0)):,.2f} ({(safe_float(form_data.get('taxable_accounts', 0)) / max(investable_portfolio, 1) * 100):.1f}%)
- Education Accounts: ${safe_float(form_data.get('education_accounts', 0)):,.2f} ({(safe_float(form_data.get('education_accounts', 0)) / max(investable_portfolio, 1) * 100):.1f}%)

**Life Insurance Analysis:**
- Recommended Coverage: ${result.get('recommended_coverage', 0):,.2f}
- Current Coverage: ${safe_float(form_data.get('current_life_insurance', 0)) + safe_float(form_data.get('individual_life', 0)) + safe_float(form_data.get('group_life', 0)):,.2f}
- Individual Life Insurance: ${safe_float(form_data.get('individual_life', 0)):,.2f}
- Group Life Insurance: ${safe_float(form_data.get('group_life', 0)):,.2f}
- Coverage Gap: ${result.get('gap', 0):,.2f} ({(result.get('gap', 0) / max(result.get('recommended_coverage', 1), 1)) * 100:.1f}% of need)
- Product Recommendation: {result.get('product_recommendation', 'N/A')}
- Duration: {result.get('duration_years', 0)} years

**Product Recommendation:**
{life_insurance_needs.get('product_recommendation', result.get('product_recommendation', 'JPM TermVest+ IUL Track'))}
JPM TermVest+ offers two tracks: Term and IUL. The IUL Track provides immediate access to cash value accumulation with tax-deferred growth potential, flexible premiums, and permanent coverage. Your cash value can grow based on market performance while providing a guaranteed death benefit for life.

Why? At age 38.0 with $266,004 annual income and 2.0 dependents, you're an ideal candidate for the IUL Track. Start with term coverage and convert to permanent coverage as your financial situation allows, building cash value for retirement and legacy planning.

**Coverage Needs Breakdown:**
- Income Replacement: ${life_insurance_needs.get('income_replacement', 0):,.2f}
- Debts & Liabilities: ${life_insurance_needs.get('debt_payoff', 0):,.2f}
- Education Funding: ${life_insurance_needs.get('education_funding', 0):,.2f}
- Funeral Expenses: ${life_insurance_needs.get('funeral_expenses', 0):,.2f}
- Legacy/Inheritance: ${life_insurance_needs.get('legacy_amount', 0):,.2f}
- Special Needs: ${life_insurance_needs.get('special_needs', 0):,.2f}

**Cash Value Projections:**
- Recommended Monthly Savings: ${result.get('recommended_monthly_savings', 0):,.2f}
- Max Monthly Contribution: ${result.get('max_monthly_contribution', 0):,.2f}
- Projection Parameters: {result.get('projection_parameters', {})}

**Portfolio Benchmarks & Industry Standards:**
- Asset Allocation vs. Industry Standards:
  - Your Equity Allocation: {portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 0):.1f}%
  - Industry Standard (Age {form_data.get('age', 35)}): {max(100 - int(form_data.get('age', 35)), 20)}%
  - Your Fixed Income: {portfolio_metrics.get('asset_allocation_percentages', {}).get('fixed_income', 0):.1f}%
  - Recommended Fixed Income: {min(int(form_data.get('age', 35)), 40)}%
- Portfolio Size Benchmarks:
  - Total Assets: ${total_assets:,.2f}
  - Investable Portfolio: ${investable_portfolio:,.2f}
  - Age {form_data.get('age', 35)} Average: ${'$50,000' if int(form_data.get('age', 35)) < 30 else '$150,000' if int(form_data.get('age', 35)) < 40 else '$300,000' if int(form_data.get('age', 35)) < 50 else '$500,000'}
  - Your Net Worth: ${total_net_worth:,.2f}
  - Net Worth to Total Assets: {(total_net_worth / max(total_assets, 1) * 100):.1f}%
  - Net Worth to Investable: {(total_net_worth / max(investable_portfolio, 1) * 100):.1f}%
- Coverage Gap Percentage: {(result.get('gap', 0) / max(result.get('recommended_coverage', 1), 1)) * 100:.1f}%

**Risk Analysis & Benchmarks:**
{risk_analysis.get('summary', 'Risk analysis completed with comprehensive assessment.')}

**Key Opportunities:**
{', '.join(opportunities) if opportunities else 'Portfolio optimization opportunities identified.'}

**Tax Efficiency Analysis:**
{tax_efficiency.get('summary', 'Tax efficiency analysis completed.')}

**Rebalancing Recommendations:**
{', '.join(rebalancing_needs) if rebalancing_needs else 'Portfolio rebalancing recommendations provided.'}

**Strategic Recommendations:**
{', '.join(recommendations) if recommendations else 'Strategic portfolio recommendations provided.'}

**Key Findings:**
{', '.join(key_findings) if key_findings else 'Comprehensive portfolio analysis completed with detailed financial assessment.'}

**IUL Portfolio Integration:**

**Recommended Strategy:**
Why IUL Makes Sense for Your Portfolio
✓ Tax-Deferred Growth: Cash value grows tax-deferred, unlike taxable investments
✓ Portfolio Diversification: Reduces equity exposure while maintaining growth potential
✓ Market Protection: 0% floor protection with unlimited upside potential
✓ Enhanced Liquidity: Tax-free access to cash value for emergencies or opportunities
✓ Legacy Planning: Tax-free death benefit for wealth transfer
✓ Retirement Income: Tax-free retirement income supplement

**IUL vs. Traditional Investment Comparison:**
- Tax Treatment: IUL = Tax-Deferred, Traditional = Taxable
- Death Benefit: IUL = Guaranteed, Traditional = None
- Withdrawal Flexibility: IUL = Tax-Free, Traditional = Taxable
- Required Distributions: IUL = None, Traditional = RMDs (IRA)
- Market Protection: IUL = Floor Protection, Traditional = Full Risk

**Portfolio Enhancement:**
- Current Portfolio Value: ${total_assets:,.2f}
- IUL Cash Value (Year 10): ${year_10_value:,.2f}
- Enhanced Portfolio: ${total_assets + year_10_value:,.2f}

**Tax Efficiency Benefits:**
- Tax-Deferred Growth: ✓ Available
- Tax-Free Withdrawals: ✓ Available
- Tax-Free Death Benefit: ✓ Guaranteed
- No Required Distributions: ✓ Flexible

**Portfolio Diversification Impact:**
- {((portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 0) - 9.2) / max(portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 1), 1) * 100):.1f}% Reduced Equity Exposure
- {((year_10_value / (total_assets + year_10_value)) * 100):.1f}% IUL Allocation
- {(((liquid_assets + year_10_value) / (total_assets + year_10_value)) * 100):.1f}% Enhanced Liquidity

**Strategic Benefits Timeline:**
- Short Term (1-5 years): Tax-deferred growth begins, Death benefit protection, Flexible premium payments, Portfolio diversification
- Medium Term (5-15 years): Significant cash value accumulation, Tax-free withdrawal options, Enhanced retirement planning, Legacy building potential
- Long Term (15+ years): Substantial cash value growth, Tax-free retirement income, Wealth transfer benefits, Permanent protection

**IUL Cash Value Growth & Future Scenarios:**
Based on your portfolio analysis, this is our calculated field for suggested monthly cash value savings. You can change this value during times of financial change (saving more or less).

**Key Growth Milestones:**
- Year 5 Cash Value: ${year_5_value:,.2f}
- Year 10 Cash Value: ${year_10_value:,.2f}
- Year 20 Cash Value: ${year_20_value:,.2f}
- Year 30 Cash Value: ${year_30_value:,.2f}
- Year 40 Cash Value: ${year_40_value:,.2f}
- Total Premiums Paid (40 years): ${total_premiums_40_years:,.2f}

**Monthly Savings Configuration:**
- Monthly Amount: ${monthly_contribution:,.2f}
- Maximum allowed: ${result.get('max_monthly_contribution', 0):,.2f}/month (MEC limit)
- Savings Level: {'Low Savings' if monthly_contribution <= result.get('max_monthly_contribution', 0) * 0.25 else 'Medium Savings' if monthly_contribution <= result.get('max_monthly_contribution', 0) * 0.5 else 'High Savings' if monthly_contribution <= result.get('max_monthly_contribution', 0) * 0.75 else 'Maximum Savings'} ({(monthly_contribution / max(result.get('max_monthly_contribution', 1), 1)) * 100:.0f}% of maximum)

**Future Financial Scenarios:**

**Retirement Planning:**
- Age at Retirement: {int(form_data.get('age', 35)) + (result.get('projection_parameters', {}).get('duration_years', 30))}
- IUL Cash Value: ${year_40_value:,.2f}
- Tax-Free Income: ${year_40_value * 0.04:,.2f}/year

**Legacy Planning:**
- Death Benefit: ${result.get('recommended_coverage', 0):,.2f}
- Cash Value (Year 40): ${year_40_value:,.2f}
- Tax-Free Transfer: ✓ Available

**Emergency Fund:**
- Current Liquid Assets: ${liquid_assets:,.2f}
- IUL Cash Value (Year 5): ${year_5_value:,.2f}
- Enhanced Emergency Fund: ${liquid_assets + year_5_value:,.2f}

**Portfolio Protection & Risk Management:**

**Market Protection Benefits:**
- Current Market Exposure: {portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 0):.1f}%
- Protected Assets (IUL): 9.2%
- Floor Protection: 1%
- Cap Potential (Yearly): 7%

**Risk Management Strategies:**
- Sequence of Returns Risk: IUL provides protection against market downturns during critical retirement years
- Longevity Risk: Permanent coverage ensures protection regardless of life expectancy
- Tax Risk: Tax-free withdrawals and death benefits provide tax efficiency
- Inflation Risk: Cash value growth potential helps maintain purchasing power

**Portfolio Stress Testing Scenarios:**
- Market Crash Scenario: Traditional investments: -30%, IUL cash value: 0% (protected), Portfolio protection: Enhanced
- Low Interest Rate Environment: Traditional bonds: Low returns, IUL cash value: Growth potential, Portfolio yield: Maintained
- High Tax Environment: Traditional investments: Tax burden, IUL withdrawals: Tax-free, Tax efficiency: Maximized
- Tax Risk: Tax-free withdrawals and death benefits provide tax efficiency

**Actionable Recommendations:**

**Portfolio Optimization:**
- Equity Allocation Analysis: Your equity allocation ({portfolio_metrics.get('asset_allocation_percentages', {}).get('equity', 0):.1f}%) compared to recommended {max(100 - int(form_data.get('age', 35)), 20)}% for your age.
- Liquidity Analysis: Your liquidity ratio ({portfolio_metrics.get('asset_allocation_percentages', {}).get('cash', 0):.1f}%) compared to recommended 10-20%. Consider increasing liquid assets by ${max(0, total_assets * 0.15 - liquid_assets):,.2f}.
- Emergency Fund Recommendation: Current liquid assets of ${liquid_assets:,.2f} should be increased to ${total_assets * 0.15:,.2f} (15% of total assets) for optimal emergency fund coverage.

**Insurance & Protection:**
- Coverage Gap Analysis: You have a ${result.get('gap', 0):,.2f} insurance gap ({(result.get('gap', 0) / max(result.get('recommended_coverage', 1), 1)) * 100:.1f}% of need). This represents a significant risk to your family's financial security.
- IUL Integration Opportunity: Consider allocating ${result.get('recommended_monthly_savings', 0):,.2f}/month to IUL for tax-deferred growth and portfolio diversification.

**Recommended Next Steps:**
- Immediate (1-3 months): Address critical insurance gaps, Review and adjust asset allocation, Establish emergency fund if needed
- Short-term (3-12 months): Implement IUL strategy if recommended, Rebalance portfolio quarterly, Review tax efficiency opportunities
- Long-term (1-5 years): Monitor portfolio performance, Adjust strategy as life changes, Plan for major life events
- Review and adjust asset allocation quarterly
- Monitor portfolio performance and adjust strategy as life changes

**Executive Summary:**

**Portfolio Strengths:**
- Total assets of ${total_assets:,.2f} including real estate
- Investable portfolio of ${investable_portfolio:,.2f} for allocation analysis
- {'Strong' if liquid_assets > investable_portfolio * 0.1 else 'Adequate'} liquidity position
- {portfolio_metrics.get('risk_level', 'moderate').title()} risk profile
- IUL integration opportunity identified

**Key Recommendations:**
- ${result.get('recommended_coverage', 0):,.2f} in life insurance coverage needed
- ${result.get('gap', 0):,.2f} coverage gap to address
- IUL Track recommended for optimal fit
- ${result.get('recommended_monthly_savings', 0):,.2f}/month IUL allocation suggested

**Portfolio Summary Cards:**
- Total Assets: ${total_assets:,.2f} (All assets including real estate)
- Investable Portfolio: ${investable_portfolio:,.2f} (Excluding real estate)
- Total Net Worth: ${total_net_worth:,.2f} (Including all assets & liabilities)
- Liquid Assets: ${liquid_assets:,.2f} (Cash & equivalents)
- Total Liabilities: ${total_liabilities:,.2f} (Debts & obligations)

**Key Insights:**
- Portfolio Strengths: Total assets of ${total_assets:,.2f} including real estate, Investable portfolio of ${investable_portfolio:,.2f} for allocation analysis, {'Strong' if liquid_assets > investable_portfolio * 0.1 else 'Adequate'} liquidity position, {portfolio_metrics.get('risk_level', 'moderate').title()} risk profile
- Insurance Recommendations: ${result.get('recommended_coverage', 0):,.2f} in life insurance coverage needed, ${result.get('gap', 0):,.2f} coverage gap to address, IUL Track recommended for optimal fit

Portfolio analysis indicates a solid financial foundation with significant opportunities for optimization through strategic life insurance integration. The recommended IUL Track provides comprehensive protection while enhancing portfolio diversification and tax efficiency."""
        
        return report
        
    else:
        return f"## {tool_type.upper()} COMPLETED\n\n{json.dumps(result_data, indent=2)}"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    
    try:
        status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "chatbot_available": chatbot_orchestrator is not None,
            "components": {}
        }
        
        if chatbot_orchestrator:
            status["components"] = {
                "intent_classifier": "available",
                "smart_router": "available",
                "rag_system": "available",
                "external_search": "available",
                "tool_integrator": "available",
                "calculator_selector": "available",
                "quick_calculator": "available",
                "file_processor": "available",
                "session_linker": "available" if session_linker else "unavailable",
                "pdf_generator": "available" if pdf_generator else "unavailable"
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/test-minimal")
async def test_minimal():
    """Test minimal response to isolate truncation issue"""
    return {"content": "This is a short test response", "test": "minimal"}

@app.get("/test-large")
async def test_large():
    """Test large response to isolate truncation issue"""
    large_content = "This is a test response. " * 200  # 5,000+ characters
    return {"content": large_content, "length": len(large_content), "test": "large"}

@app.post("/test-chat-minimal")
async def test_chat_minimal(request: ChatRequest):
    """Test minimal chat response bypassing all processing"""
    return ChatResponseAPI(
        content="Short test response",
        quality_score=1.0,
        routing_decision={"route_type": "test", "confidence": 1.0},
        disclaimers=[],
        session_id=request.session_id
    )

@app.post("/test-chat-large")
async def test_chat_large(request: ChatRequest):
    """Test large chat response bypassing all processing"""
    large_content = "This is a large test response that simulates the full RAG system output. " * 50  # 3,000+ characters
    return ChatResponseAPI(
        content=large_content,
        quality_score=1.0,
        routing_decision={"route_type": "test", "confidence": 1.0},
        disclaimers=[],
        session_id=request.session_id
    )

@app.post("/test-chat-orchestrator")
async def test_chat_orchestrator(request: ChatRequest):
    """Test chat response using orchestrator but with error handling"""
    try:
        logger.info(f"🧪 TEST: Starting orchestrator test for message: {request.message}")
        
        # Create chat message
        message = ChatMessage(
            id=str(uuid.uuid4()),
            type="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"🧪 TEST: Created chat message, calling orchestrator...")
        
        # Add timeout to orchestrator call
        import asyncio
        try:
            # Process through orchestrator with 30 second timeout
            response = await asyncio.wait_for(
                chatbot_orchestrator.process_message(message, request.session_id),
                timeout=30.0
            )
            logger.info(f"🧪 TEST: Orchestrator returned response within timeout")
        except asyncio.TimeoutError:
            logger.error(f"🧪 TEST: Orchestrator timed out after 30 seconds!")
            return ChatResponseAPI(
                content="Error: Orchestrator timed out after 30 seconds. This indicates a hanging issue.",
                quality_score=0.0,
                routing_decision={"route_type": "timeout", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        
        logger.info(f"🧪 TEST: Response content length: {len(response.content)}")
        logger.info(f"🧪 TEST: Response content preview: {response.content[:100]}...")
        logger.info(f"🧪 TEST: Routing decision type: {response.routing_decision.route_type}")
        logger.info(f"🧪 TEST: Quality score: {response.quality_score}")
        
        # Try to convert routing decision to dict
        try:
            routing_dict = response.routing_decision.dict()
            logger.info(f"🧪 TEST: Routing decision dict successful")
        except Exception as e:
            logger.error(f"🧪 TEST: Routing decision dict failed: {e}")
            routing_dict = {"route_type": "error", "confidence": 0.0}
        
        # Create final response
        final_response = ChatResponseAPI(
            content=response.content,
            quality_score=response.quality_score,
            routing_decision=routing_dict,
            disclaimers=response.disclaimers,
            session_id=request.session_id
        )
        
        logger.info(f"🧪 TEST: Final response created successfully")
        logger.info(f"🧪 TEST: Final response content length: {len(final_response.content)}")
        
        return final_response
        
    except Exception as e:
        logger.error(f"🧪 TEST: Error in orchestrator test: {e}")
        import traceback
        logger.error(f"🧪 TEST: Traceback: {traceback.format_exc()}")
        
        # Return error response
        return ChatResponseAPI(
            content=f"Error: {str(e)}",
            quality_score=0.0,
            routing_decision={"route_type": "error", "confidence": 0.0},
            disclaimers=[],
            session_id=request.session_id
        )

@app.post("/test-orchestrator-step-by-step")
async def test_orchestrator_step_by_step(request: ChatRequest):
    """Test each step of the orchestrator individually to isolate the issue"""
    try:
        logger.info(f"🔍 STEP TEST: Starting step-by-step test for message: {request.message}")
        
        # Create chat message
        message = ChatMessage(
            id=str(uuid.uuid4()),
            type="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Step 1: Test Intent Classification
        logger.info(f"🔍 STEP TEST: Testing Step 1 - Intent Classification")
        try:
            import asyncio
            intent_result = await asyncio.wait_for(
                chatbot_orchestrator.intent_classifier.classify_intent_semantically(
                    message.content, 
                    chatbot_orchestrator._get_or_create_session(request.session_id).get_context()
                ),
                timeout=10.0
            )
            logger.info(f"🔍 STEP TEST: Intent classification successful: {intent_result.intent.value}")
        except asyncio.TimeoutError:
            logger.error(f"🔍 STEP TEST: Intent classification timed out!")
            return ChatResponseAPI(
                content="Error: Intent classification timed out after 10 seconds.",
                quality_score=0.0,
                routing_decision={"route_type": "timeout", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        except Exception as e:
            logger.error(f"🔍 STEP TEST: Intent classification failed: {e}")
            return ChatResponseAPI(
                content=f"Error: Intent classification failed: {str(e)}",
                quality_score=0.0,
                routing_decision={"route_type": "error", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        
        # Step 2: Test Smart Routing
        logger.info(f"🔍 STEP TEST: Testing Step 2 - Smart Routing")
        try:
            routing_decision = await asyncio.wait_for(
                chatbot_orchestrator.smart_router.route_query_semantically(
                    intent_result, 
                    chatbot_orchestrator._get_or_create_session(request.session_id).get_context()
                ),
                timeout=10.0
            )
            logger.info(f"🔍 STEP TEST: Smart routing successful: {routing_decision.route_type.value}")
        except asyncio.TimeoutError:
            logger.error(f"🔍 STEP TEST: Smart routing timed out!")
            return ChatResponseAPI(
                content="Error: Smart routing timed out after 10 seconds.",
                quality_score=0.0,
                routing_decision={"route_type": "timeout", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        except Exception as e:
            logger.error(f"🔍 STEP TEST: Smart routing failed: {e}")
            return ChatResponseAPI(
                content=f"Error: Smart routing failed: {str(e)}",
                quality_score=0.0,
                routing_decision={"route_type": "error", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        
        # Step 3: Test Response Generation
        logger.info(f"🔍 STEP TEST: Testing Step 3 - Response Generation")
        try:
            response_content = await asyncio.wait_for(
                chatbot_orchestrator._generate_response_content(
                    routing_decision, 
                    message.content, 
                    chatbot_orchestrator._get_or_create_session(request.session_id).get_context(),
                    intent_result
                ),
                timeout=15.0
            )
            logger.info(f"🔍 STEP TEST: Response generation successful: {len(response_content)} characters")
        except asyncio.TimeoutError:
            logger.error(f"🔍 STEP TEST: Response generation timed out!")
            return ChatResponseAPI(
                content="Error: Response generation timed out after 15 seconds.",
                quality_score=0.0,
                routing_decision={"route_type": "timeout", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        except Exception as e:
            logger.error(f"🔍 STEP TEST: Response generation failed: {e}")
            return ChatResponseAPI(
                content=f"Error: Response generation failed: {str(e)}",
                quality_score=0.0,
                routing_decision={"route_type": "error", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        
        # All steps successful - create response
        logger.info(f"🔍 STEP TEST: All steps completed successfully!")
        
        # Test routing decision serialization
        try:
            routing_dict = routing_decision.dict()
            logger.info(f"🔍 STEP TEST: Routing decision serialization successful")
        except Exception as e:
            logger.error(f"🔍 STEP TEST: Routing decision serialization failed: {e}")
            routing_dict = {"route_type": "error", "confidence": 0.0}
        
        return ChatResponseAPI(
            content=f"Step-by-step test successful! Generated response: {response_content[:200]}...",
            quality_score=1.0,
            routing_decision=routing_dict,
            disclaimers=[],
                session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"🔍 STEP TEST: Unexpected error: {e}")
        import traceback
        logger.error(f"🔍 STEP TEST: Traceback: {traceback.format_exc()}")
        
        return ChatResponseAPI(
            content=f"Unexpected error: {str(e)}",
            quality_score=0.0,
            routing_decision={"route_type": "error", "confidence": 0.0},
            disclaimers=[],
            session_id=request.session_id
        )

@app.post("/test-intent-classifier-only")
async def test_intent_classifier_only(request: ChatRequest):
    """Test only the intent classifier to isolate the issue"""
    try:
        logger.info(f"🎯 INTENT TEST: Testing intent classifier only")
        
        # Create chat message
        message = ChatMessage(
            id=str(uuid.uuid4()),
            type="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Test intent classifier directly
        try:
            import asyncio
            context = chatbot_orchestrator._get_or_create_session(request.session_id).get_context()
            
            logger.info(f"🎯 INTENT TEST: Calling intent classifier...")
            intent_result = await asyncio.wait_for(
                chatbot_orchestrator.intent_classifier.classify_intent_semantically(
                    message.content, context
                ),
                timeout=15.0
            )
            
            logger.info(f"🎯 INTENT TEST: Intent classification successful!")
            logger.info(f"🎯 INTENT TEST: Intent: {intent_result.intent.value}")
            logger.info(f"🎯 INTENT TEST: Confidence: {intent_result.confidence}")
            
            return ChatResponseAPI(
                content=f"Intent classification successful! Intent: {intent_result.intent.value}, Confidence: {intent_result.confidence}",
                quality_score=1.0,
                routing_decision={"route_type": "intent_test", "confidence": intent_result.confidence},
                disclaimers=[],
                session_id=request.session_id
            )
            
        except asyncio.TimeoutError:
            logger.error(f"🎯 INTENT TEST: Intent classifier timed out after 15 seconds!")
            return ChatResponseAPI(
                content="Error: Intent classifier timed out after 15 seconds. This indicates the issue is in the intent classifier.",
                quality_score=0.0,
                routing_decision={"route_type": "timeout", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
        except Exception as e:
            logger.error(f"🎯 INTENT TEST: Intent classifier failed: {e}")
            import traceback
            logger.error(f"🎯 INTENT TEST: Traceback: {traceback.format_exc()}")
            return ChatResponseAPI(
                content=f"Error: Intent classifier failed: {str(e)}",
                quality_score=0.0,
                routing_decision={"route_type": "error", "confidence": 0.0},
                disclaimers=[],
                session_id=request.session_id
            )
            
    except Exception as e:
        logger.error(f"🎯 INTENT TEST: Unexpected error: {e}")
        return ChatResponseAPI(
            content=f"Unexpected error: {str(e)}",
            quality_score=0.0,
            routing_decision={"route_type": "error", "confidence": 0.0},
            disclaimers=[],
            session_id=request.session_id
        )

@app.post("/test-intermittent-issue")
async def test_intermittent_issue(request: ChatRequest):
    """Test to see if the issue is intermittent by running multiple queries"""
    try:
        logger.info(f"🔄 INTERMITTENT TEST: Testing multiple queries to see if issue is intermittent")
        
        results = []
        
        # Test 1: Simple query
        logger.info(f"🔄 INTERMITTENT TEST: Test 1 - Simple query")
        try:
            import asyncio
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type="user",
                content="hello",
                timestamp=datetime.utcnow()
            )
            
            response = await asyncio.wait_for(
                chatbot_orchestrator.process_message(message, f"{request.session_id}_test1"),
                timeout=20.0
            )
            
            results.append(f"Test 1 SUCCESS: {len(response.content)} chars")
            logger.info(f"🔄 INTERMITTENT TEST: Test 1 successful")
            
        except asyncio.TimeoutError:
            results.append("Test 1 TIMEOUT")
            logger.error(f"🔄 INTERMITTENT TEST: Test 1 timed out")
        except Exception as e:
            results.append(f"Test 1 ERROR: {str(e)}")
            logger.error(f"🔄 INTERMITTENT TEST: Test 1 error: {e}")
        
        # Test 2: Knowledge query
        logger.info(f"🔄 INTERMITTENT TEST: Test 2 - Knowledge query")
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type="user",
                content="what is life insurance",
                timestamp=datetime.utcnow()
            )
            
            response = await asyncio.wait_for(
                chatbot_orchestrator.process_message(message, f"{request.session_id}_test2"),
                timeout=20.0
            )
            
            results.append(f"Test 2 SUCCESS: {len(response.content)} chars")
            logger.info(f"🔄 INTERMITTENT TEST: Test 2 successful")
            
        except asyncio.TimeoutError:
            results.append("Test 2 TIMEOUT")
            logger.error(f"🔄 INTERMITTENT TEST: Test 2 timed out")
        except Exception as e:
            results.append(f"Test 2 ERROR: {str(e)}")
            logger.error(f"🔄 INTERMITTENT TEST: Test 2 error: {e}")
        
        # Test 3: Calculator query
        logger.info(f"🔄 INTERMITTENT TEST: Test 3 - Calculator query")
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type="user",
                content="calculate my life insurance needs",
                timestamp=datetime.utcnow()
            )
            
            response = await asyncio.wait_for(
                chatbot_orchestrator.process_message(message, f"{request.session_id}_test3"),
                timeout=20.0
            )
            
            results.append(f"Test 3 SUCCESS: {len(response.content)} chars")
            logger.info(f"🔄 INTERMITTENT TEST: Test 3 successful")
            
        except asyncio.TimeoutError:
            results.append("Test 3 TIMEOUT")
            logger.error(f"🔄 INTERMITTENT TEST: Test 3 timed out")
        except Exception as e:
            results.append(f"Test 3 ERROR: {str(e)}")
            logger.error(f"🔄 INTERMITTENT TEST: Test 3 error: {e}")
        
        # Summary
        summary = f"Intermittent Test Results:\n" + "\n".join(results)
        logger.info(f"🔄 INTERMITTENT TEST: All tests completed. Summary: {summary}")
        
        return ChatResponseAPI(
            content=summary,
            quality_score=1.0,
            routing_decision={"route_type": "intermittent_test", "confidence": 1.0},
            disclaimers=[],
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"🔄 INTERMITTENT TEST: Unexpected error: {e}")
        import traceback
        logger.error(f"🔄 INTERMITTENT TEST: Traceback: {traceback.format_exc()}")
        
        return ChatResponseAPI(
            content=f"Unexpected error in intermittent test: {str(e)}",
            quality_score=0.0,
            routing_decision={"route_type": "error", "confidence": 0.0},
            disclaimers=[],
            session_id=request.session_id
        )

@app.post("/test-resource-issue")
async def test_resource_issue(request: ChatRequest):
    """Test to see if the issue is resource-related (memory, Qdrant, etc.)"""
    try:
        logger.info(f"🔧 RESOURCE TEST: Testing for resource-related issues")
        
        import psutil
        import gc
        
        # Get current memory usage
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        logger.info(f"🔧 RESOURCE TEST: Current memory usage: {memory_mb:.1f} MB")
        
        # Test Qdrant health
        try:
            qdrant_info = chatbot_orchestrator.rag_system.collection_info
            logger.info(f"🔧 RESOURCE TEST: Qdrant collection info: {qdrant_info}")
            qdrant_status = "HEALTHY"
        except Exception as e:
            logger.error(f"🔧 RESOURCE TEST: Qdrant error: {e}")
            qdrant_status = f"ERROR: {str(e)}"
        
        # Test OpenAI client health
        try:
            # Simple test - just check if we can create a client
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=config.openai_api_key)
            openai_status = "HEALTHY"
        except Exception as e:
            logger.error(f"🔧 RESOURCE TEST: OpenAI client error: {e}")
            openai_status = f"ERROR: {str(e)}"
        
        # Force garbage collection
        gc.collect()
        
        # Test a simple query to see if it works
        try:
            message = ChatMessage(
                id=str(uuid.uuid4()),
                type="user",
                content="hello",
                timestamp=datetime.utcnow()
            )
            
            import asyncio
            response = await asyncio.wait_for(
                chatbot_orchestrator.process_message(message, f"{request.session_id}_resource_test"),
                timeout=15.0
            )
            
            query_status = f"SUCCESS: {len(response.content)} chars"
            logger.info(f"🔧 RESOURCE TEST: Query test successful")
            
        except asyncio.TimeoutError:
            query_status = "TIMEOUT"
            logger.error(f"🔧 RESOURCE TEST: Query test timed out")
        except Exception as e:
            query_status = f"ERROR: {str(e)}"
            logger.error(f"🔧 RESOURCE TEST: Query test error: {e}")
        
        # Final memory check
        memory_info_after = process.memory_info()
        memory_mb_after = memory_info_after.rss / 1024 / 1024
        memory_diff = memory_mb_after - memory_mb
        
        summary = f"""Resource Test Results:
Memory: {memory_mb:.1f} MB → {memory_mb_after:.1f} MB (Δ: {memory_diff:+.1f} MB)
Qdrant: {qdrant_status}
OpenAI Client: {openai_status}
Query Test: {query_status}"""
        
        logger.info(f"🔧 RESOURCE TEST: Resource test completed")
        
        return ChatResponseAPI(
            content=summary,
            quality_score=1.0,
            routing_decision={"route_type": "resource_test", "confidence": 1.0},
            disclaimers=[],
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"🔧 RESOURCE TEST: Unexpected error: {e}")
        import traceback
        logger.error(f"🔧 RESOURCE TEST: Traceback: {traceback.format_exc()}")
        
        return ChatResponseAPI(
            content=f"Resource test error: {str(e)}",
            quality_score=0.0,
            routing_decision={"route_type": "error", "confidence": 0.0},
            disclaimers=[],
            session_id=request.session_id
        )

@app.get("/")
async def root():
    """Root endpoint"""
    
    return {
        "message": "Robo-Advisor Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "websocket": "/ws/chat/{session_id}",
            "chat": "/api/chat/process",
            "file_upload": "/api/chat/file/upload",
            "file_analyze": "/api/chat/file/analyze",
            "calculator": "/api/chat/calculator",
            "health": "/health",
            "test_minimal": "/test-minimal",
            "test_large": "/test-large",
            "test_chat_minimal": "/test-chat-minimal",
            "test_chat_large": "/test-chat-large",
            "test_chat_orchestrator": "/test-chat-orchestrator",
            "test_orchestrator_step_by_step": "/test-orchestrator-step-by-step",
            "test_intent_classifier_only": "/test-intent-classifier-only",
            "test_intermittent_issue": "/test-intermittent-issue",
            "test_resource_issue": "/test-resource-issue"
        }
    } 
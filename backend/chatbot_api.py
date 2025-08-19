import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from datetime import datetime

# Fix: Use absolute imports instead of relative imports
from chatbot.schemas import ChatMessage, ChatResponse, ConversationContext
from chatbot.intent_classifier import SemanticIntentClassifier
from chatbot.smart_router import SemanticSmartRouter, ToolIntegrator
from chatbot.external_search import ExternalSearchSystem
from chatbot.orchestrator import ChatbotOrchestrator
from chatbot.calculator_selector import SemanticCalculatorSelector
from chatbot.quick_calculator import QuickCalculator
from chatbot.advanced_rag import EnhancedRAGSystem
from chatbot.file_processor import FileProcessor
from chatbot.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Robo-Advisor Chatbot API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chatbot orchestrator
chatbot_orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize chatbot components on startup"""
    
    global chatbot_orchestrator
    
    try:
        logger.info("🚀 Initializing Robo-Advisor Chatbot...")
        
        # Initialize core components
        logger.info("📚 Initializing RAG system...")
        rag_system = EnhancedRAGSystem()
        
        logger.info("🔍 Initializing external search...")
        external_search = ExternalSearchSystem()
        
        logger.info("🔗 Initializing tool integrator...")
        tool_integrator = ToolIntegrator()
        
        logger.info("🧮 Initializing calculator selector...")
        calculator_selector = SemanticCalculatorSelector()
        
        logger.info("⚡ Initializing quick calculator...")
        quick_calculator = QuickCalculator()
        
        logger.info("📁 Initializing file processor...")
        file_processor = FileProcessor()
        
        logger.info("🎯 Initializing intent classifier...")
        intent_classifier = SemanticIntentClassifier()
        
        logger.info("🛣️ Initializing smart router...")
        smart_router = SemanticSmartRouter(
            rag_system=rag_system,
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
            
            # Process message through chatbot
            if chatbot_orchestrator:
                try:
                    # Create chat message
                    chat_message = ChatMessage(
                        id=str(uuid.uuid4()),
                        type="user",
                        content=message_data.get("content", ""),
                        timestamp=datetime.utcnow(),
                        session_id=session_id
                    )
                    
                    # Process message
                    response = await chatbot_orchestrator.process_message(chat_message, session_id)
                    
                    # Send response back
                    await manager.send_message(session_id, {
                        "type": "chat_response",
                        "content": response.content,
                        "quality_score": response.quality_score,
                        "routing_decision": response.routing_decision.dict(),
                        "disclaimers": response.disclaimers,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await manager.send_message(session_id, {
                        "type": "error",
                        "content": f"Error processing message: {str(e)}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            else:
                # Send error if orchestrator not available
                await manager.send_message(session_id, {
                    "type": "error",
                    "content": "Chatbot system is not available. Please try again later.",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        manager.disconnect(session_id)

# HTTP endpoints
@app.post("/api/chat/process", response_model=ChatResponseAPI)
async def process_chat_message(request: ChatRequest):
    """HTTP endpoint for processing chat messages"""
    
    if not chatbot_orchestrator:
        raise HTTPException(status_code=503, detail="Chatbot system is not available")
    
    try:
        # Create chat message
        chat_message = ChatMessage(
            id=str(uuid.uuid4()),
            type="user",
            content=request.message,
            timestamp=datetime.utcnow()
        )
        
        # Process message
        response = await chatbot_orchestrator.process_message(chat_message, request.session_id)
        
        return ChatResponseAPI(
            content=response.content,
            quality_score=response.quality_score,
            routing_decision=response.routing_decision.dict(),
            disclaimers=response.disclaimers,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

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
                "message": welcome_message
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
                "file_processor": "available"
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

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
            "health": "/health"
        }
    } 
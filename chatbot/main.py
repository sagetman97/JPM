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
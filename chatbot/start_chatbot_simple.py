#!/usr/bin/env python3
"""
Simple chatbot startup test
"""

import asyncio
import logging
from core.orchestrator import ChatbotOrchestrator
from core.intent_classifier import SemanticIntentClassifier
from core.smart_router import SemanticSmartRouter, ToolIntegrator
from core.external_search import ExternalSearchSystem
from core.advanced_rag import EnhancedRAGSystem
from core.calculator_selector import SemanticCalculatorSelector
from core.quick_calculator import QuickCalculator
from core.file_processor import FileProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chatbot():
    """Test basic chatbot functionality"""
    
    try:
        logger.info("🚀 Starting Chatbot Test...")
        
        # Initialize core components
        logger.info("📚 Initializing RAG system...")
        rag_system = EnhancedRAGSystem(external_search_system=None)  # No external search needed for simple startup
        
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
        
        logger.info("✅ Chatbot initialized successfully!")
        
        # Test basic message processing
        logger.info("🧪 Testing message processing...")
        
        # Create a test message
        from core.schemas import ChatMessage, MessageType
        from datetime import datetime, timezone
        test_message = ChatMessage(
            id="test_1",
            type=MessageType.USER,
            content="What is life insurance?",
            timestamp=datetime.now(timezone.utc)
        )
        
        # Process the message
        response = await chatbot_orchestrator.process_message(test_message, "test_session")
        
        logger.info(f"✅ Message processed successfully!")
        logger.info(f"📝 Response: {response.content[:100]}...")
        logger.info(f"🎯 Quality Score: {response.quality_score}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Chatbot test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chatbot())
    if success:
        print("\n🎉 Chatbot is working correctly!")
    else:
        print("\n❌ Chatbot has issues that need fixing!") 
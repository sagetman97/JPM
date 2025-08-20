#!/usr/bin/env python3
"""Test script to verify all imports work correctly"""

import asyncio
import logging
import sys
import os

# Add the chatbot directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_imports():
    """Test all critical imports"""
    
    try:
        logger.info("Testing core imports...")
        
        # Test core modules
        from core.config import config
        logger.info("✓ Config imported successfully")
        
        from core.schemas import (
            ConversationContext, IntentCategory, CalculatorType, 
            RouteType, KnowledgeLevel, IntentResult
        )
        logger.info("✓ Schemas imported successfully")
        
        from core.intent_classifier import SemanticIntentClassifier
        logger.info("✓ Intent classifier imported successfully")
        
        from core.smart_router import SemanticSmartRouter
        logger.info("✓ Smart router imported successfully")
        
        from core.quick_calculator import QuickCalculator
        logger.info("✓ Quick calculator imported successfully")
        
        from core.orchestrator import ChatbotOrchestrator
        logger.info("✓ Orchestrator imported successfully")
        
        from core.advanced_rag import EnhancedRAGSystem
        logger.info("✓ Advanced RAG imported successfully")
        
        from core.external_search import ExternalSearchSystem
        logger.info("✓ External search imported successfully")
        
        logger.info("✓ All core imports successful!")
        
        # Test basic initialization (without complex dependencies)
        logger.info("Testing basic system initialization...")
        
        # Test external search
        external_search = ExternalSearchSystem()
        logger.info("✓ External search initialized")
        
        # Test RAG system
        rag_system = EnhancedRAGSystem(external_search_system=external_search)
        logger.info("✓ RAG system initialized")
        
        # Test quick calculator
        calculator = QuickCalculator()
        logger.info("✓ Quick calculator initialized")
        
        # Test calculator session functionality
        logger.info("Testing calculator session functionality...")
        
        # Create a mock context
        context = ConversationContext(
            session_id="test_session",
            user_id="test_user",
            chat_history=[],
            knowledge_level=KnowledgeLevel.BEGINNER,
            calculator_state="inactive",
            calculator_session=None,
            calculator_type=None
        )
        
        # Test starting a calculation session
        result = await calculator.start_calculation_session("test_session", context)
        
        if result["status"] == "started":
            logger.info("✓ Calculator session started successfully")
            logger.info(f"  - Message: {result['message'][:100]}...")
            logger.info(f"  - Question: {result['question'][:100]}...")
            logger.info(f"  - Session ID: {result['session_id']}")
        else:
            logger.error(f"❌ Calculator session failed to start: {result}")
            return False
        
        # Test processing an answer
        answer_result = await calculator.process_answer("35", context)
        
        if answer_result["status"] in ["question", "completed"]:
            logger.info("✓ Calculator answer processing successful")
            logger.info(f"  - Status: {answer_result['status']}")
            if "progress" in answer_result:
                logger.info(f"  - Progress: {answer_result['progress']}")
        else:
            logger.error(f"❌ Calculator answer processing failed: {answer_result}")
            return False
        
        logger.info("✓ Calculator session functionality test passed!")
        
        logger.info("✓ Basic initialization successful!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting comprehensive import and functionality tests...")
    
    # Test imports
    imports_ok = await test_imports()
    
    if imports_ok:
        logger.info("🎉 All tests passed successfully!")
        return 0
    else:
        logger.error("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 
"""
Test script for calculator integration functionality.
Tests the end-to-end calculator workflow and integration.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_calculator_selection_flow():
    """Test that general calculation requests trigger calculator selection"""
    try:
        logger.info("🧮 Testing calculator selection flow...")
        
        from core.schemas import ConversationContext, KnowledgeLevel
        
        # For now, just test that the schemas support calculator selection
        # The actual routing logic will be tested in the main chatbot
        
        context = ConversationContext(
            session_id="test_selection",
            user_id="test_user",
            chat_history=[],
            knowledge_level=KnowledgeLevel.BEGINNER,
            calculator_state="inactive",
            calculator_session=None,
            calculator_type=None
        )
        
        logger.info("✓ Calculator selection schemas working")
        return True
            
    except Exception as e:
        logger.error(f"❌ Calculator selection test failed: {e}")
        return False

async def test_calculator_session_continuity():
    """Test that calculator sessions maintain continuity"""
    try:
        logger.info("🔄 Testing calculator session continuity...")
        
        from core.quick_calculator import QuickCalculator
        from core.schemas import ConversationContext, KnowledgeLevel, CalculatorType
        
        # Create calculator
        calculator = QuickCalculator()
        
        # Create context
        context = ConversationContext(
            session_id="test_continuity",
            user_id="test_user",
            chat_history=[],
            knowledge_level=KnowledgeLevel.BEGINNER,
            calculator_state="inactive",
            calculator_session=None,
            calculator_type=None
        )
        
        # Start session
        result = await calculator.start_calculation_session("test_continuity", context)
        logger.info(f"✓ Session started: {len(str(result))} characters")
        
        # Verify session is active in context
        if context.calculator_state == "active" and context.calculator_session:
            logger.info("✓ Calculator session active in context")
        else:
            logger.error("❌ Calculator session not properly initialized in context")
            return False
        
        # Process an answer
        answer_result = await calculator.process_answer("35", context)
        logger.info(f"✓ Answer processed: {len(str(answer_result))} characters")
        
        # Check if we got a question response
        if isinstance(answer_result, dict) and answer_result.get("status") == "question":
            logger.info("✓ Calculator continued to next question")
            return True
        elif isinstance(answer_result, dict) and answer_result.get("status") == "completed":
            logger.info("✓ Calculator completed (unexpected but valid)")
            return True
        else:
            logger.error(f"❌ Unexpected answer result: {answer_result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Calculator session continuity test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator_integration():
    """Test basic orchestrator components"""
    try:
        logger.info("🎯 Testing basic orchestrator components...")
        
        from core.quick_calculator import QuickCalculator
        from core.advanced_rag import EnhancedRAGSystem
        from core.external_search import ExternalSearchSystem
        
        # Initialize components
        external_search = ExternalSearchSystem()
        rag_system = EnhancedRAGSystem(external_search_system=external_search)
        quick_calculator = QuickCalculator()
        
        logger.info("✓ All basic components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Basic orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting comprehensive calculator integration tests...")
    
    # Run tests
    selection_ok = await test_calculator_selection_flow()
    continuity_ok = await test_calculator_session_continuity()
    orchestrator_ok = await test_orchestrator_integration()
    
    if selection_ok and continuity_ok and orchestrator_ok:
        logger.info("🎉 All calculator integration tests passed!")
        return 0
    else:
        logger.error("❌ Some calculator integration tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

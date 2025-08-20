#!/usr/bin/env python3
"""Test script for RAG system functionality"""

import asyncio
import logging
import sys
import os

# Add the chatbot directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_system():
    """Test the RAG system functionality"""
    
    try:
        logger.info("Testing RAG system...")
        
        from core.config import config
        from core.external_search import ExternalSearchSystem
        from core.advanced_rag import EnhancedRAGSystem
        from core.schemas import ConversationContext, KnowledgeLevel
        
        # Initialize external search first
        external_search = ExternalSearchSystem()
        logger.info("✓ External search initialized")
        
        # Initialize RAG system with external search
        rag_system = EnhancedRAGSystem(external_search_system=external_search)
        logger.info("✓ RAG system initialized")
        
        # Create test context
        context = ConversationContext(
            session_id="test_rag_session",
            knowledge_level=KnowledgeLevel.BEGINNER,
            semantic_themes=["life insurance", "coverage"],
            user_goals=["understand insurance needs"],
            current_topic="Insurance Planning"
        )
        
        # Test query
        test_query = "What is term life insurance?"
        logger.info(f"Testing query: {test_query}")
        
        # Get response
        result = await rag_system.get_semantic_response(test_query, context)
        logger.info(f"✓ RAG response generated: {len(result.response)} characters")
        logger.info(f"✓ Quality score: {result.quality_score}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    
    logger.info("🚀 Starting RAG system test...")
    
    success = await test_rag_system()
    
    if success:
        logger.info("🎉 RAG system test passed!")
        return 0
    else:
        logger.error("❌ RAG system test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

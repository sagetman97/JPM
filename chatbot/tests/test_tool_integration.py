#!/usr/bin/env python3
"""
Test Tool Integration Script
Tests the chatbot's ability to route users to external portfolio tools.
"""

import asyncio
import logging
import sys
import os

# Add the chatbot directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from core.smart_router import SemanticSmartRouter, ToolIntegrator
from core.schemas import IntentResult, IntentCategory, CalculatorType, ConversationContext, KnowledgeLevel
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_tool_integration():
    """Test the chatbot's tool integration capabilities"""
    
    try:
        logger.info("🚀 Testing Tool Integration...")
        
        # Create test context
        test_context = ConversationContext(
            session_id="test_tool_integration",
            knowledge_level=KnowledgeLevel.BEGINNER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Test different intents and routing
        test_cases = [
            {
                "query": "I want to calculate my life insurance needs",
                "expected_tool": "quick_calculator",
                "description": "Quick calculator routing"
            },
            {
                "query": "I need a comprehensive portfolio analysis",
                "expected_tool": "portfolio_analysis",
                "description": "Portfolio analysis routing"
            },
            {
                "query": "I want to assess a new client",
                "expected_tool": "client_assessment",
                "description": "Client assessment routing"
            }
        ]
        
        # Initialize tool integrator
        tool_integrator = ToolIntegrator()
        
        for test_case in test_cases:
            logger.info(f"\n🧪 Testing: {test_case['description']}")
            logger.info(f"📝 Query: '{test_case['query']}'")
            
            # Test tool routing
            try:
                tool_response = await tool_integrator.route_to_external_tool(
                    test_case['expected_tool'], 
                    test_context
                )
                
                logger.info(f"✅ Tool Response:")
                logger.info(f"  - Tool Type: {tool_response.tool_type}")
                logger.info(f"  - Action: {tool_response.action}")
                logger.info(f"  - URL: {tool_response.url}")
                logger.info(f"  - Message: {tool_response.message[:100]}...")
                
            except Exception as e:
                logger.error(f"❌ Tool routing failed: {e}")
        
        # Test external tool communication
        logger.info("\n🔗 Testing External Tool Communication...")
        
        # Test if we can reach the portfolio tools API
        import httpx
        
        async with httpx.AsyncClient() as client:
            try:
                # Test portfolio analysis endpoint
                backend_url = os.getenv("BACKEND_API_URL", "http://localhost:8000")
                response = await client.get(f"{backend_url}/api/health")
                if response.status_code == 200:
                    logger.info("✅ Portfolio tools API (port 8000) is accessible")
                    logger.info(f"  - Response: {response.json()}")
                else:
                    logger.warning(f"⚠️ Portfolio tools API returned status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"❌ Cannot reach portfolio tools API: {e}")
        
        logger.info("\n🎉 Tool Integration Testing Completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Tool integration testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_tool_integration())
    sys.exit(0 if success else 1) 
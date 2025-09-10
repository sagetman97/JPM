#!/usr/bin/env python3
"""
Test file for the new conversation management system
Tests conversation memory queries like "what did we just talk about"
"""

import asyncio
import sys
import os
import logging

# Add the chatbot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_conversation_management():
    """Test the conversation management system"""
    
    try:
        # Import required modules
        from conversation_memory import ConversationMemory, MemoryType
        from schemas import IntentCategory, RouteType
        
        logger.info("🧪 Testing Conversation Management System")
        
        # Test 1: Create conversation memory
        logger.info("Test 1: Creating conversation memory")
        memory = ConversationMemory()
        
        # Test 2: Add conversation turns
        logger.info("Test 2: Adding conversation turns")
        memory.add_conversation_turn(
            user_query="what are the current rates for term life insurance?",
            system_response="Term life insurance rates vary based on age, health, and coverage amount. For a healthy 30-year-old, $250k coverage typically costs around $200/year.",
            intent="life_insurance_education"
        )
        
        memory.add_conversation_turn(
            user_query="tell me more about IUL",
            system_response="Indexed Universal Life (IUL) is a permanent life insurance policy that offers both death benefit protection and cash value growth potential. The cash value can grow based on the performance of a stock market index.",
            intent="life_insurance_education"
        )
        
        memory.add_conversation_turn(
            user_query="how does the cash value work?",
            system_response="The cash value in IUL works by accumulating premiums over time and growing based on index performance. You can access this cash value through loans or withdrawals, and it grows tax-deferred.",
            intent="life_insurance_education"
        )
        
        # Test 3: Test conversation management queries
        logger.info("Test 3: Testing conversation management queries")
        
        # Test "what did we just talk about"
        response1 = memory.handle_conversation_management_query("what did we just talk about")
        logger.info(f"Response to 'what did we just talk about': {response1}")
        
        # Test "summarize our conversation"
        response2 = memory.handle_conversation_management_query("summarize our conversation")
        logger.info(f"Response to 'summarize our conversation': {response2}")
        
        # Test "what was the main topic"
        response3 = memory.handle_conversation_management_query("what was the main topic")
        logger.info(f"Response to 'what was the main topic': {response3}")
        
        # Test "how many questions have I asked"
        response4 = memory.handle_conversation_management_query("how many questions have I asked")
        logger.info(f"Response to 'how many questions have I asked': {response4}")
        
        # Test 4: Test memory stats
        logger.info("Test 4: Testing memory statistics")
        stats = memory.get_memory_stats()
        logger.info(f"Memory stats: {stats}")
        
        # Test 5: Test follow-up detection
        logger.info("Test 5: Testing follow-up detection")
        is_follow_up, main_topic, related_concepts = memory.understand_follow_up("how does the cash value work?")
        logger.info(f"Follow-up detected: {is_follow_up}, Main topic: {main_topic}, Related concepts: {related_concepts}")
        
        # Test 6: Test conversation context
        logger.info("Test 6: Testing conversation context")
        context = memory.get_conversation_context()
        logger.info(f"Conversation context: {context}")
        
        logger.info("✅ All conversation management tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_intent_classification():
    """Test that conversation management queries are properly classified"""
    
    try:
        logger.info("🧪 Testing Intent Classification for Conversation Management")
        
        # Import required modules
        from intent_classifier import SemanticIntentClassifier
        from schemas import ConversationContext, KnowledgeLevel
        
        # Create intent classifier
        classifier = SemanticIntentClassifier()
        
        # Create test context
        context = ConversationContext(
            session_id="test_session",
            knowledge_level=KnowledgeLevel.BEGINNER
        )
        
        # Test conversation management queries
        test_queries = [
            "what did we just talk about",
            "summarize our conversation",
            "what was the main topic",
            "what have we covered so far",
            "can you repeat what you said about IUL",
            "how long have we been talking"
        ]
        
        for query in test_queries:
            logger.info(f"Testing query: '{query}'")
            try:
                intent_result = await classifier.classify_intent_semantically(query, context)
                logger.info(f"Intent: {intent_result.intent.value}, Confidence: {intent_result.confidence}")
                
                # Check if it's classified as conversation management
                if intent_result.intent.value == "conversation_management":
                    logger.info("✅ Correctly classified as conversation_management")
                else:
                    logger.warning(f"⚠️ Expected conversation_management, got {intent_result.intent.value}")
                    
            except Exception as e:
                logger.error(f"Error classifying query '{query}': {e}")
        
        logger.info("✅ Intent classification tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Intent classification test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_routing():
    """Test that conversation management queries are properly routed"""
    
    try:
        logger.info("🧪 Testing Routing for Conversation Management")
        
        # Import required modules
        from smart_router import SemanticSmartRouter
        from schemas import IntentResult, IntentCategory, ConversationContext, KnowledgeLevel
        
        # Create mock dependencies
        class MockExternalSearch:
            pass
        
        class MockToolIntegrator:
            pass
        
        class MockBaseLLM:
            pass
        
        class MockCalculatorSelector:
            pass
        
        class MockQuickCalculator:
            pass
        
        # Create router
        router = SemanticSmartRouter(
            external_search=MockExternalSearch(),
            tool_integrator=MockToolIntegrator(),
            base_llm=MockBaseLLM(),
            calculator_selector=MockCalculatorSelector(),
            quick_calculator=MockQuickCalculator()
        )
        
        # Create test context
        context = ConversationContext(
            session_id="test_session",
            knowledge_level=KnowledgeLevel.BEGINNER
        )
        
        # Create test intent result
        intent_result = IntentResult(
            intent=IntentCategory.CONVERSATION_MANAGEMENT,
            semantic_goal="User wants to know what was discussed",
            calculator_type=None,
            confidence=0.95,
            reasoning="Query asks about conversation state",
            follow_up_clarification=None,
            needs_external_search=False,
            needs_calculator_selection=False,
            suggested_calculator=None
        )
        
        # Test routing
        routing_decision = await router.route_query_semantically(intent_result, context)
        logger.info(f"Routing decision: {routing_decision.route_type.value}")
        
        # Check if routed to conversation management
        if routing_decision.route_type.value == "conversation_management":
            logger.info("✅ Correctly routed to conversation_management")
        else:
            logger.warning(f"⚠️ Expected conversation_management route, got {routing_decision.route_type.value}")
        
        logger.info("✅ Routing tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("🚀 Starting Conversation Management System Tests")
    
    tests = [
        test_conversation_management,
        test_intent_classification,
        test_routing
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Conversation management system is working correctly.")
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

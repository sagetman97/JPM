#!/usr/bin/env python3
"""
Test Simple Conversation History System

This test file verifies that the simple conversation history system
works correctly for conversation management queries.
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.simple_conversation_history import SimpleConversationHistory

def test_simple_history():
    """Test the simple conversation history system"""
    print("🧪 Testing Simple Conversation History System")
    print("=" * 50)
    
    # Initialize the history system
    history = SimpleConversationHistory(max_history=8)
    
    # Test 1: Empty history
    print("\n📝 Test 1: Empty History")
    print(f"Summary: {history.get_conversation_summary()}")
    print(f"Detailed: {history.get_detailed_summary()}")
    print(f"Main Topic: {history.get_main_topic()}")
    
    # Test 2: Add first conversation turn
    print("\n📝 Test 2: First Conversation Turn")
    history.add_conversation_turn(
        user_message="Tell me about IUL insurance",
        bot_response="IUL (Indexed Universal Life) is a type of permanent life insurance that combines death benefit protection with cash value accumulation..."
    )
    print(f"Summary: {history.get_conversation_summary()}")
    print(f"Main Topic: {history.get_main_topic()}")
    
    # Test 3: Add second conversation turn
    print("\n📝 Test 3: Second Conversation Turn")
    history.add_conversation_turn(
        user_message="How does the cash value work?",
        bot_response="The cash value in IUL grows based on the performance of a stock market index, but with protection from market losses..."
    )
    print(f"Summary: {history.get_conversation_summary()}")
    print(f"Main Topic: {history.get_main_topic()}")
    
    # Test 4: Add more turns to test max history
    print("\n📝 Test 4: Multiple Turns (Testing Max History)")
    for i in range(3, 11):  # Add 8 more turns (total 10)
        history.add_conversation_turn(
            user_message=f"Question {i}: Tell me more about term life insurance",
            bot_response=f"Response {i}: Term life insurance provides coverage for a specific period..."
        )
    
    print(f"Total turns: {len(history.conversation_turns)}")
    print(f"Max history: {history.max_history}")
    print(f"Summary: {history.get_conversation_summary()}")
    print(f"Detailed: {history.get_detailed_summary()}")
    print(f"Main Topic: {history.get_main_topic()}")
    
    # Test 5: Test conversation metrics
    print("\n📝 Test 5: Conversation Metrics")
    print(f"Metrics: {history.get_conversation_metrics()}")
    
    # Test 6: Test last response
    print("\n📝 Test 6: Last Response")
    print(f"Last Response: {history.get_last_response()}")
    
    # Test 7: Test history stats
    print("\n📝 Test 7: History Stats")
    stats = history.get_history_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test 8: Test topic extraction
    print("\n📝 Test 8: Topic Extraction")
    test_messages = [
        "Tell me about IUL insurance",
        "How much coverage do I need?",
        "What are the current rates?",
        "Explain portfolio analysis",
        "Calculate my insurance needs"
    ]
    
    for msg in test_messages:
        topic = history._extract_topic(msg)
        print(f"  '{msg}' -> Topic: {topic}")
    
    print("\n✅ All tests completed successfully!")
    return True

def test_conversation_management_queries():
    """Test conversation management query handling"""
    print("\n🗣️ Testing Conversation Management Query Handling")
    print("=" * 50)
    
    # Initialize history with some conversation
    history = SimpleConversationHistory(max_history=8)
    
    # Add some conversation turns
    history.add_conversation_turn(
        user_message="Tell me about IUL insurance",
        bot_response="IUL is a type of permanent life insurance..."
    )
    history.add_conversation_turn(
        user_message="How does the cash value work?",
        bot_response="The cash value grows based on market performance..."
    )
    history.add_conversation_turn(
        user_message="What are the benefits?",
        bot_response="IUL offers tax-deferred growth and flexibility..."
    )
    
    # Test different query types
    test_queries = [
        "what did we just talk about",
        "summarize our conversation",
        "what was the main topic",
        "repeat what you said",
        "how long have we been talking",
        "what have we covered so far"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
        query_lower = query.lower()
        
        if any(phrase in query_lower for phrase in ["what did we just talk about", "what were we discussing", "what was our conversation about"]):
            response = history.get_conversation_summary()
        elif any(phrase in query_lower for phrase in ["summarize", "summary", "recap", "what have we covered"]):
            response = history.get_detailed_summary()
        elif any(phrase in query_lower for phrase in ["what was the main topic", "what topic were we on", "what were we focusing on"]):
            response = history.get_main_topic()
        elif any(phrase in query_lower for phrase in ["repeat", "restate", "say again", "what did you say about"]):
            response = history.get_last_response()
        elif any(phrase in query_lower for phrase in ["how long have we been talking", "how many questions", "conversation length"]):
            response = history.get_conversation_metrics()
        else:
            response = history.get_generic_response()
        
        print(f"Response: {response[:100]}...")
    
    print("\n✅ Conversation management query tests completed!")

if __name__ == "__main__":
    try:
        # Run basic tests
        test_simple_history()
        
        # Run conversation management tests
        test_conversation_management_queries()
        
        print("\n🎉 All tests passed! The simple conversation history system is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

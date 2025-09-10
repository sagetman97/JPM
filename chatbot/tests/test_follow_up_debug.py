#!/usr/bin/env python3
"""
Debug script to test follow-up detection system
"""

import asyncio
import sys
import os

# Add the chatbot directory to the path
sys.path.append('/mnt/c/AIProjects/RoboAdvisor/chatbot')

from core.follow_up_detector import FollowUpDetector
from core.simple_conversation_history import SimpleConversationHistory
from core.schemas import ConversationContext, KnowledgeLevel
from openai import AsyncOpenAI

async def test_follow_up_detection():
    """Test follow-up detection with detailed logging"""
    
    print("🔍 Testing Follow-up Detection System")
    print("=" * 50)
    
    # Create conversation history
    history = SimpleConversationHistory()
    history.add_conversation_turn(
        'I want to do a portfolio analyzer calculation', 
        'Portfolio analysis completed. Total assets: $2,214,840.00. Risk level: moderate. Life insurance need: $3,990,060.00'
    )
    
    print(f"📝 Created conversation history with {len(history.conversation_turns)} turns")
    
    # Get conversation turns
    conversation_history = history.get_conversation_turns()
    print(f"📝 Conversation history: {conversation_history}")
    
    # Create follow-up detector
    detector = FollowUpDetector(None)  # No LLM for this test
    
    # Test conversation context building
    context_str = detector._build_conversation_context(conversation_history)
    print(f"📝 Context string: {context_str}")
    
    # Test with a real LLM (if available)
    try:
        llm = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-test'))
        detector_with_llm = FollowUpDetector(llm)
        
        print("\n🤖 Testing with LLM...")
        result = await detector_with_llm.detect_follow_up(
            'I meant can you break down the report in more detail', 
            conversation_history
        )
        
        print(f"🔍 Follow-up result: {result}")
        
    except Exception as e:
        print(f"❌ Error testing with LLM: {e}")

if __name__ == "__main__":
    asyncio.run(test_follow_up_detection())

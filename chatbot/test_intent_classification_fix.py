#!/usr/bin/env python3
"""
Test script to verify the intent classification fix for follow-up questions.
This tests that "expand on cash value" is classified as life_insurance_education, not conversation_management.
"""

import asyncio
import sys
import os

# Add the chatbot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from chatbot.core.intent_classifier import SemanticIntentClassifier
from chatbot.core.schemas import ConversationContext, KnowledgeLevel, ClientContext

async def test_follow_up_intent_classification():
    """Test that follow-up questions are classified correctly"""
    
    print("🧪 Testing Intent Classification Fix for Follow-up Questions")
    print("=" * 60)
    
    # Initialize the intent classifier
    classifier = SemanticIntentClassifier()
    
    # Create a context with previous IUL discussion
    context = ConversationContext(
        session_id="test_session",
        knowledge_level=KnowledgeLevel.INTERMEDIATE,
        semantic_themes=["IUL", "cash value", "life insurance"],
        current_topic="Indexed Universal Life Insurance",
        user_goals=["understand IUL benefits", "learn about cash value"],
        client_context=ClientContext.PERSONAL,
        calculator_state=None,
        calculator_type=None
    )
    
    # Test cases
    test_cases = [
        {
            "query": "Can you expand on the cash value that you mentioned?",
            "expected_intent": "life_insurance_education",
            "description": "Follow-up question about cash value concept"
        },
        {
            "query": "Tell me more about IUL",
            "expected_intent": "life_insurance_education", 
            "description": "Follow-up question about IUL product"
        },
        {
            "query": "Go deeper into how the growth works",
            "expected_intent": "life_insurance_education",
            "description": "Follow-up question about growth mechanics"
        },
        {
            "query": "What about the death benefit?",
            "expected_intent": "life_insurance_education",
            "description": "Follow-up question about death benefit feature"
        },
        {
            "query": "what did we just talk about?",
            "expected_intent": "conversation_management",
            "description": "Conversation management question"
        },
        {
            "query": "summarize our conversation",
            "expected_intent": "conversation_management",
            "description": "Conversation management question"
        },
        {
            "query": "What is term life insurance?",
            "expected_intent": "life_insurance_education",
            "description": "New question about term life concept"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['description']}")
        print(f"Query: '{test_case['query']}'")
        
        try:
            # Classify the intent
            intent_result = await classifier.classify_intent_semantically(
                test_case['query'], 
                context
            )
            
            actual_intent = intent_result.intent.value
            expected_intent = test_case['expected_intent']
            
            # Check if classification is correct
            is_correct = actual_intent == expected_intent
            
            print(f"Expected: {expected_intent}")
            print(f"Actual:   {actual_intent}")
            print(f"Confidence: {intent_result.confidence}")
            print(f"Reasoning: {intent_result.reasoning[:100]}...")
            print(f"Result: {'✅ PASS' if is_correct else '❌ FAIL'}")
            
            results.append({
                "test_case": test_case,
                "actual_intent": actual_intent,
                "expected_intent": expected_intent,
                "is_correct": is_correct,
                "confidence": intent_result.confidence,
                "reasoning": intent_result.reasoning
            })
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results.append({
                "test_case": test_case,
                "error": str(e),
                "is_correct": False
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.get('is_correct', False))
    total = len(results)
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get('is_correct', False) else "❌ FAIL"
        print(f"{i}. {status} - {result['test_case']['description']}")
        if 'error' in result:
            print(f"   Error: {result['error']}")
        elif 'actual_intent' in result:
            print(f"   Expected: {result['expected_intent']}, Got: {result['actual_intent']}")
    
    # Check if the main issue is fixed
    follow_up_tests = [r for r in results if "Follow-up question" in r['test_case']['description']]
    follow_up_passed = sum(1 for r in follow_up_tests if r.get('is_correct', False))
    
    print(f"\n🎯 FOLLOW-UP QUESTION TESTS:")
    print(f"Follow-up questions passed: {follow_up_passed}/{len(follow_up_tests)}")
    
    if follow_up_passed == len(follow_up_tests):
        print("🎉 SUCCESS: All follow-up questions are now classified correctly!")
        print("   The intent classification fix is working properly.")
    else:
        print("⚠️  WARNING: Some follow-up questions are still misclassified.")
        print("   The fix may need additional adjustments.")
    
    return results

if __name__ == "__main__":
    print("🚀 Starting Intent Classification Fix Test")
    print("This test verifies that follow-up questions like 'expand on cash value'")
    print("are classified as 'life_insurance_education' instead of 'conversation_management'")
    print()
    
    try:
        results = asyncio.run(test_follow_up_intent_classification())
        
        # Exit with appropriate code
        all_passed = all(r.get('is_correct', False) for r in results)
        sys.exit(0 if all_passed else 1)
        
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
Test script to verify that user experience sharing is no longer treated as knowledge requests
"""

import asyncio
import os
import sys
from app.services.dialogue_manager import DialogueManager

# Test cases from the user's examples
test_cases = [
    {
        "name": "User sharing IT service proposal experience",
        "user_response": "例えば、初心者のお客様向けにITサービスを紹介する資料では、専門用語を避け、課題→解決策→効果の順に構成し、身近な例を用いて説明しました。",
        "expected": "Should NOT be treated as a request for knowledge"
    },
    {
        "name": "User sharing presentation experience",
        "user_response": "「結論→理由→具体例」の順でスライドを構成し、1スライド1メッセージを守ったことで、相手に内容がスムーズに伝わりました。図やアイコンを使って視覚的に整理した点も効果的でした。",
        "expected": "Should NOT be treated as a request for knowledge"
    },
    {
        "name": "Actual request for example",
        "user_response": "具体例を教えてください。どのような資料を作成すればいいか例を見せてください。",
        "expected": "Should be treated as a request for knowledge"
    },
    {
        "name": "Actual request for template",
        "user_response": "テンプレートをください。参考になる資料があれば見せてください。",
        "expected": "Should be treated as a request for knowledge"
    },
    {
        "name": "User asking question (not request)",
        "user_response": "どのようにすれば効果的な資料が作れますか？",
        "expected": "Should NOT be treated as a request for knowledge"
    }
]

async def test_user_experience_detection():
    """Test the fixed user experience detection"""
    
    # Initialize dialogue manager
    dialogue_manager = DialogueManager()
    await dialogue_manager.initialize()
    
    # Test instruction for context
    test_instruction = {
        "abstract_concept": "伝わる資料作成",
        "original_text": "もっと伝わる資料を作れるようになるといいね",
        "category": "document_creation"
    }
    
    print("Testing User Experience Detection Fix")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {test_case['user_response']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            # Test the fixed method
            result = await dialogue_manager._check_for_specific_user_request(
                test_case['user_response'],
                test_instruction
            )
            
            # Analyze result
            if result is None:
                actual = "No request detected (correct for experience sharing)"
                is_correct = "NOT be treated as a request" in test_case['expected']
            else:
                actual = f"Request detected: {result['type']} (confidence: {result.get('confidence', 'N/A')})"
                is_correct = "Should be treated as a request" in test_case['expected']
            
            print(f"Actual: {actual}")
            print(f"Status: {'✅ PASS' if is_correct else '❌ FAIL'}")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Status: ❌ ERROR")
        
        print("-" * 40)
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_user_experience_detection())
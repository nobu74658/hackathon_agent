#!/usr/bin/env python3
"""
Test script to verify the complete dialogue flow with the user experience fix
"""

import asyncio
import os
import sys
from app.services.dialogue_manager import DialogueManager

async def test_complete_dialogue_flow():
    """Test the complete dialogue flow with user experience sharing"""
    
    # Initialize dialogue manager
    dialogue_manager = DialogueManager()
    await dialogue_manager.initialize()
    
    print("Testing Complete Dialogue Flow with User Experience Fix")
    print("=" * 70)
    
    # Simulate the 1on1 content that would trigger the process
    one_on_one_content = """
    上司：営業活動の調子はどう？
    新人：新規のアポは取れているのですが、なかなか成約に結びつかないです。
    上司：そうだね。お客さんとの距離を詰めるのがカギだと思うんだ。もう少し相手の課題に寄り添った提案ができるといいね。
    新人：距離を詰めるというのは、具体的にはどういうことでしょうか？
    上司：うーん、例えば相手の話をよく聞いて、本当に困っていることを理解することかな。それに、相手の温度感を読む感覚も大切だよ。
    新人：温度感ですか...少し曖昧で、具体的にどうすればいいのかよくわからないです。
    上司：そうだね、抽象的だね。数こなして感覚を磨いていけるといいかな。
    """
    
    session_id = "test_session_001"
    
    # Step 1: Initial 1on1 processing
    print("Step 1: Processing initial 1on1 content...")
    result1 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=one_on_one_content,
        db_session=None
    )
    
    print(f"Result type: {result1.get('type')}")
    if result1.get('type') == 'one_on_one_clarification':
        print(f"Questions generated: {len(result1.get('questions', []))}")
        print(f"Current instruction: {result1.get('instruction_being_clarified', {}).get('abstract_concept', 'N/A')}")
    print()
    
    # Step 2: User shares their experience (should NOT trigger knowledge provision)
    print("Step 2: User shares their own experience...")
    user_experience_response = "例えば、初心者のお客様向けにITサービスを紹介する資料では、専門用語を避け、課題→解決策→効果の順に構成し、身近な例を用いて説明しました。"
    
    result2 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=user_experience_response,
        db_session=None
    )
    
    print(f"Result type: {result2.get('type')}")
    if result2.get('type') == 'knowledge_provision':
        print("❌ ISSUE: User experience was treated as knowledge request!")
        print(f"Knowledge response provided: {result2.get('knowledge_response', '')[:100]}...")
    elif result2.get('type') == 'one_on_one_clarification':
        print("✅ GOOD: User experience processed as dialogue continuation")
        print(f"Next questions: {len(result2.get('questions', []))}")
    print()
    
    # Step 3: User asks for actual knowledge
    print("Step 3: User makes an actual knowledge request...")
    knowledge_request = "具体例を教えてください。参考になる提案資料のテンプレートがあれば見せてください。"
    
    result3 = await dialogue_manager.process_user_response(
        session_id=session_id,
        user_response=knowledge_request,
        db_session=None
    )
    
    print(f"Result type: {result3.get('type')}")
    if result3.get('type') == 'knowledge_provision':
        print("✅ GOOD: Actual knowledge request properly handled")
        print(f"Knowledge provided: {result3.get('knowledge_response', '')[:100]}...")
    else:
        print("❌ ISSUE: Actual knowledge request not handled properly")
    print()
    
    print("Test completed!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_complete_dialogue_flow())
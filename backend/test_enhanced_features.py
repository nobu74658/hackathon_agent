#!/usr/bin/env python3
"""
改善された機能のテストスクリプト
"""

import asyncio
import sys
from datetime import datetime

# サービスのインポートテスト
def test_imports():
    """インポートのテスト"""
    print("🧪 インポートテスト開始...")
    
    try:
        from app.services.knowledge_base_service import KnowledgeBaseService
        print("✅ KnowledgeBaseService インポート成功")
    except Exception as e:
        print(f"❌ KnowledgeBaseService インポート失敗: {e}")
        return False
    
    try:
        from app.services.action_template_generator import ActionTemplateGenerator
        print("✅ ActionTemplateGenerator インポート成功")
    except Exception as e:
        print(f"❌ ActionTemplateGenerator インポート失敗: {e}")
        return False
    
    try:
        from app.services.enhanced_dialogue_manager import EnhancedDialogueManager
        print("✅ EnhancedDialogueManager インポート成功")
    except Exception as e:
        print(f"❌ EnhancedDialogueManager インポート失敗: {e}")
        return False
    
    try:
        from app.api.enhanced_llm_endpoints import router
        print("✅ Enhanced API エンドポイント インポート成功")
    except Exception as e:
        print(f"❌ Enhanced API エンドポイント インポート失敗: {e}")
        return False
    
    return True

async def test_knowledge_base():
    """知識ベースサービスのテスト"""
    print("\n🧪 知識ベースサービステスト開始...")
    
    from app.services.knowledge_base_service import KnowledgeBaseService
    
    kb_service = KnowledgeBaseService()
    
    # 会社の価値観取得テスト
    try:
        values = await kb_service.get_company_values()
        print(f"✅ 会社の価値観取得成功")
        print(f"   ミッション: {values.get('mission', 'N/A')[:50]}...")
        print(f"   バリュー数: {len(values.get('values', []))}")
    except Exception as e:
        print(f"❌ 会社の価値観取得失敗: {e}")
        return False
    
    # 知識検索テスト
    try:
        results = await kb_service.search_knowledge("緊張")
        print(f"✅ 知識検索成功")
        print(f"   検索結果数: {len(results)}")
        if results:
            print(f"   最初の結果カテゴリ: {results[0].get('category', 'N/A')}")
    except Exception as e:
        print(f"❌ 知識検索失敗: {e}")
        return False
    
    # 課題解決策取得テスト
    try:
        solution = await kb_service.get_solution_for_challenge("緊張で頭が真っ白")
        print(f"✅ 課題解決策取得成功")
        if solution:
            print(f"   課題: {solution.get('challenge', 'N/A')}")
            print(f"   マッチタイプ: {solution.get('type', 'N/A')}")
    except Exception as e:
        print(f"❌ 課題解決策取得失敗: {e}")
        return False
    
    return True

async def test_template_generator():
    """テンプレート生成サービスのテスト"""
    print("\n🧪 テンプレート生成サービステスト開始...")
    
    from app.services.action_template_generator import ActionTemplateGenerator
    
    generator = ActionTemplateGenerator()
    
    # テンプレート一覧取得テスト
    try:
        templates = await generator.list_available_templates()
        print(f"✅ テンプレート一覧取得成功")
        print(f"   カテゴリ数: {len(templates)}")
        for category, items in templates.items():
            print(f"   - {category}: {len(items)}個のテンプレート")
    except Exception as e:
        print(f"❌ テンプレート一覧取得失敗: {e}")
        return False
    
    # アクションプラン生成テスト
    try:
        context = {
            "user_name": "テストユーザー",
            "experience_years": 1,
            "department": "営業部"
        }
        plan = await generator.generate_action_plan(
            challenge="新規開拓がうまくいかない",
            context=context,
            timeline="1ヶ月"
        )
        print(f"✅ アクションプラン生成成功")
        print(f"   アクションアイテム数: {len(plan.get('action_items', []))}")
        print(f"   使用テンプレート数: {len(plan.get('templates_used', []))}")
        print(f"   必要リソース数: {len(plan.get('required_resources', []))}")
    except Exception as e:
        print(f"❌ アクションプラン生成失敗: {e}")
        return False
    
    return True

async def test_enhanced_dialogue_manager():
    """改善された対話マネージャーのテスト（LLM呼び出しなし）"""
    print("\n🧪 改善された対話マネージャーテスト開始...")
    
    from app.services.enhanced_dialogue_manager import EnhancedDialogueManager
    
    # Note: 実際のLLM呼び出しは行わないため、このテストは限定的
    try:
        manager = EnhancedDialogueManager()
        print("✅ EnhancedDialogueManager インスタンス作成成功")
        
        # 自己解決メカニズムのテスト
        questions = ["営業の基本は？", "プレゼンのコツは？"]
        context = {"session_id": "test-session"}
        
        resolution = await manager.self_resolve_questions(questions, context)
        print(f"✅ 自己解決メカニズム実行成功")
        print(f"   解決された質問数: {len(resolution.resolved_questions)}")
        print(f"   残りの質問数: {len(resolution.remaining_questions)}")
        print(f"   確信度: {resolution.confidence_level}")
        
    except Exception as e:
        print(f"❌ 対話マネージャーテスト失敗: {e}")
        return False
    
    return True

async def test_api_structure():
    """APIエンドポイント構造のテスト"""
    print("\n🧪 APIエンドポイント構造テスト開始...")
    
    try:
        from app.api.enhanced_llm_endpoints import router
        
        # ルートのパスを確認
        routes = []
        for route in router.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        print(f"✅ APIルーター構造確認成功")
        print(f"   エンドポイント数: {len(routes)}")
        print("   主要エンドポイント:")
        for route in routes[:5]:  # 最初の5個を表示
            print(f"   - {route}")
        
    except Exception as e:
        print(f"❌ API構造テスト失敗: {e}")
        return False
    
    return True

def main():
    """メインテスト実行"""
    print("=" * 60)
    print("🧪 改善された機能のテスト")
    print(f"   実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 同期テスト
    if not test_imports():
        print("\n❌ インポートテストに失敗しました")
        sys.exit(1)
    
    # 非同期テスト
    async def run_async_tests():
        results = []
        
        results.append(await test_knowledge_base())
        results.append(await test_template_generator())
        results.append(await test_enhanced_dialogue_manager())
        results.append(await test_api_structure())
        
        return all(results)
    
    # 非同期テストの実行
    success = asyncio.run(run_async_tests())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ すべてのテストが成功しました！")
    else:
        print("❌ 一部のテストが失敗しました")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
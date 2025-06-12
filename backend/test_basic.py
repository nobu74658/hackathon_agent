#!/usr/bin/env python3
"""
基本的な動作確認テスト
uvのインストールやLangChainなしでも実行可能
"""

import requests
import json
import sys
import subprocess
from pathlib import Path

def test_imports():
    """基本的なPythonモジュールのインポートテスト"""
    print("=== インポートテスト ===")
    
    modules_to_test = [
        "fastapi",
        "pydantic", 
        "uvicorn",
        "langchain",
        "sqlalchemy"
    ]
    
    results = {}
    for module in modules_to_test:
        try:
            __import__(module)
            results[module] = "✓ OK"
        except ImportError as e:
            results[module] = f"✗ NG: {e}"
    
    for module, result in results.items():
        print(f"{module}: {result}")
    
    return all("✓" in result for result in results.values())

def test_app_structure():
    """アプリケーション構造のテスト"""
    print("\n=== アプリケーション構造テスト ===")
    
    required_files = [
        "app/__init__.py",
        "app/main.py", 
        "app/core/__init__.py",
        "app/core/config.py",
        "app/services/__init__.py",
        "app/services/conversation_memory.py",
        "app/services/dialogue_manager.py",
        "pyproject.toml"
    ]
    
    base_path = Path(__file__).parent
    missing_files = []
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_config_loading():
    """設定ファイルの読み込みテスト"""
    print("\n=== 設定読み込みテスト ===")
    
    try:
        import sys
        sys.path.append(str(Path(__file__).parent))
        
        from app.core.config import settings
        
        print(f"✓ APP_NAME: {settings.APP_NAME}")
        print(f"✓ DATABASE_URL: {settings.DATABASE_URL}")
        print(f"✓ DEBUG: {settings.DEBUG}")
        return True
        
    except Exception as e:
        print(f"✗ 設定読み込みエラー: {e}")
        return False

def test_service_instantiation():
    """サービスクラスのインスタンス化テスト"""
    print("\n=== サービスインスタンス化テスト ===")
    
    try:
        import sys
        sys.path.append(str(Path(__file__).parent))
        
        # LangChainを使わない基本テスト
        from app.services.conversation_memory import ConversationMemoryService
        from app.services.dialogue_manager import DialogueManager
        
        memory_service = ConversationMemoryService()
        dialogue_manager = DialogueManager()
        
        print("✓ ConversationMemoryService: インスタンス化成功")
        print("✓ DialogueManager: インスタンス化成功")
        return True
        
    except Exception as e:
        print(f"✗ サービスインスタンス化エラー: {e}")
        return False

def run_server_test():
    """サーバー起動テスト"""
    print("\n=== サーバー起動テスト ===")
    
    try:
        # バックグラウンドでサーバー起動
        import subprocess
        import time
        import signal
        
        process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8001",  # テスト用ポート
            "--log-level", "error"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # サーバー起動を待つ
        time.sleep(3)
        
        # ヘルスチェック
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ サーバー起動成功: {data}")
            success = True
        else:
            print(f"✗ ヘルスチェック失敗: {response.status_code}")
            success = False
        
        # プロセス終了
        process.terminate()
        process.wait(timeout=5)
        
        return success
        
    except Exception as e:
        print(f"✗ サーバーテストエラー: {e}")
        return False

def main():
    """メインテスト実行"""
    print("Backend Basic Test Suite")
    print("=" * 50)
    
    tests = [
        ("インポートテスト", test_imports),
        ("アプリケーション構造テスト", test_app_structure), 
        ("設定読み込みテスト", test_config_loading),
        ("サービスインスタンス化テスト", test_service_instantiation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name}でエラー: {e}")
            results.append((test_name, False))
    
    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー:")
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n合計: {passed}/{len(results)} テスト通過")
    
    if passed == len(results):
        print("✓ すべてのテストが通過しました！")
        return True
    else:
        print("✗ 一部のテストが失敗しました。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
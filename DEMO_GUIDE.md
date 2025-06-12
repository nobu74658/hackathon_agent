# 🤖 新人営業マン成長支援AIエージェント - デモガイド

## 📋 概要

このデモでは、実際のLLM API（OpenAI GPT または Anthropic Claude）を使用して、新人営業マンとの対話から営業スキル向上のためのアクションプランを自動生成するシステムを体験できます。

## 🎯 デモの機能

- **対話型情報収集**: AIが適切な質問を生成し、営業課題を深掘り
- **リアルタイム分析**: 感情分析、情報充足度評価
- **自動アクションプラン生成**: 具体的で実行可能な改善プランを作成
- **複数LLMプロバイダー対応**: OpenAI と Anthropic の切り替え可能

## 🚀 セットアップ手順

### 前提条件

- Python 3.11以上
- OpenAI API key または Anthropic API key
- インターネット接続

### 1. リポジトリの準備

```bash
cd hackathon_agent/backend
```

### 2. 仮想環境の作成

#### uvを使用する場合（推奨）
```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh
# または
brew install uv

# 仮想環境作成と有効化
uv venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows
```

#### 通常のvenvを使用する場合
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate     # Windows
```

### 3. 依存関係のインストール

#### uvの場合
```bash
uv pip install fastapi uvicorn pydantic aiohttp python-dotenv pydantic-settings
uv pip install langchain langchain-openai langchain-anthropic langchain-community
```

#### pipの場合
```bash
pip install fastapi uvicorn pydantic aiohttp python-dotenv pydantic-settings
pip install langchain langchain-openai langchain-anthropic langchain-community
```

### 4. API keyの設定

`.env`ファイルを編集して、使用するLLMプロバイダーのAPI keyを設定してください：

```bash
# .envファイルを編集
nano .env  # または任意のエディタ

# 以下の設定を行ってください
USE_MOCK_LLM=false

# OpenAIを使用する場合
OPENAI_API_KEY=your-actual-openai-api-key-here

# Anthropicを使用する場合
ANTHROPIC_API_KEY=your-actual-anthropic-api-key-here

# 両方設定しても構いません（デモ時に選択可能）
```

#### API keyの取得方法

**OpenAI API key:**
1. https://platform.openai.com/ にアクセス
2. アカウント作成/ログイン
3. API Keys セクションで新しいキーを作成

**Anthropic API key:**
1. https://console.anthropic.com/ にアクセス
2. アカウント作成/ログイン
3. API Keys セクションで新しいキーを作成

## 🎮 デモの実行

### 1. サーバーの起動

```bash
uvicorn app.main:app --reload --port 8000
```

サーバーが正常に起動すると、以下のメッセージが表示されます：
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

### 2. API接続の確認

別のターミナルを開いて、API接続をテストします：

```bash
# ヘルスチェック
curl http://localhost:8000/health

# OpenAI接続テスト
curl http://localhost:8000/demo/test-connection/openai

# Anthropic接続テスト
curl http://localhost:8000/demo/test-connection/anthropic
```

### 3. インタラクティブデモの実行

```bash
python demo_script.py
```

#### デモの流れ

1. **LLMプロバイダー選択**
   ```
   LLMプロバイダーを選択してください:
   1. OpenAI GPT-3.5-turbo
   2. Anthropic Claude
   選択 (1-2): 1
   ```

2. **接続テスト**
   ```
   🔍 OPENAI 接続テスト中...
   ✅ OPENAI 接続成功!
   ```

3. **セッション開始**
   AIが初期質問を生成します：
   ```
   📝 生成された質問:
   1. どのような場面で最も困難を感じますか？
   2. 現在の営業活動で最も時間を取られていることは何ですか？
   3. 理想的な営業成果とはどのようなものですか？
   ```

4. **対話フェーズ**
   質問に回答していくと、AIが追加質問を生成または情報が十分な場合はアクションプランを作成します。

5. **アクションプラン生成**
   情報が充足すると、具体的なアクションプランが生成されます：
   ```
   🎯 アクションプラン生成完了!
   📋 サマリー: 新規顧客開拓スキル向上のための包括的なプラン
   📈 アクションアイテム:
   1. 顧客ニーズ分析スキルの向上
   2. 効果的なアプローチ方法の習得
   3. フォローアップ体制の構築
   ```

### 4. バッチデモの実行

事前に用意されたサンプル会話で自動実行：

```bash
python demo_script.py batch
```

## 🌐 Web APIの直接利用

### デモセッション開始

```bash
curl -X POST http://localhost:8000/demo/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_name": "田中太郎",
    "department": "営業部", 
    "experience_years": 1,
    "initial_topic": "新規顧客開拓のスキル向上",
    "llm_provider": "openai"
  }'
```

### メッセージ送信

```bash
curl -X POST http://localhost:8000/demo/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "取得したセッションID",
    "message": "新規顧客へのアプローチ方法に悩んでいます"
  }'
```

### セッション情報取得

```bash
curl http://localhost:8000/demo/session/{session_id}
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. API key エラー
```
❌ LLMサービス初期化エラー: OPENAI_API_KEYが設定されていません
```

**解決方法:**
- `.env`ファイルの`OPENAI_API_KEY`または`ANTHROPIC_API_KEY`を確認
- API keyが正しく設定されているか確認
- 環境変数が正しく読み込まれているか確認

#### 2. モジュールインストールエラー
```
ImportError: No module named 'langchain_openai'
```

**解決方法:**
```bash
# 仮想環境が有効化されているか確認
which python

# 依存関係を再インストール
pip install langchain langchain-openai langchain-anthropic langchain-community

# サーバーを再起動
pkill -f uvicorn  # 既存プロセス終了
uvicorn app.main:app --reload --port 8000
```

#### 3. サーバー起動エラー
```
OSError: [Errno 48] Address already in use
```

**解決方法:**
```bash
# ポートを変更
uvicorn app.main:app --reload --port 8001

# または既存プロセスを終了
lsof -ti:8000 | xargs kill -9
```

#### 4. API レート制限エラー
```
Rate limit exceeded
```

**解決方法:**
- API使用量を確認
- 少し時間を置いてから再実行
- 異なるAPI keyを使用

### デバッグモード

詳細なログを確認したい場合：

```bash
# ログレベルをDEBUGに変更
LOG_LEVEL=DEBUG uvicorn app.main:app --reload --port 8000
```

## 📊 デモシナリオ例

### シナリオ1: 新規顧客開拓の課題

**ユーザー設定:**
- 名前: 田中太郎
- 部署: 営業部
- 経験年数: 1年
- トピック: 新規顧客開拓

**サンプル回答:**
1. 「テレアポでアポイントが取れません」
2. 「断られることが多く、心が折れそうです」
3. 「月10件の新規顧客獲得が目標です」
4. 「既存顧客のフォローは得意です」

### シナリオ2: プレゼンテーションスキル向上

**ユーザー設定:**
- 名前: 佐藤花子  
- 部署: 営業部
- 経験年数: 2年
- トピック: プレゼンテーションスキル

**サンプル回答:**
1. 「大きな商談でのプレゼンが苦手です」
2. 「緊張して話が伝わりません」
3. 「資料作成は得意ですが、話し方に課題があります」

## 🎯 期待される結果

デモ完了時に以下が得られます：

1. **具体的なアクションプラン**
   - 3-5個の実行可能なアクションアイテム
   - 優先順位と期限の設定
   - 成功指標の定義

2. **個別化された提案**
   - ユーザーの経験レベルに合わせた内容
   - 具体的な課題に基づく解決策
   - 実現可能性を考慮した計画

3. **継続的改善の仕組み**
   - 進捗測定方法
   - 定期レビューのスケジュール
   - 必要なリソースの特定

## 📝 フィードバック

デモの感想や改善提案があれば、以下の方法でお知らせください：

- GitHub Issues
- メール
- Slack（社内の場合）

## 🔗 関連リンク

- [システム設計書](docs/system_design.md)
- [API仕様書](http://localhost:8000/docs) - サーバー起動後にアクセス
- [開発者向けREADME](backend/README.md)
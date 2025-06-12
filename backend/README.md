# 営業成長AI支援エージェントシステム

## 📋 概要

Slack統合による営業担当者向けのAI支援システムです。1対1の営業セッションから課題を分析し、個別の成長アクションプランを生成します。

## 🏗️ システム構成

```mermaid
graph TB
    %% User Interface Layer
    subgraph "👥 User Interface"
        SLACK[📱 Slack]
        USER[👤 Sales Rep]
    end

    %% API Gateway Layer
    subgraph "🌐 API Gateway"
        FASTAPI[🚀 FastAPI Server<br/>Port: 8000]
        SLACK_EP[📡 Slack Endpoints<br/>/api/slack/events]
        HEALTH_EP[🏥 Health Check<br/>/slack/health]
    end

    %% Core Service Layer
    subgraph "🧠 Core AI Services"
        SLACK_SVC[🤖 SlackService<br/>Event Handler]
        DIALOGUE_MGR[💬 DialogueManager<br/>Conversation Flow]
        MEMORY_SVC[🧠 ConversationMemoryService<br/>Context Management]
    end

    %% LLM Integration Layer
    subgraph "🤖 LLM Integration"
        LLM_SELECTOR{USE_MOCK_LLM?}
        MOCK_LLM[🎭 MockLLMProvider<br/>Development Mode]
        REAL_LLM[🧮 RealLLMService<br/>OpenAI GPT-3.5-turbo]
    end

    %% Data Layer
    subgraph "💾 Data Storage"
        REDIS[(🔴 Redis<br/>Conversation Memory<br/>TTL: 24h)]
        SQLITE[(📊 SQLite<br/>Dialogue Sessions<br/>Optional)]
    end

    %% External Services
    subgraph "🌍 External Services"
        OPENAI[🤖 OpenAI API<br/>GPT-3.5-turbo]
        SLACK_API[📡 Slack API<br/>Bot Integration]
    end
```

## 🚀 クイックスタート

### 前提条件
- Python 3.11+
- Redis Server
- OpenAI API Key
- Slack App設定

### セットアップ手順

1. **リポジトリクローンと環境構築**
```bash
cd backend
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -e ".[dev]"
```

2. **Redis起動**
```bash
brew install redis
brew services start redis
```

3. **環境変数設定**
```bash
# .envファイルを作成
cp .env.example .env

# 必要な設定を追加
OPENAI_API_KEY=your-openai-api-key-here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
USE_MOCK_LLM=false
```

4. **サーバー起動**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 使用方法

### Slack統合

1. **ボットメンション**
```
@ai mentor 1on1で新規顧客獲得について話し合いました
```

2. **AI質問応答**
- AIが営業課題に関する質問を返します
- 進捗状況（0-100%）が表示されます

3. **アクションプラン生成**
- 80%の情報が収集されると自動でアクションプランを生成
- 具体的で測定可能な改善項目を提示

### 対話例

```
👤 ユーザー: @営業成長AI 1on1で営業について話し合いました。新規顧客獲得に苦労しています。

🤖 AI: 📊 情報収集進捗: 30%

以下の点について詳しく教えてください：
1. 過去に新規顧客獲得のためにどのようなアプローチを試みたことがありますか？
2. 現在のターゲット顧客層はどのような特徴がありますか？
3. 営業活動で最も時間を取られている部分は何ですか？

👤 ユーザー: テレアポと飛び込み営業を試しましたが、成約率が低いです...

🤖 AI: 🎯 営業成長アクションプラン (完了度: 85%)

📝 概要
テレアポと飛び込み営業の成約率向上を目指した戦略的アプローチの実施

📋 具体的アクション
🔴 顧客リサーチの強化
   └ 事前調査により提案の質を向上させる
   📅 期限: 2024-01-31

🟡 アプローチ手法の多様化
   └ SNS活用、紹介営業の導入
   📅 期限: 2024-02-15
```

## 🛠️ 開発環境

### 開発コマンド

```bash
# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# コード品質チェック
black app tests          # フォーマット
ruff check app tests     # リント
mypy app                 # 型チェック
pytest                   # テスト実行
pytest --cov=app tests/  # カバレッジ付きテスト
```

### デモスクリプト

```bash
# 基本的なAI対話デモ
python demo_script.py

# Slack統合テスト
python slack_demo.py

# Slack設定ガイド
python slack_setup_guide.py
```

## 📁 プロジェクト構造

```
backend/
├── app/
│   ├── main.py                 # FastAPI アプリケーション
│   ├── api/
│   │   ├── slack_endpoints.py  # Slack API エンドポイント
│   │   ├── llm_demo_endpoints.py # AI対話デモ
│   │   └── test_endpoints.py   # テスト用エンドポイント
│   ├── services/
│   │   ├── slack_service.py    # Slack統合サービス
│   │   ├── dialogue_manager.py # 対話フロー管理
│   │   ├── conversation_memory.py # 会話記憶管理
│   │   ├── real_llm_service.py # 本番LLMサービス
│   │   └── mock_llm.py         # 開発用モックサービス
│   ├── models/
│   │   └── dialogue.py         # データベースモデル
│   └── core/
│       └── config.py           # 設定管理
├── tests/                      # テストファイル
├── .env                        # 環境変数
└── README.md                   # このファイル
```

## 🔧 設定詳細

### 環境変数一覧

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `USE_MOCK_LLM` | モックLLM使用フラグ | `false` |
| `OPENAI_API_KEY` | OpenAI APIキー | `sk-...` |
| `OPENAI_MODEL` | 使用するOpenAIモデル | `gpt-3.5-turbo` |
| `SLACK_BOT_TOKEN` | Slack Bot Token | `xoxb-...` |
| `SLACK_SIGNING_SECRET` | Slack Signing Secret | `abc123...` |
| `REDIS_URL` | Redis接続URL | `redis://localhost:6379/0` |
| `DATABASE_URL` | DB接続URL（オプション） | `sqlite+aiosqlite:///./test.db` |

### Slack App設定

1. **Slack Appの作成**
   - https://api.slack.com/apps でアプリを作成
   - Bot Token Scopes: `app_mentions:read`, `chat:write`, `im:read`, `im:write`

2. **Event Subscriptions**
   - Request URL: `https://your-domain.com/api/slack/events`
   - Subscribe to bot events: `app_mention`, `message.im`

3. **Install App**
   - ワークスペースにアプリをインストール
   - Bot User OAuth Tokenを取得

## 🧠 AI機能詳細

### 対話フロー

1. **初期分析**
   - ユーザーの入力から営業課題を抽出
   - 情報の完成度を0-100%で評価

2. **質問生成**
   - 不足している情報に基づいて追加質問を生成
   - 最大5つまでの具体的な質問

3. **アクションプラン作成**
   - 80%以上の情報が集まった時点で実行
   - 優先度付きの具体的な改善項目
   - 期限と成功指標を含む

### 情報評価観点

- 現在の課題や悩みの明確性
- 具体的な状況や事例の有無
- 目標や期待される成果の明確性
- 現在のスキルレベルの把握
- 利用可能なリソースや制約の理解

## 🛡️ 安全機能

### イベント重複防止
- タイムスタンプベースの重複検出
- 5分間のイベント履歴保持
- Bot自身のメッセージ除外

### エラーハンドリング
- LLM API障害時のグレースフル処理
- Redis接続エラー時の代替処理
- Slack API制限への対応

## 🧪 テスト

### ユニットテスト
```bash
# 全テスト実行
pytest

# カバレッジ付きテスト
pytest --cov=app tests/

# 特定のテスト実行
pytest tests/test_dialogue_manager.py
```

### 統合テスト
```bash
# Mock LLMでのテスト
USE_MOCK_LLM=true python demo_script.py

# Slack統合テスト
python slack_demo.py
```

## 🚀 デプロイ

### 本番環境設定

1. **環境変数設定**
```bash
export USE_MOCK_LLM=false
export OPENAI_API_KEY=your-production-key
export REDIS_URL=redis://your-redis-server:6379/0
```

2. **Redis設定**
```bash
# 本番Redis設定
redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

3. **アプリケーション起動**
```bash
# 本番起動
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (オプション)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e ".[dev]"
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📊 監視・ログ

### ログレベル設定
```bash
export LOG_LEVEL=INFO
export LOG_FORMAT=json
```

### ヘルスチェック
```bash
curl http://localhost:8000/api/slack/health
```

### メトリクス

- 対話セッション数
- 質問生成回数
- アクションプラン作成数
- API応答時間
- エラー率

## 🔄 継続的改善

### モニタリング指標

1. **ユーザーエクスペリエンス**
   - 対話完了率
   - 平均セッション時間
   - ユーザー満足度

2. **技術指標**
   - API応答時間
   - エラー率
   - リソース使用率

3. **ビジネス指標**
   - 営業スキル向上度
   - アクションプラン実行率
   - ROI測定

## 🤝 コントリビューション

1. フォークしてブランチを作成
2. 変更を実装
3. テストを追加・実行
4. プルリクエストを作成

## 📜 ライセンス

MIT License

## 📞 サポート

- 技術的な質問: [Issues](https://github.com/your-repo/issues)
- 機能要望: [Discussions](https://github.com/your-repo/discussions)
- バグレポート: [Bug Report Template](https://github.com/your-repo/issues/new?template=bug_report.md)

---

🚀 **営業成長AI支援エージェント** - あなたの営業スキル向上をAIがサポートします！
# 営業成長AI支援エージェント - API仕様書

## 📡 API概要

### Base URL
```
http://localhost:8000
```

### 認証
- Slack Events API: Signing Secret検証
- 内部API: 認証なし（開発環境）

### レスポンス形式
- Content-Type: `application/json`
- 文字エンコーディング: UTF-8

## 🔗 エンドポイント一覧

### 1. Slack Events API

#### POST /api/slack/events
Slack Events APIのメインwebhookエンドポイント

**リクエスト**
```http
POST /api/slack/events
Content-Type: application/json
X-Slack-Signature: sha256=...
X-Slack-Request-Timestamp: 1531420618

{
  "token": "verification_token",
  "team_id": "T1234567890",
  "api_app_id": "A1234567890",
  "event": {
    "type": "app_mention",
    "user": "U1234567890",
    "text": "<@U987654321> 営業について相談したいです",
    "ts": "1531420618.000200",
    "channel": "C1234567890",
    "event_ts": "1531420618.000200"
  },
  "type": "event_callback",
  "event_id": "Ev1234567890",
  "event_time": 1531420618
}
```

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
}
```

**エラーレスポンス**
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "Slack credentials not configured"
}
```

#### GET /api/slack/health
Slack統合のヘルスチェック

**レスポンス（正常）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "message": "Slack integration is configured and ready",
  "use_mock_llm": false
}
```

**レスポンス（異常）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "error",
  "message": "SLACK_BOT_TOKEN not configured"
}
```

### 2. LLM Demo API

#### POST /api/llm/start-dialogue
AI対話セッション開始

**リクエスト**
```http
POST /api/llm/start-dialogue
Content-Type: application/json

{
  "session_id": "demo_session_123",
  "initial_context": {
    "topic": "新規顧客獲得",
    "urgency": "high",
    "department": "営業部"
  }
}
```

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "questions": [
    "どのような業界の新規顧客を獲得したいですか？",
    "現在の営業アプローチで最も効果的だったものは何ですか？",
    "新規顧客獲得の目標数値はありますか？"
  ],
  "metadata": {
    "stage": "initial",
    "reasoning": "新規顧客獲得の詳細を把握するために基本的な質問から開始します",
    "information_needed": ["ターゲット業界", "現在の手法", "目標設定"],
    "completeness_score": 10
  }
}
```

#### POST /api/llm/process-response
ユーザー回答の処理

**リクエスト**
```http
POST /api/llm/process-response
Content-Type: application/json

{
  "session_id": "demo_session_123",
  "user_response": "IT業界をターゲットにしていて、テレアポが中心ですが成約率が低いです"
}
```

**レスポンス（追加質問）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "type": "follow_up",
  "questions": [
    "現在のテレアポの成約率はどの程度ですか？",
    "IT業界のどのような企業規模をターゲットにしていますか？",
    "テレアポ以外に試したことがある営業手法はありますか？"
  ],
  "completeness_score": 45
}
```

**レスポンス（アクションプラン）**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "type": "action_plan",
  "data": {
    "action_items": [
      {
        "id": "action_1",
        "title": "IT業界特化型アプローチの開発",
        "description": "IT業界の課題に特化したトークスクリプトの作成",
        "priority": "high",
        "due_date": "2024-02-15",
        "category": "approach_improvement",
        "metrics": ["成約率", "アポイント獲得率"]
      }
    ],
    "summary": "IT業界の新規顧客獲得において、テレアポの質向上と多角的なアプローチの実施",
    "key_improvements": [
      "業界特化型トークスクリプト開発",
      "デジタルマーケティング活用",
      "既存顧客からの紹介制度構築"
    ],
    "metrics": {
      "success_indicators": ["成約率向上", "新規顧客獲得数増加"],
      "review_frequency": "monthly",
      "evaluation_criteria": ["定量評価", "定性評価"]
    }
  },
  "completeness_score": 85
}
```

#### GET /api/llm/session/{session_id}
セッション情報の取得

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "session_id": "demo_session_123",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "message_count": 8,
  "completeness_score": 75,
  "stage": "gathering"
}
```

### 3. Test API

#### GET /api/test/health
基本的なヘルスチェック

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0"
}
```

#### POST /api/test/echo
エコーテスト

**リクエスト**
```http
POST /api/test/echo
Content-Type: application/json

{
  "message": "テストメッセージ"
}
```

**レスポンス**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "echo": "テストメッセージ",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 📋 データモデル

### Slack Event Model
```typescript
interface SlackEvent {
  token: string;
  team_id: string;
  api_app_id: string;
  event: {
    type: "app_mention" | "message";
    user: string;
    text: string;
    ts: string;
    channel: string;
    event_ts: string;
    subtype?: string;
    bot_id?: string;
  };
  type: "event_callback" | "url_verification";
  event_id: string;
  event_time: number;
  challenge?: string;
}
```

### Dialogue Session Model
```typescript
interface DialogueSession {
  session_id: string;
  user_id: string;
  status: "active" | "completed" | "archived";
  created_at: string;
  updated_at: string;
  completeness_score: number;
  stage: "initial" | "gathering" | "clarifying" | "planning";
}
```

### AI Response Model
```typescript
interface AIResponse {
  type: "follow_up" | "action_plan";
  questions?: string[];
  data?: ActionPlan;
  completeness_score: number;
  metadata?: {
    reasoning: string;
    information_needed: string[];
    stage: string;
  };
}
```

### Action Plan Model
```typescript
interface ActionPlan {
  action_items: ActionItem[];
  summary: string;
  key_improvements: string[];
  metrics: {
    success_indicators: string[];
    review_frequency: string;
    evaluation_criteria: string[];
  };
  generated_at: string;
}

interface ActionItem {
  id: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  due_date: string;
  category: string;
  metrics: string[];
}
```

## 🚨 エラーコード

### HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | 正常な処理完了 |
| 400 | Bad Request | 不正なリクエスト形式 |
| 401 | Unauthorized | 認証エラー |
| 403 | Forbidden | アクセス権限なし |
| 404 | Not Found | リソースが見つからない |
| 500 | Internal Server Error | サーバー内部エラー |
| 503 | Service Unavailable | サービス利用不可 |

### Application Error Codes

```typescript
interface ErrorResponse {
  detail: string;
  error_code?: string;
  error_type?: "validation" | "authentication" | "authorization" | "internal";
  timestamp: string;
}
```

### 具体的なエラー例

#### Slack認証エラー
```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "detail": "Slack credentials not configured",
  "error_code": "SLACK_CONFIG_ERROR",
  "error_type": "internal",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### セッション不存在エラー
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Session demo_session_123 not found",
  "error_code": "SESSION_NOT_FOUND",
  "error_type": "validation",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### OpenAI API エラー
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "detail": "LLM service temporarily unavailable",
  "error_code": "LLM_SERVICE_ERROR", 
  "error_type": "internal",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔧 設定パラメータ

### 環境変数

| 変数名 | 型 | デフォルト | 説明 |
|--------|-----|----------|------|
| `USE_MOCK_LLM` | boolean | `false` | モックLLM使用フラグ |
| `OPENAI_API_KEY` | string | `""` | OpenAI APIキー |
| `OPENAI_MODEL` | string | `"gpt-3.5-turbo"` | 使用するOpenAIモデル |
| `SLACK_BOT_TOKEN` | string | `""` | Slack Bot Token |
| `SLACK_SIGNING_SECRET` | string | `""` | Slack Signing Secret |
| `REDIS_URL` | string | `"redis://localhost:6379/0"` | Redis接続URL |
| `CORS_ORIGINS` | string | `"*"` | CORS許可オリジン |
| `LOG_LEVEL` | string | `"INFO"` | ログレベル |

### レート制限

| API | 制限 | 備考 |
|-----|------|------|
| Slack Events | 30,000リクエスト/時間 | Slack側の制限 |
| OpenAI API | 3,500リクエスト/分 | プランにより異なる |
| 内部API | 制限なし | 開発環境 |

## 📚 使用例

### cURL Examples

#### Slack Webhook テスト
```bash
curl -X POST http://localhost:8000/api/slack/events \
  -H "Content-Type: application/json" \
  -H "X-Slack-Signature: sha256=..." \
  -H "X-Slack-Request-Timestamp: 1531420618" \
  -d '{
    "type": "url_verification",
    "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
  }'
```

#### ヘルスチェック
```bash
curl -X GET http://localhost:8000/api/slack/health
```

#### AI対話開始
```bash
curl -X POST http://localhost:8000/api/llm/start-dialogue \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session",
    "initial_context": {
      "topic": "営業スキル向上",
      "urgency": "medium"
    }
  }'
```

### Python SDK Example

```python
import httpx
import asyncio

async def test_dialogue():
    async with httpx.AsyncClient() as client:
        # セッション開始
        response = await client.post(
            "http://localhost:8000/api/llm/start-dialogue",
            json={
                "session_id": "python_test",
                "initial_context": {"topic": "新規顧客獲得"}
            }
        )
        print("Initial Questions:", response.json()["questions"])
        
        # ユーザー回答処理
        response = await client.post(
            "http://localhost:8000/api/llm/process-response",
            json={
                "session_id": "python_test", 
                "user_response": "IT業界をターゲットにしています"
            }
        )
        result = response.json()
        print(f"Response Type: {result['type']}")
        print(f"Completeness: {result['completeness_score']}%")

# 実行
asyncio.run(test_dialogue())
```

## 🔍 デバッグ・トラブルシューティング

### ログ出力例

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "message": "Processing user message",
  "session_id": "slack_U1234567890",
  "user_id": "U1234567890",
  "completeness_score": 65,
  "response_type": "follow_up"
}
```

### 一般的な問題と解決方法

1. **Slack Events 受信できない**
   - Webhook URLの確認
   - Signing Secretの確認
   - ネットワーク接続確認

2. **OpenAI API エラー**
   - API キーの確認
   - レート制限の確認
   - API残高の確認

3. **Redis接続エラー**
   - Redisサーバーの起動確認
   - 接続URLの確認
   - ファイアウォール設定の確認

---

この仕様書は開発環境での使用を前提としています。本番環境では適切な認証・認可の実装が必要です。
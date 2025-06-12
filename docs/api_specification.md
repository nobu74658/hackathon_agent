# 新人営業マン成長支援AIエージェント API仕様書

## 1. API概要

### 1.1 基本情報
- **ベースURL**: `https://api.sales-growth-ai.com/v1`
- **認証方式**: Bearer Token (JWT)
- **レスポンス形式**: JSON
- **文字エンコーディング**: UTF-8
- **APIバージョン**: v1

### 1.2 共通ヘッダー
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
X-Request-ID: <unique_request_id>
```

### 1.3 共通レスポンス形式

#### 成功レスポンス
```json
{
  "success": true,
  "data": {
    // レスポンスデータ
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

#### エラーレスポンス
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {
      // 詳細情報
    }
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

### 1.4 HTTPステータスコード
| コード | 説明 |
|--------|------|
| 200 | OK - リクエスト成功 |
| 201 | Created - リソース作成成功 |
| 204 | No Content - 処理成功（レスポンスボディなし） |
| 400 | Bad Request - リクエスト不正 |
| 401 | Unauthorized - 認証エラー |
| 403 | Forbidden - アクセス権限なし |
| 404 | Not Found - リソースが見つからない |
| 422 | Unprocessable Entity - バリデーションエラー |
| 429 | Too Many Requests - レート制限超過 |
| 500 | Internal Server Error - サーバーエラー |
| 503 | Service Unavailable - サービス利用不可 |

## 2. 認証API

### 2.1 ログイン
**POST** `/auth/login`

#### リクエスト
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 1800,
    "token_type": "Bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "山田太郎",
      "role": "new_salesperson"
    }
  }
}
```

### 2.2 トークンリフレッシュ
**POST** `/auth/refresh`

#### リクエスト
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 1800
  }
}
```

### 2.3 ログアウト
**POST** `/auth/logout`

#### リクエスト
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "message": "ログアウトしました"
  }
}
```

## 3. ユーザーAPI

### 3.1 ユーザー情報取得
**GET** `/users/me`

#### レスポンス
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "山田太郎",
    "role": "new_salesperson",
    "department": "営業一部",
    "manager": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "鈴木一郎"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### 3.2 ユーザー情報更新
**PUT** `/users/me`

#### リクエスト
```json
{
  "name": "山田太郎",
  "department": "営業二部"
}
```

## 4. 1on1セッションAPI

### 4.1 セッション一覧取得
**GET** `/sessions`

#### クエリパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| page | integer | × | ページ番号（デフォルト: 1） |
| per_page | integer | × | 1ページあたりの件数（デフォルト: 20） |
| status | string | × | ステータスフィルタ |
| from_date | date | × | 開始日 |
| to_date | date | × | 終了日 |

#### レスポンス
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "date": "2024-01-15T10:00:00Z",
        "manager": {
          "id": "660e8400-e29b-41d4-a716-446655440001",
          "name": "鈴木一郎"
        },
        "status": "completed",
        "summary": "顧客コミュニケーション改善について議論",
        "has_action_plan": true
      }
    ],
    "pagination": {
      "current_page": 1,
      "per_page": 20,
      "total_pages": 5,
      "total_items": 100
    }
  }
}
```

### 4.2 セッション作成
**POST** `/sessions`

#### リクエスト
```json
{
  "manager_id": "660e8400-e29b-41d4-a716-446655440001",
  "date": "2024-01-15T10:00:00Z",
  "raw_text": "本日の1on1では、新人の田中さんの最近の営業活動について話しました。\n\n良かった点：\n- 顧客リストの整理が丁寧\n- 報告書の提出が期限通り\n\n改善点：\n- 顧客とのコミュニケーションをもっと積極的に\n- 提案内容の具体性を高める必要がある\n- フォローアップのタイミングを早める"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "id": "880e8400-e29b-41d4-a716-446655440000",
    "status": "created",
    "message": "セッションを作成しました"
  }
}
```

### 4.3 セッション詳細取得
**GET** `/sessions/{session_id}`

#### レスポンス
```json
{
  "success": true,
  "data": {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "manager": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "鈴木一郎"
    },
    "date": "2024-01-15T10:00:00Z",
    "raw_text": "本日の1on1では...",
    "extracted_points": {
      "positive_points": [
        {
          "content": "顧客リストの整理が丁寧",
          "category": "organization"
        },
        {
          "content": "報告書の提出が期限通り",
          "category": "time_management"
        }
      ],
      "improvement_points": [
        {
          "content": "顧客とのコミュニケーションをもっと積極的に",
          "category": "communication",
          "abstraction_level": "high",
          "requires_clarification": true
        },
        {
          "content": "提案内容の具体性を高める必要がある",
          "category": "proposal_skill",
          "abstraction_level": "medium",
          "requires_clarification": true
        }
      ]
    },
    "status": "analyzed",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

## 5. AI対話API

### 5.1 セッション分析開始
**POST** `/ai/analyze`

#### リクエスト
```json
{
  "session_id": "770e8400-e29b-41d4-a716-446655440000"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "analysis_id": "990e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "message": "分析を開始しました"
  }
}
```

### 5.2 対話セッション開始
**POST** `/ai/chat/start`

#### リクエスト
```json
{
  "session_id": "770e8400-e29b-41d4-a716-446655440000",
  "improvement_point_id": "point_001"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "chat_session_id": "aa0e8400-e29b-41d4-a716-446655440000",
    "initial_questions": [
      {
        "question_id": "q001",
        "question": "「顧客とのコミュニケーションをもっと積極的に」という点について、具体的にどのような場面でコミュニケーションに課題を感じていますか？",
        "options": [
          "初回訪問時の会話",
          "提案プレゼンテーション時",
          "メールでのやり取り",
          "電話でのフォローアップ",
          "その他"
        ]
      }
    ]
  }
}
```

### 5.3 対話応答送信
**POST** `/ai/chat/respond`

#### リクエスト
```json
{
  "chat_session_id": "aa0e8400-e29b-41d4-a716-446655440000",
  "question_id": "q001",
  "response": "初回訪問時の会話",
  "additional_info": "特に雑談から本題に入るタイミングが掴めません"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "next_questions": [
      {
        "question_id": "q002",
        "question": "初回訪問時の会話で困っているとのことですが、訪問前にどのような準備をしていますか？",
        "input_type": "text"
      }
    ],
    "progress": {
      "completion_percentage": 40,
      "estimated_questions_remaining": 3
    }
  }
}
```

### 5.4 アクションプラン生成
**POST** `/ai/generate-plan`

#### リクエスト
```json
{
  "chat_session_id": "aa0e8400-e29b-41d4-a716-446655440000"
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "action_plan": {
      "id": "bb0e8400-e29b-41d4-a716-446655440000",
      "summary": "初回訪問時のコミュニケーション改善プラン",
      "actions": [
        {
          "id": "action_001",
          "title": "訪問前準備チェックリストの作成と活用",
          "description": "顧客の業界情報、最近のニュース、担当者の背景などを事前に調査し、話題の引き出しを準備する",
          "category": "preparation",
          "priority": "high",
          "specific_steps": [
            "顧客企業のWebサイトから最新情報を3つピックアップ",
            "業界ニュースを2つ以上確認",
            "担当者のLinkedInプロフィールを確認"
          ],
          "success_metrics": {
            "metric": "準備項目の完了率",
            "target": "100%",
            "measurement_method": "チェックリストの記録"
          },
          "due_date": "2024-01-22",
          "resources": [
            {
              "type": "template",
              "name": "訪問前準備チェックリストテンプレート",
              "url": "/resources/templates/visit-preparation"
            }
          ]
        },
        {
          "id": "action_002",
          "title": "アイスブレイク話題集の作成",
          "description": "汎用的に使える話題を10個用意し、状況に応じて使い分ける",
          "category": "communication",
          "priority": "medium",
          "specific_steps": [
            "季節の話題を3つ準備",
            "業界共通の話題を3つ準備",
            "ビジネストレンドの話題を4つ準備"
          ],
          "success_metrics": {
            "metric": "会話の自然な開始率",
            "target": "80%以上",
            "measurement_method": "訪問後の自己評価"
          },
          "due_date": "2024-01-25"
        }
      ],
      "follow_up_schedule": [
        {
          "date": "2024-01-29",
          "action": "1週間後の振り返り"
        },
        {
          "date": "2024-02-12",
          "action": "実践結果の評価と調整"
        }
      ]
    }
  }
}
```

## 6. アクションプランAPI

### 6.1 アクションプラン一覧取得
**GET** `/plans`

#### クエリパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| status | string | × | pending, in_progress, completed |
| category | string | × | カテゴリフィルタ |

#### レスポンス
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "bb0e8400-e29b-41d4-a716-446655440000",
        "session_id": "770e8400-e29b-41d4-a716-446655440000",
        "title": "初回訪問時のコミュニケーション改善プラン",
        "created_at": "2024-01-15T11:00:00Z",
        "total_actions": 5,
        "completed_actions": 2,
        "progress_percentage": 40
      }
    ]
  }
}
```

### 6.2 アクション更新
**PUT** `/plans/{plan_id}/actions/{action_id}`

#### リクエスト
```json
{
  "status": "completed",
  "completion_note": "チェックリストを作成し、3回の訪問で活用。準備の質が向上した。",
  "actual_result": {
    "metric_value": "100%",
    "achievement": "exceeded"
  }
}
```

#### レスポンス
```json
{
  "success": true,
  "data": {
    "message": "アクションを更新しました",
    "action": {
      "id": "action_001",
      "status": "completed",
      "completed_at": "2024-01-22T15:30:00Z"
    }
  }
}
```

### 6.3 進捗レポート取得
**GET** `/plans/{plan_id}/report`

#### レスポンス
```json
{
  "success": true,
  "data": {
    "plan_id": "bb0e8400-e29b-41d4-a716-446655440000",
    "overall_progress": {
      "percentage": 60,
      "completed_actions": 3,
      "total_actions": 5,
      "on_track": true
    },
    "category_breakdown": [
      {
        "category": "preparation",
        "progress": 100,
        "impact_score": 8.5
      },
      {
        "category": "communication",
        "progress": 40,
        "impact_score": 7.2
      }
    ],
    "timeline": [
      {
        "date": "2024-01-22",
        "event": "アクション「訪問前準備チェックリストの作成と活用」完了",
        "impact": "訪問の質が向上"
      }
    ],
    "recommendations": [
      "現在のペースを維持すれば、予定通り完了見込みです",
      "コミュニケーションカテゴリのアクションに注力しましょう"
    ]
  }
}
```

## 7. レポートAPI

### 7.1 成長サマリー取得
**GET** `/reports/growth-summary`

#### クエリパラメータ
| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| period | string | × | monthly, quarterly, yearly |
| from_date | date | × | 開始日 |
| to_date | date | × | 終了日 |

#### レスポンス
```json
{
  "success": true,
  "data": {
    "period": {
      "from": "2024-01-01",
      "to": "2024-01-31"
    },
    "metrics": {
      "total_sessions": 4,
      "completed_actions": 12,
      "improvement_rate": 75,
      "skill_improvements": [
        {
          "skill": "コミュニケーション",
          "before_score": 3.2,
          "after_score": 4.1,
          "improvement": 28.1
        }
      ]
    },
    "achievements": [
      {
        "date": "2024-01-22",
        "achievement": "初回訪問成功率が50%から75%に向上"
      }
    ],
    "next_focus_areas": [
      "提案スキルの向上",
      "クロージング技術の習得"
    ]
  }
}
```

## 8. Webhook API

### 8.1 Webhook設定
**POST** `/webhooks`

#### リクエスト
```json
{
  "url": "https://example.com/webhook",
  "events": ["session.analyzed", "plan.completed", "action.completed"],
  "secret": "webhook_secret_key"
}
```

### 8.2 Webhookイベント形式
```json
{
  "event": "action.completed",
  "timestamp": "2024-01-22T15:30:00Z",
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "action_id": "action_001",
    "plan_id": "bb0e8400-e29b-41d4-a716-446655440000"
  },
  "signature": "sha256=..."
}
```

## 9. エラーコード一覧

| エラーコード | 説明 | 対処法 |
|-------------|------|--------|
| AUTH_001 | 認証トークンが無効 | 再ログインしてください |
| AUTH_002 | トークンの有効期限切れ | トークンをリフレッシュしてください |
| AUTH_003 | 権限不足 | 管理者に権限付与を依頼してください |
| VAL_001 | 必須パラメータ不足 | リクエストパラメータを確認してください |
| VAL_002 | パラメータ形式エラー | 正しい形式で入力してください |
| AI_001 | AI分析エラー | しばらく待ってから再試行してください |
| AI_002 | LLMサービス利用不可 | サポートに連絡してください |
| RATE_001 | レート制限超過 | 時間を置いてから再試行してください |

## 10. レート制限

| エンドポイント | 制限 | 期間 |
|--------------|------|------|
| 認証API | 10回 | 1分 |
| AI分析API | 100回 | 1時間 |
| その他のAPI | 1000回 | 1時間 |

制限を超えた場合、`429 Too Many Requests`が返され、`X-RateLimit-Reset`ヘッダーにリセット時刻が含まれます。

## 11. SDKサンプル

### JavaScript/TypeScript
```typescript
import { SalesGrowthClient } from '@sales-growth/sdk';

const client = new SalesGrowthClient({
  apiKey: 'your_api_key',
  baseUrl: 'https://api.sales-growth-ai.com/v1'
});

// セッション作成
const session = await client.sessions.create({
  managerId: 'manager_id',
  date: new Date(),
  rawText: '1on1の内容...'
});

// AI分析開始
const analysis = await client.ai.analyze({
  sessionId: session.id
});

// 対話開始
const chat = await client.ai.startChat({
  sessionId: session.id,
  improvementPointId: 'point_001'
});
```

### Python
```python
from sales_growth_sdk import SalesGrowthClient

client = SalesGrowthClient(
    api_key='your_api_key',
    base_url='https://api.sales-growth-ai.com/v1'
)

# セッション作成
session = client.sessions.create(
    manager_id='manager_id',
    date=datetime.now(),
    raw_text='1on1の内容...'
)

# AI分析開始
analysis = client.ai.analyze(session_id=session.id)

# 対話開始
chat = client.ai.start_chat(
    session_id=session.id,
    improvement_point_id='point_001'
)
```
# 改善されたAPI仕様書

## 概要

このドキュメントは、改善されたSales Growth AI Agentの新しいAPIエンドポイントについて説明します。主な改善点は以下の通りです：

1. **知識ベースの統合** - 社内ナレッジ（会社のミッション・ビジョン・バリュー、先輩の成功事例など）を活用
2. **自己解決機能** - AIが社内ナレッジを参照して自動的に質問を解決し、ユーザーの負荷を軽減
3. **具体的なテンプレート生成** - アクションプランに具体的な実行テンプレートを含める

## 新しいエンドポイント

### 1. 改善されたセッション管理

#### POST /enhanced/start
改善された対話セッションを開始します。

**リクエスト:**
```json
{
  "user_name": "田中太郎",
  "department": "営業部",
  "experience_years": 1,
  "initial_topic": "営業スキル向上",
  "specific_challenge": "プレゼンで緊張する"  // オプション
}
```

**レスポンス:**
```json
{
  "session_id": "uuid-string",
  "questions": ["質問1", "質問2"],
  "reasoning": "これらの質問が必要な理由",
  "self_resolved_insights": [
    {
      "insight": "社内ナレッジから得られた洞察",
      "source": "knowledge_base_category"
    }
  ],
  "suggested_resources": ["推奨リソース1", "推奨リソース2"],
  "completeness_score": 30,
  "knowledge_used": true
}
```

#### POST /enhanced/message
メッセージを送信し、知識ベースを活用した応答を取得します。

**リクエスト:**
```json
{
  "session_id": "uuid-string",
  "message": "ユーザーのメッセージ"
}
```

**レスポンス（フォローアップの場合）:**
```json
{
  "type": "follow_up",
  "questions": ["追加質問1", "追加質問2"],
  "self_resolved": [
    {
      "question": "自己解決された質問",
      "answer": "知識ベースからの回答",
      "source": "情報源"
    }
  ],
  "completeness_score": 60,
  "confidence": "high"
}
```

**レスポンス（アクションプランの場合）:**
```json
{
  "type": "action_plan",
  "action_plan": {
    "action_items": [
      {
        "id": "action_1",
        "title": "アクション名",
        "description": "詳細説明",
        "priority": "high",
        "duration": "1週間",
        "due_date": "2024-02-15",
        "deliverables": ["成果物1", "成果物2"],
        "success_criteria": "成功基準",
        "template_reference": "email_campaign"
      }
    ],
    "templates_provided": [
      {
        "category": "新規開拓",
        "name": "email_campaign",
        "title": "メールアプローチキャンペーン"
      }
    ],
    "summary": "アクションプランの要約",
    "key_improvements": ["改善点1", "改善点2"],
    "metrics": {
      "success_indicator": "成功指標"
    },
    "knowledge_references": [
      {
        "type": "課題タイプ",
        "content": {
          "solution": "解決策の詳細"
        }
      }
    ],
    "mentor_suggestions": [
      "先輩からのアドバイス1",
      "先輩からのアドバイス2"
    ]
  },
  "completeness_score": 85,
  "templates_provided": [...],
  "knowledge_references": [...]
}
```

### 2. 知識ベースAPI

#### POST /enhanced/knowledge/search
知識ベースを検索します。

**リクエスト:**
```json
{
  "query": "検索クエリ",
  "category": "sales_best_practices"  // オプション
}
```

**レスポンス:**
```json
{
  "query": "検索クエリ",
  "results": [
    {
      "category": "カテゴリ名",
      "type": "結果タイプ",
      "content": "内容",
      "relevance_score": 0.95
    }
  ],
  "count": 5
}
```

#### GET /enhanced/knowledge/company-values
会社のミッション・ビジョン・バリューを取得します。

**レスポンス:**
```json
{
  "mission": "会社のミッション",
  "vision": "会社のビジョン",
  "values": [
    "価値観1",
    "価値観2"
  ]
}
```

### 3. テンプレートAPI

#### GET /enhanced/templates/list
利用可能なアクションテンプレートの一覧を取得します。

**レスポンス:**
```json
{
  "templates": {
    "新規開拓": [
      {
        "name": "email_campaign",
        "title": "メールアプローチキャンペーン",
        "description": "体系的なメールアプローチで新規顧客を開拓"
      }
    ],
    "プレゼンテーション改善": [...]
  }
}
```

#### GET /enhanced/templates/{category}/{template_name}
特定のテンプレートの詳細を取得します。

**レスポンス:**
```json
{
  "category": "新規開拓",
  "name": "email_campaign",
  "template": {
    "title": "メールアプローチキャンペーン",
    "description": "説明",
    "steps": [
      {
        "step": 1,
        "action": "ターゲットリスト作成",
        "details": "詳細な手順",
        "deliverable": "成果物",
        "duration": "2日",
        "success_criteria": "成功基準"
      }
    ],
    "tools_required": ["CRM", "メール配信ツール"],
    "expected_outcome": "期待される成果"
  }
}
```

### 4. セッション洞察API

#### GET /enhanced/session/{session_id}/insights
セッションから得られた洞察を取得します。

**レスポンス:**
```json
{
  "session_id": "uuid-string",
  "user_profile": {
    "name": "田中太郎",
    "department": "営業部",
    "experience_years": 1
  },
  "identified_challenges": ["課題1", "課題2"],
  "self_resolved_count": 5,
  "knowledge_references_used": 8,
  "conversation_efficiency": {
    "total_messages": 6,
    "questions_asked": 10,
    "questions_self_resolved": 5
  }
}
```

### 5. デモシナリオAPI

#### GET /enhanced/demo/scenario/{scenario}
事前定義されたシナリオを実行します。

利用可能なシナリオ:
- `nervous_presentation` - プレゼンでの緊張克服
- `new_customer_acquisition` - 新規顧客開拓

**レスポンス:**
```json
{
  "scenario": "nervous_presentation",
  "session_id": "uuid-string",
  "interactions": [
    {
      "message": "ユーザーメッセージ",
      "response": {
        "type": "follow_up",
        "questions": [...],
        "self_resolved": [...]
      }
    }
  ]
}
```

## 主な改善点の詳細

### 1. 質問の負荷軽減
- 従来: すべての情報をユーザーに質問
- 改善版: 知識ベースから自動的に情報を取得し、必要最小限の質問のみ

### 2. 具体的なアクションテンプレート
- 従来: 抽象的なアクションプラン（例：「資料を改善する」）
- 改善版: 具体的なテンプレート付き（例：メール文面テンプレート、チェックリスト）

### 3. 社内ナレッジの活用
- 会社のミッション・ビジョン・バリューに基づいたアドバイス
- 先輩の成功事例を参考にした具体的な提案
- よくある課題に対する検証済みの解決策

## 使用例

### 基本的な対話フロー

```python
# 1. セッション開始
response = await client.post("/enhanced/start", json={
    "user_name": "新人営業",
    "specific_challenge": "緊張で頭が真っ白になる"
})

# 2. 自己解決された情報の確認
print(f"自己解決された洞察: {response['self_resolved_insights']}")

# 3. 必要最小限の質問に回答
await client.post("/enhanced/message", json={
    "session_id": session_id,
    "message": "明日重要なプレゼンがあります"
})

# 4. 具体的なテンプレート付きアクションプラン受領
```

### 知識ベース検索

```python
# 特定の課題に対する解決策を検索
response = await client.post("/enhanced/knowledge/search", json={
    "query": "プレゼン 緊張",
    "category": "common_challenges"
})
```

## エラーハンドリング

すべてのエンドポイントは以下の形式でエラーを返します：

```json
{
  "detail": "エラーの詳細説明"
}
```

一般的なエラーコード：
- `404`: セッションまたはリソースが見つからない
- `500`: サーバー内部エラー
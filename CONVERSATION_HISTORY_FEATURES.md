# 会話履歴機能

## 概要

AIエージェントがユーザーとの過去の会話ログを活用して、より効果的でパーソナライズされた対話を実現する機能です。

## 主な機能

### 1. 会話履歴の記録と管理

- すべての対話セッションを自動的に記録
- ユーザーごとの会話履歴を長期保存
- セッションごとのコンテキストと成果を追跡

### 2. 洞察の抽出と保存

- **課題の識別**: 繰り返し出現する問題や困難を自動検出
- **強みの発見**: ユーザーの得意分野や成功パターンを認識
- **学習スタイルの把握**: 好む学習方法（視覚的、実践的など）を特定
- **行動パターンの分析**: 回答傾向や進捗速度を理解

### 3. ユーザープロファイルの構築

各ユーザーに対して以下の情報を集約：

```python
{
    "user_id": "user_123",
    "common_challenges": ["プレゼン時の緊張", "新規開拓"],
    "strengths": ["製品知識", "顧客フォロー"],
    "improvement_areas": ["クロージング", "価格交渉"],
    "preferred_learning_style": "practical",
    "total_sessions": 10,
    "completed_actions": 25,
    "success_rate": 0.75
}
```

### 4. パーソナライズされた対話

- **質問の最適化**: 過去に回答済みの内容は再度聞かない
- **的確な提案**: ユーザーの傾向に合わせたアドバイス
- **継続的な支援**: 前回からの進捗を踏まえた内容

## 技術的実装

### データモデル

```python
# 会話セッション
class DialogueSession:
    - id: セッションID
    - user_id: ユーザーID
    - status: ステータス（active/completed/archived）
    - created_at: 作成日時
    - messages: メッセージリスト
    - insights: 抽出された洞察

# 会話洞察
class ConversationInsight:
    - session_id: セッションID
    - user_id: ユーザーID
    - insight_type: 洞察タイプ（challenge/strength/preference）
    - content: 内容
    - confidence_score: 確信度（0.0-1.0）

# ユーザープロファイル
class UserProfile:
    - user_id: ユーザーID
    - common_challenges: よくある課題
    - strengths: 強み
    - improvement_areas: 改善領域
    - preferred_learning_style: 学習スタイル
```

### サービス層

- **ConversationHistoryService**: 会話履歴の管理と分析
- **EnhancedDialogueManager**: 履歴を活用した対話管理
- **InsightExtractor**: 会話から洞察を抽出

## 使用例

### 初回セッション
```
ユーザー: プレゼンで緊張してしまいます
AI: 緊張は自然な反応です。具体的にどのような場面で緊張しますか？
（通常の質問を実施）
```

### 2回目以降のセッション
```
ユーザー: 来週大事なプレゼンがあります
AI: 前回お伝えした深呼吸法は効果がありましたか？
    今回は技術的な質問への準備も重要そうですね。
（過去の履歴を踏まえた、より的確な質問）
```

## 効果

### 1. 質問数の削減
- 初回: 5-7個の質問
- 2回目以降: 2-3個の質問（**60-70%削減**）

### 2. 対話の質の向上
- ユーザーの成長を認識
- 継続的な改善をサポート
- 個別最適化された提案

### 3. ユーザー満足度の向上
- 「覚えていてくれる」安心感
- 無駄な繰り返しがない
- 自分に合った学習方法

## API エンドポイント

### 会話履歴取得
```
GET /enhanced/user/{user_id}/history
```

### ユーザー洞察取得
```
GET /enhanced/user/{user_id}/insights
```

### セッションサマリー作成
```
POST /enhanced/session/{session_id}/summary
```

## テスト方法

### 1. 単体テスト
```bash
cd backend
python test_conversation_history.py
```

### 2. 統合デモ
```bash
python enhanced_demo_with_history.py
```

### 3. API経由のテスト
```bash
# サーバー起動
uvicorn app.main:app --reload

# 別ターミナルでテスト実行
python test_conversation_history.py
```

## 今後の拡張可能性

1. **機械学習による改善**
   - より高度なパターン認識
   - 成功予測モデルの構築

2. **チーム全体の学習**
   - 組織全体の傾向分析
   - ベストプラクティスの共有

3. **外部システム連携**
   - CRMとの統合
   - 成果測定との連動
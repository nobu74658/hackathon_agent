# 理想的な対話ワークフロー - 実装ガイド

## 概要

このドキュメントは、`IDEAL_DIALOGUE_SCENARIO.md`に記載された理想的な対話シナリオの実装について説明します。

## アーキテクチャ

### コアコンポーネント

1. **IdealDialogueWorkflow** (`app/services/ideal_dialogue_workflow.py`)
   - 対話フローの中心的な実装
   - ソクラテス式質問法の実装
   - 段階的な対話状態管理

2. **API エンドポイント** (`app/api/ideal_dialogue_endpoints.py`)
   - RESTful APIインターフェース
   - セッション管理
   - 進捗追跡

3. **デモンストレーション**
   - `demo_ideal_scenario.py` - シナリオ完全再現
   - `ideal_interactive_demo.py` - インタラクティブ体験
   - `test_ideal_workflow.py` - ワークフローテスト

## 対話フェーズ

### 1. Greeting（挨拶）
- 温かく共感的な導入
- 上司の指示の確認
- 協力的な雰囲気作り

### 2. Current Situation（現状把握）
- 売上状況の確認
- 時間配分の把握
- 上司の指示への理解度確認

### 3. Problem Analysis（課題分析）
- 成功体験の発見
- 成功要因の分析
- 成功パターンの抽出

### 4. Solution Exploration（ソリューション探索）
- 顧客セグメンテーション
- 優先順位付け
- 戦略的アプローチの設計

### 5. Action Plan（アクションプラン）
- SMART目標の設定
- 測定可能な指標の決定
- 短期・中期目標の設定

### 6. Execution Support（実行支援）
- 障害の予測と対策
- 継続の仕組み作り
- 進捗確認方法の設定

## 主要な機能

### 1. 回答分析（ResponseAnalysis）
```python
- key_points: 重要ポイントの抽出
- emotional_state: 感情状態の把握
- understanding_level: 理解度の評価
- success_patterns: 成功パターンの発見
- challenges: 課題の特定
```

### 2. ソクラテス式質問生成
```python
- question: 部下の気づきを促す質問
- purpose: 質問の目的
- expected_outcome: 期待される成果
- follow_up_options: フォローアップの選択肢
```

### 3. アクションプラン生成
```python
- short_term_goals: 1ヶ月の目標
- mid_term_goals: 3ヶ月の目標
- success_patterns: 活用すべきパターン
- challenges_and_solutions: 課題と解決策
- progress_check: 進捗確認方法
```

## 使用方法

### 1. APIサーバーの起動
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. デモの実行

#### シナリオ完全再現
```bash
python demo_ideal_scenario.py
```

#### インタラクティブ体験
```bash
python ideal_interactive_demo.py
```

#### ワークフローテスト
```bash
python test_ideal_workflow.py
```

### 3. API利用例

#### セッション開始
```bash
curl -X POST http://localhost:8000/api/ideal-dialogue/start \
  -H "Content-Type: application/json" \
  -d '{
    "abstract_instruction": "もっと顧客との関係を深めて売上を伸ばしてほしい",
    "user_context": {
      "name": "田中",
      "role": "新人営業担当",
      "experience": "6ヶ月"
    }
  }'
```

#### 回答送信
```bash
curl -X POST http://localhost:8000/api/ideal-dialogue/respond \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "ideal_xxxxxx",
    "user_response": "今月も目標の85%でした..."
  }'
```

## 特徴

### 1. ソクラテス式質問法
- 答えを直接教えない
- 部下自身の気づきを促す
- 段階的な深掘り
- 共感的な姿勢

### 2. 成功体験の活用
- 既存の成功パターンを発見
- 成功要因の分析
- 他の状況への応用

### 3. SMART目標設定
- Specific（具体的）
- Measurable（測定可能）
- Achievable（達成可能）
- Relevant（関連性）
- Time-bound（期限付き）

### 4. 継続的な成長支援
- 進捗確認の仕組み
- 障害の予測と対策
- 自律的な問題解決能力の育成

## 期待される成果

### 短期的成果（1-3ヶ月）
- 具体的なアクションプランの作成
- 顧客関係の改善
- 売上の向上

### 長期的成果（3-12ヶ月）
- 自律的な問題解決能力
- 抽象→具体の変換スキル
- 継続的な成長習慣

## トラブルシューティング

### OpenAI APIエラー
```bash
export OPENAI_API_KEY="your-api-key"
```

### セッションが見つからない
- セッションは一時的なメモリに保存されます
- サーバー再起動でリセットされます

### 質問生成が遅い
- APIレスポンス時間は通常2-5秒
- タイムアウトは30秒に設定

## 今後の拡張

1. **永続化**
   - Redis/PostgreSQLでのセッション管理
   - 対話履歴の長期保存

2. **分析機能**
   - 対話パターンの分析
   - 成功率の測定
   - 改善提案の自動生成

3. **カスタマイズ**
   - 業界別テンプレート
   - 役職別アプローチ
   - 多言語対応

4. **統合**
   - Slack以外のチャットツール
   - CRMシステム連携
   - レポート自動生成
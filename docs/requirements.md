# 新人営業マン成長支援AIエージェント 要件定義書

## 1. プロジェクト概要

### 1.1 背景
新人営業マンの教育において、上司との1on1ミーティングで挙げられる改善点が抽象的であるため、具体的な行動につながらず、成長を実感できないという課題が存在する。

### 1.2 目的
- 新人営業マンの営業成績向上を支援する
- ビジネススキルの具体的な改善を促進する
- 1on1ミーティングの効果を最大化する

### 1.3 スコープ
- 1on1ミーティング資料の解析と具体化
- AIエージェントによる対話型情報補完
- 具体的なアクションプランの生成と追跡

## 2. システム要件

### 2.1 機能要件

#### 2.1.1 1on1資料解析機能
- **入力形式**: テキストデータ（議事録、フィードバック）
- **処理内容**:
  - 改善点の自動抽出
  - カテゴリ分類（営業スキル、コミュニケーション、業務知識等）
  - 抽象度レベルの判定

#### 2.1.2 対話型情報補完機能
- **目的**: 抽象的な改善点を具体化するための情報収集
- **機能詳細**:
  - コンテキストに基づく質問自動生成
  - 回答の妥当性検証
  - 追加質問の動的生成
  - 対話履歴の管理

#### 2.1.3 アクションプラン生成機能
- **SMART目標への変換**:
  - Specific（具体的）
  - Measurable（測定可能）
  - Achievable（達成可能）
  - Relevant（関連性）
  - Time-bound（期限設定）
- **出力内容**:
  - 優先順位付きタスクリスト
  - 推奨実施スケジュール
  - 成功指標の定義

#### 2.1.4 進捗管理・分析機能
- **データ管理**:
  - 1on1履歴の保存
  - アクションプランの実施状況追跡
  - 成長指標の記録
- **分析機能**:
  - 改善傾向の可視化
  - パターン認識
  - 成功要因の抽出

### 2.2 非機能要件

#### 2.2.1 パフォーマンス要件
- レスポンスタイム: 3秒以内（95%タイル）
- 同時接続数: 1,000ユーザー
- データ処理能力: 10,000文字/リクエスト

#### 2.2.2 セキュリティ要件
- データ暗号化: AES-256
- 認証方式: OAuth 2.0 / SAML
- アクセス制御: ロールベース（本人、上司、管理者）
- 監査ログ: 全操作の記録

#### 2.2.3 可用性要件
- SLA: 99.5%
- バックアップ: 日次自動バックアップ
- 災害復旧: RPO 24時間、RTO 4時間

## 3. システムアーキテクチャ

### 3.1 技術スタック
- **フロントエンド**: React 18 + Next.js 14
- **バックエンド**: Python 3.11 + FastAPI
- **LLMインテグレーション**: OpenAI GPT-4 / Anthropic Claude 3
- **データベース**: 
  - PostgreSQL 15（構造化データ）
  - Pinecone（ベクトルデータベース）
- **キャッシュ**: Redis 7
- **メッセージキュー**: RabbitMQ
- **インフラ**: AWS（ECS, RDS, S3, CloudFront）

### 3.2 システム構成図
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Web UI    │────▶│   API GW    │────▶│  Backend    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │     LLM     │
                                        └─────────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    ▼                          ▼                          ▼
             ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
             │ PostgreSQL  │          │  Vector DB  │          │    Redis    │
             └─────────────┘          └─────────────┘          └─────────────┘
```

## 4. データモデル

### 4.1 主要エンティティ

#### User（ユーザー）
```json
{
  "user_id": "string",
  "name": "string",
  "email": "string",
  "role": "enum(new_salesperson, manager, admin)",
  "department": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

#### OneOnOneSession（1on1セッション）
```json
{
  "session_id": "string",
  "user_id": "string",
  "manager_id": "string",
  "date": "datetime",
  "raw_text": "text",
  "extracted_points": "json",
  "status": "enum(draft, analyzed, completed)",
  "created_at": "datetime"
}
```

#### ActionPlan（アクションプラン）
```json
{
  "plan_id": "string",
  "session_id": "string",
  "user_id": "string",
  "actions": [
    {
      "action_id": "string",
      "description": "string",
      "category": "string",
      "priority": "enum(high, medium, low)",
      "due_date": "date",
      "status": "enum(pending, in_progress, completed)",
      "metrics": "json"
    }
  ],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

## 5. 画面設計

### 5.1 主要画面一覧
1. ログイン画面
2. ダッシュボード
3. 1on1入力画面
4. AI対話画面
5. アクションプラン画面
6. 進捗レポート画面
7. 設定画面

### 5.2 画面遷移図
```
ログイン ──▶ ダッシュボード ──┬──▶ 1on1入力 ──▶ AI対話 ──▶ アクションプラン
                          │
                          ├──▶ 進捗レポート
                          │
                          └──▶ 設定
```

## 6. API設計

### 6.1 主要エンドポイント

#### 認証関連
- `POST /api/auth/login` - ログイン
- `POST /api/auth/logout` - ログアウト
- `POST /api/auth/refresh` - トークンリフレッシュ

#### 1on1セッション関連
- `GET /api/sessions` - セッション一覧取得
- `POST /api/sessions` - 新規セッション作成
- `GET /api/sessions/{id}` - セッション詳細取得
- `PUT /api/sessions/{id}` - セッション更新

#### AI対話関連
- `POST /api/ai/analyze` - 1on1資料解析
- `POST /api/ai/chat` - 対話セッション
- `GET /api/ai/suggestions` - 改善提案取得

#### アクションプラン関連
- `GET /api/plans` - プラン一覧取得
- `POST /api/plans` - プラン作成
- `PUT /api/plans/{id}/actions/{action_id}` - アクション更新

## 7. 開発計画

### 7.1 フェーズ分け
- **フェーズ1（MVP）**: 基本的な1on1解析と対話機能（3ヶ月）
- **フェーズ2**: アクションプラン管理機能（2ヶ月）
- **フェーズ3**: 分析・レポート機能（2ヶ月）
- **フェーズ4**: 外部連携・拡張機能（3ヶ月）

### 7.2 マイルストーン
1. 要件定義完了（2週間）
2. 基本設計完了（3週間）
3. MVP開発完了（8週間）
4. テスト完了（3週間）
5. 本番リリース（1週間）

## 8. 運用・保守

### 8.1 監視項目
- システム稼働率
- レスポンスタイム
- エラー率
- リソース使用率

### 8.2 メンテナンス計画
- 定期メンテナンス: 月1回（第3日曜日 深夜）
- セキュリティパッチ: 随時適用
- バックアップ: 日次自動実行

## 9. 制約事項・前提条件

### 9.1 制約事項
- 個人情報保護法への準拠
- 1on1データの保存期間は最大2年
- LLM APIの利用制限内での運用

### 9.2 前提条件
- ユーザーは基本的なPC操作ができる
- 1on1資料はテキスト形式で提供される
- インターネット接続環境がある

## 10. リスクと対策

| リスク | 影響度 | 発生確率 | 対策 |
|-------|--------|----------|------|
| LLM APIの障害 | 高 | 中 | 複数プロバイダーの利用、フォールバック機能 |
| データ漏洩 | 高 | 低 | 暗号化、アクセス制御、監査ログ |
| ユーザー採用の遅れ | 中 | 中 | UI/UXの改善、トレーニング提供 |
| スケーラビリティ問題 | 中 | 低 | 負荷テスト実施、自動スケーリング設定 |
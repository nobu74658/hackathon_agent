# AI営業支援エージェント - 強化版Slack統合ガイド

## 概要

強化版Slack統合は、従来のチャットボット機能に加えて、以下の高度な機能を提供します：

- **会話履歴の永続化と学習**: 過去の対話から学習し、パーソナライズされた支援を提供
- **社内ナレッジベースの活用**: ベストプラクティスや成功事例を即座に参照
- **ユーザープロファイリング**: 個人の成長履歴、課題、強みを記録・分析
- **テンプレート提案**: 過去の成功パターンに基づく行動計画の自動提案

## セットアップ手順

### 1. 前提条件

- Python 3.8以上
- PostgreSQL（データベース）
- Redis（セッション管理）
- Slack Workspace管理者権限

### 2. 環境変数の設定

`.env`ファイルに以下の環境変数を設定してください：

```bash
# Slack設定（必須）
SLACK_BOT_TOKEN=xoxb-your-bot-token        # Bot User OAuth Token
SLACK_SIGNING_SECRET=your-signing-secret    # Signing Secret
SLACK_APP_TOKEN=xapp-your-app-token        # App-Level Token (Socket Mode用)

# LLM設定（いずれか必須）
OPENAI_API_KEY=your-openai-key            # OpenAI使用時
ANTHROPIC_API_KEY=your-anthropic-key      # Anthropic使用時

# データベース設定
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/salesai_db

# Redis設定
REDIS_URL=redis://localhost:6379/0

# その他の設定
USE_MOCK_LLM=false                         # テスト時はtrueに設定
LOG_LEVEL=INFO
```

### 3. Slackアプリの設定

#### 3.1 アプリの作成

1. [Slack API](https://api.slack.com/apps)にアクセス
2. 「Create New App」→「From scratch」を選択
3. アプリ名：「AI営業支援エージェント」
4. ワークスペースを選択

#### 3.2 OAuth & Permissions

**Bot Token Scopes**に以下を追加：

- `app_mentions:read` - メンション読み取り
- `channels:history` - チャンネル履歴読み取り
- `channels:read` - チャンネル情報読み取り
- `chat:write` - メッセージ送信
- `commands` - スラッシュコマンド
- `groups:history` - プライベートチャンネル履歴
- `groups:read` - プライベートチャンネル情報
- `im:history` - DM履歴読み取り
- `im:read` - DM情報読み取り
- `im:write` - DM送信
- `users:read` - ユーザー情報読み取り

#### 3.3 Event Subscriptions

**Request URL**: `https://your-domain.com/api/v1/slack/events`

**Subscribe to bot events**:
- `app_mention` - アプリへのメンション
- `message.im` - ダイレクトメッセージ

#### 3.4 Slash Commands

以下のコマンドを追加：

| コマンド | Request URL | 説明 |
|---------|------------|------|
| `/ai_help` | `https://your-domain.com/api/v1/slack/commands` | ヘルプ表示 |
| `/ai_knowledge` | `https://your-domain.com/api/v1/slack/commands` | ナレッジ検索 |
| `/ai_history` | `https://your-domain.com/api/v1/slack/commands` | 成長履歴表示 |

### 4. アプリケーションの起動

```bash
# 依存関係のインストール
cd backend
uv pip install -e ".[dev]"

# データベースマイグレーション
alembic upgrade head

# ナレッジベースの初期データ投入（オプション）
python scripts/seed_knowledge_base.py

# アプリケーション起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. エンドポイントの更新

`app/api/slack_endpoints.py`を編集して、強化版サービスを使用するように変更：

```python
# 既存のインポートを置き換え
from app.services.enhanced_slack_service import get_enhanced_slack_service

# エンドポイントの更新
slack_service = get_enhanced_slack_service()
```

## 使用方法

### 基本的な対話

#### 1. ダイレクトメッセージ（DM）

AI営業支援エージェントとのDMで直接対話できます：

```
あなた: こんにちは。新規開拓の営業で苦戦しています。
AI: 新規開拓での課題について詳しくお聞かせください。

📊 情報収集進捗: 15%
👤 お帰りなさい！前回から3日ぶりですね。
💡 過去の課題を考慮して質問を調整しました。

以下の点について詳しく教えてください：
1. どのような業界・規模の企業をターゲットにしていますか？
2. 現在のアプローチ方法（電話、メール、訪問等）と成功率はどの程度ですか？
3. 最も困難を感じている具体的な場面はどこですか？
```

#### 2. チャンネルでのメンション

```
あなた: @AI営業支援 プレゼンの構成について相談したい
AI: プレゼンテーション構成のご相談ですね。

📚 社内ナレッジを参考にしています。

以下の点について詳しく教えてください：
1. プレゼンの目的と対象者（役職・人数等）を教えてください
2. 持ち時間と期待される成果は何ですか？
3. 過去に類似のプレゼンで成功/失敗した経験はありますか？
```

### スラッシュコマンド

#### `/ai_help` - ヘルプ表示

```
/ai_help

🤖 AI営業支援エージェント - Slackコマンド一覧

基本的な使い方:
• DMで直接メッセージを送信
• チャンネルで @AI営業支援 をメンション

コマンド:
• /ai_help - このヘルプを表示
• /ai_knowledge キーワード - 社内ナレッジを検索
• /ai_history - あなたの成長履歴を表示
```

#### `/ai_knowledge` - ナレッジ検索

```
/ai_knowledge クロージング

📚 ナレッジベース検索結果

1. 効果的なクロージング技法
   カテゴリ: 営業スキル
   関連度: 95%
   クロージングは営業プロセスの最終段階で、顧客に決断を促す重要なステップです...

2. クロージング時のよくある失敗パターン
   カテゴリ: 注意点
   関連度: 88%
   急ぎすぎるクロージングは顧客の不信感を招きます。適切なタイミングを...
```

#### `/ai_history` - 成長履歴表示

```
/ai_history

📊 あなたの成長履歴

セッション数: 12回
完了アクション: 28件
成功率: 78%

💪 取り組んでいる課題
• 新規開拓のアプローチ方法
• プレゼンテーション時の緊張対策
• 顧客ニーズの深掘り

✨ あなたの強み
• 製品知識の深さ
• 顧客フォローの丁寧さ
• 資料作成スキル

🔍 最近の洞察
• [challenge] 初回訪問での関係構築に課題がある
• [strength] 技術的な質問への対応力が高い
• [preference] 実践的なロールプレイを通じた学習を好む
```

### アクションプラン生成

十分な情報が収集されると、パーソナライズされたアクションプランが生成されます：

```
🎯 営業成長アクションプラン (完了度: 85%)
📈 あなたの過去の成功率: 78%

📝 概要
12回の対話から、新規開拓とプレゼンスキル向上のための実践的なプランを作成しました。

📋 推奨テンプレート
• 新規開拓アプローチテンプレート (成功率: 82%)
• 役員向けプレゼン構成テンプレート (成功率: 75%)

📋 具体的アクション
🔴 初回アプローチの改善
   └ メールテンプレートを3パターン作成し、A/Bテストを実施
   📅 期限: 2024-02-15

🟡 プレゼン練習の習慣化
   └ 週1回、同僚とロールプレイを実施し、フィードバックを記録
   📅 期限: 2024-02-29

💬 /ai_history で過去の会話履歴と洞察を確認できます。
```

## 活用例

### 1. 継続的な成長支援

定期的な1on1の内容をAIに相談することで、長期的な成長をサポート：

- 毎週の1on1後に要点を共有
- AIが進捗を追跡し、次のステップを提案
- 成功パターンを学習し、類似状況で活用

### 2. 緊急時の相談

重要商談前の準備など、即座のアドバイスが必要な場合：

- 状況を簡潔に説明
- 過去の類似ケースから最適な対策を提案
- 社内のベストプラクティスを即座に参照

### 3. チーム全体の底上げ

- 共通の課題をナレッジベース化
- 成功事例をチーム内で共有
- 新人の早期戦力化を支援

## トラブルシューティング

### よくある問題と解決方法

#### 1. ボットが応答しない

- **原因**: 権限設定の不足
- **解決**: OAuth & Permissionsで必要な権限を確認

#### 2. コマンドが認識されない

- **原因**: Request URLの設定ミス
- **解決**: Slash CommandsのURLが正しいか確認

#### 3. 履歴が保存されない

- **原因**: データベース接続エラー
- **解決**: DATABASE_URLと接続を確認

#### 4. 「考えています...」で止まる

- **原因**: LLM APIのタイムアウト
- **解決**: APIキーの確認、ネットワーク接続の確認

### ログの確認

```bash
# アプリケーションログ
tail -f logs/app.log

# Slackイベントログ
tail -f logs/slack_events.log

# エラーログのみ
grep ERROR logs/app.log
```

## セキュリティとプライバシー

### データの取り扱い

- **会話データ**: PostgreSQLに暗号化して保存
- **セッション情報**: Redis（24時間で自動削除）
- **個人情報**: ユーザーIDのみ保存（実名は保存しない）

### アクセス制御

- Slack認証によるユーザー識別
- 各ユーザーは自分のデータのみアクセス可能
- 管理者機能は別途権限管理

## パフォーマンス最適化

### 推奨設定

- **並行処理**: 最大10セッション
- **タイムアウト**: 30秒
- **キャッシュ**: ナレッジ検索結果を5分間キャッシュ

### スケーリング

大規模利用時の推奨構成：

- FastAPIワーカー: 4プロセス
- Redis: 専用インスタンス
- PostgreSQL: Read Replicaの活用
- LLM API: レート制限に注意

## 今後の拡張予定

- 音声入力対応
- 多言語サポート（英語・中国語）
- 外部CRMとの連携
- より高度な分析ダッシュボード

## サポート

質問や問題がある場合は、以下までお問い合わせください：

- 社内Slackチャンネル: #ai-sales-support
- メール: ai-support@company.com
- ドキュメント: https://internal-docs.company.com/ai-sales-agent
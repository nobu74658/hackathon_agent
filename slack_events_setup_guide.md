# Slack Events API設定ガイド

このガイドでは、Sales Growth AI AgentのSlack統合でEvents APIサブスクリプションを設定する方法を詳しく説明します。

## 概要

Events APIを使用することで、Slackワークスペースで発生するイベント（メッセージ、チャンネル参加など）をリアルタイムで受信し、AI Agentが適切に応答できるようになります。

## 前提条件

1. Slack App が作成済みであること
2. 必要な権限（スコープ）が設定済みであること
3. FastAPIサーバーが動作していること

## ステップ1: Request URLの設定

### 1.1 エンドポイントの準備

まず、Slackからのイベントを受信するためのエンドポイントが必要です：

```python
# app/api/slack_endpoints.py
from fastapi import APIRouter, Request, HTTPException
import json

router = APIRouter()

@router.post("/slack/events")
async def handle_slack_events(request: Request):
    """Slack Events APIからのイベントを処理"""
    body = await request.body()
    
    # URL verification challenge
    if request.headers.get("content-type") == "application/json":
        data = json.loads(body)
        if data.get("type") == "url_verification":
            return {"challenge": data["challenge"]}
    
    # 実際のイベント処理
    # ... イベント処理ロジック
    
    return {"status": "ok"}
```

### 1.2 ngrokでローカル開発用URL作成

ローカル開発環境では、ngrokを使用してSlackがアクセス可能なURLを作成：

```bash
# ngrokのインストール（まだの場合）
brew install ngrok

# FastAPIサーバーを起動
uvicorn app.main:app --reload --port 8000

# 別のターミナルでngrokを起動
ngrok http 8000
```

ngrokが表示するHTTPS URLをメモしておきます（例：`https://abc123.ngrok.io`）

## ステップ2: Slack App設定

### 2.1 Event Subscriptionsの有効化

1. [Slack API](https://api.slack.com/apps)にアクセス
2. 対象のSlack Appを選択
3. 左サイドバーから **「Event Subscriptions」** をクリック
4. **「Enable Events」** をオンに切り替え

### 2.2 Request URLの設定

1. **Request URL** フィールドに以下を入力：
   ```
   https://abc123.ngrok.io/slack/events
   ```
   （`abc123.ngrok.io`は実際のngrok URLに置き換え）

2. **「Verify」** をクリック
3. 緑色のチェックマークが表示されれば成功

### 2.3 Bot Eventsの購読設定

**「Subscribe to bot events」** セクションで、必要なイベントを追加：

#### 基本的なメッセージング
- `message.channels` - パブリックチャンネルでのメッセージ
- `message.groups` - プライベートチャンネルでのメッセージ  
- `message.im` - ダイレクトメッセージ
- `app_mention` - アプリへのメンション

#### ユーザー管理
- `team_join` - 新しいユーザーの参加
- `user_change` - ユーザー情報の変更

#### チャンネル管理
- `channel_created` - チャンネル作成
- `member_joined_channel` - チャンネル参加

### 2.4 設定の保存

1. **「Save Changes」** をクリック
2. アプリの再インストールが求められた場合は、**「Reinstall App」** をクリック

## ステップ3: イベント処理の実装

### 3.1 基本的なイベントハンドラー

```python
# app/services/slack_service.py
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SlackEventHandler:
    def __init__(self):
        self.handlers = {
            "message": self.handle_message,
            "app_mention": self.handle_app_mention,
            "team_join": self.handle_team_join,
        }
    
    async def process_event(self, event_data: Dict[str, Any]):
        """イベントを処理"""
        event = event_data.get("event", {})
        event_type = event.get("type")
        
        if event_type in self.handlers:
            try:
                await self.handlers[event_type](event)
            except Exception as e:
                logger.error(f"Event handling error: {e}")
        else:
            logger.warning(f"Unhandled event type: {event_type}")
    
    async def handle_message(self, event: Dict[str, Any]):
        """メッセージイベントの処理"""
        # ボット自身のメッセージは無視
        if event.get("bot_id"):
            return
            
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "")
        
        logger.info(f"Message from {user_id}: {text}")
        
        # AI Agent処理を呼び出し
        # await self.process_ai_interaction(user_id, channel_id, text)
    
    async def handle_app_mention(self, event: Dict[str, Any]):
        """アプリメンションの処理"""
        user_id = event.get("user")
        channel_id = event.get("channel")
        text = event.get("text", "")
        
        # メンション文字列を除去
        clean_text = self.remove_mention(text)
        
        logger.info(f"App mention from {user_id}: {clean_text}")
        
        # AI Agent処理を呼び出し
        # await self.process_ai_interaction(user_id, channel_id, clean_text)
    
    async def handle_team_join(self, event: Dict[str, Any]):
        """新しいユーザー参加の処理"""
        user_id = event.get("user", {}).get("id")
        logger.info(f"New user joined: {user_id}")
        
        # ウェルカムメッセージの送信など
        # await self.send_welcome_message(user_id)
    
    def remove_mention(self, text: str) -> str:
        """メンション文字列を除去"""
        import re
        return re.sub(r'<@[A-Z0-9]+>', '', text).strip()
```

### 3.2 完全なイベントエンドポイント

```python
# app/api/slack_endpoints.py
from fastapi import APIRouter, Request, HTTPException
from app.services.slack_service import SlackEventHandler
import json
import hashlib
import hmac
import time

router = APIRouter()
event_handler = SlackEventHandler()

@router.post("/slack/events")
async def handle_slack_events(request: Request):
    """Slack Events APIからのイベントを処理"""
    
    # リクエストの検証
    if not await verify_slack_request(request):
        raise HTTPException(status_code=401, detail="Invalid request signature")
    
    body = await request.body()
    data = json.loads(body)
    
    # URL verification challenge
    if data.get("type") == "url_verification":
        return {"challenge": data["challenge"]}
    
    # Event callback処理
    elif data.get("type") == "event_callback":
        await event_handler.process_event(data)
        return {"status": "ok"}
    
    return {"status": "ignored"}

async def verify_slack_request(request: Request) -> bool:
    """Slackリクエストの署名を検証"""
    signing_secret = settings.SLACK_SIGNING_SECRET
    if not signing_secret:
        return True  # 開発環境では検証をスキップ
    
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    signature = request.headers.get("X-Slack-Signature")
    
    if not timestamp or not signature:
        return False
    
    # Replay attack防止（5分以内のリクエストのみ受け入れ）
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    body = await request.body()
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    
    computed_signature = hmac.new(
        signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"v0={computed_signature}"
    
    return hmac.compare_digest(expected_signature, signature)
```

## ステップ4: 権限（Scopes）の設定

Events APIと連携するために必要な権限を設定：

### 4.1 Bot Token Scopes

1. Slack Appの設定画面で **「OAuth & Permissions」** をクリック
2. **「Scopes」** セクションの **「Bot Token Scopes」** で以下を追加：

#### 基本権限
- `chat:write` - メッセージ送信
- `chat:write.public` - 参加していないチャンネルへの投稿
- `channels:read` - パブリックチャンネル情報の読み取り
- `groups:read` - プライベートチャンネル情報の読み取り
- `im:read` - ダイレクトメッセージ情報の読み取り
- `users:read` - ユーザー情報の読み取り

#### イベント関連
- `channels:history` - チャンネル履歴の読み取り
- `groups:history` - プライベートチャンネル履歴の読み取り
- `im:history` - ダイレクトメッセージ履歴の読み取り

## ステップ5: 環境変数の設定

### 5.1 必要なトークンの取得

1. **Bot User OAuth Token**: `OAuth & Permissions` ページの `xoxb-` で始まるトークン
2. **Signing Secret**: `Basic Information` ページの `App Credentials` セクション

### 5.2 .envファイルの設定

```bash
# .env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## ステップ6: テストと検証

### 6.1 基本テスト

1. FastAPIサーバーとngrokを起動
2. Slackワークスペースでボットにメンションを送信
3. サーバーログでイベント受信を確認

### 6.2 デバッグ用ログ設定

```python
# app/main.py
import logging

# ログレベルの設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Slackイベント専用ログ
slack_logger = logging.getLogger("slack_events")
slack_logger.setLevel(logging.DEBUG)
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. URL Verification失敗
```
❌ "url_verification challenge failed"
```
**解決方法:**
- ngrok URLが正しく設定されているか確認
- FastAPIサーバーが起動しているか確認
- `/slack/events` エンドポイントが実装されているか確認

#### 2. イベントが受信されない
```
❌ Events not being received
```
**解決方法:**
- Event Subscriptionsが有効になっているか確認
- 適切なイベントタイプが購読されているか確認
- ボットが該当チャンネルに参加しているか確認

#### 3. 権限エラー
```
❌ "missing_scope" error
```
**解決方法:**
- 必要なBot Token Scopesが設定されているか確認
- アプリの再インストールを実行
- ワークスペース管理者に権限を確認

#### 4. 署名検証エラー
```
❌ Invalid request signature
```
**解決方法:**
- SLACK_SIGNING_SECRETが正しく設定されているか確認
- タイムスタンプのずれがないか確認
- 署名検証ロジックを確認

## 本番環境への展開

### 1. HTTPSエンドポイントの準備
- Heroku、AWS、GCPなどでHTTPSエンドポイントを用意
- SSL証明書が有効であることを確認

### 2. 環境変数の設定
```bash
# 本番環境
SLACK_BOT_TOKEN=xoxb-production-token
SLACK_SIGNING_SECRET=production-signing-secret
USE_MOCK_LLM=false
OPENAI_API_KEY=production-openai-key
```

### 3. Request URLの更新
- Slack Appの設定でRequest URLを本番環境のURLに変更
- URL Verificationを再実行

## 参考リンク

- [Slack Events API公式ドキュメント](https://api.slack.com/events)
- [イベントタイプ一覧](https://api.slack.com/events)
- [Bot Token Scopes](https://api.slack.com/scopes)
- [Request verification](https://api.slack.com/authentication/verifying-requests-from-slack)
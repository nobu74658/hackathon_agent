# AI営業支援エージェント - 管理者ガイド

## 概要

このガイドは、AI営業支援エージェントのシステム管理者向けに、インストール、設定、運用、保守に関する詳細情報を提供します。

## システム要件

### ハードウェア要件

**最小構成（〜50ユーザー）**
- CPU: 4コア
- メモリ: 8GB
- ストレージ: 50GB SSD

**推奨構成（〜500ユーザー）**
- CPU: 8コア
- メモリ: 16GB
- ストレージ: 200GB SSD

**エンタープライズ構成（500ユーザー以上）**
- CPU: 16コア以上
- メモリ: 32GB以上
- ストレージ: 500GB SSD以上

### ソフトウェア要件

- OS: Ubuntu 20.04 LTS / CentOS 8 / macOS 11+
- Python: 3.8以上
- PostgreSQL: 13以上
- Redis: 6.0以上
- Docker: 20.10以上（オプション）

## インストール手順

### 1. システムの準備

```bash
# Ubuntu/Debianの場合
sudo apt update
sudo apt install -y python3.8 python3-pip postgresql redis-server nginx

# CentOS/RHELの場合
sudo yum install -y python38 python38-pip postgresql13 redis nginx
```

### 2. プロジェクトのセットアップ

```bash
# プロジェクトのクローン
git clone https://github.com/company/ai-sales-agent.git
cd ai-sales-agent/backend

# Python仮想環境の作成
python3 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -e ".[dev]"
```

### 3. データベースの設定

```bash
# PostgreSQLの設定
sudo -u postgres psql

CREATE DATABASE salesai_db;
CREATE USER salesai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE salesai_db TO salesai_user;
\q

# データベースマイグレーション
alembic upgrade head

# 初期データの投入
python scripts/init_database.py
python scripts/seed_knowledge_base.py
```

### 4. 環境変数の設定

```bash
# .envファイルの作成
cp .env.example .env

# 本番環境用の設定
cat > .env << EOF
# アプリケーション設定
APP_NAME="AI Sales Agent"
APP_VERSION="1.0.0"
ENVIRONMENT="production"
DEBUG=false
LOG_LEVEL=INFO

# データベース設定
DATABASE_URL=postgresql+asyncpg://salesai_user:secure_password@localhost/salesai_db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis設定
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# Slack設定
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}
SLACK_APP_TOKEN=${SLACK_APP_TOKEN}

# LLM設定
USE_MOCK_LLM=false
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
LLM_PROVIDER=openai  # openai or anthropic
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_REQUEST_TIMEOUT=30

# セキュリティ設定
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=["https://your-domain.com"]
ALLOWED_HOSTS=["your-domain.com", "localhost"]

# パフォーマンス設定
WORKERS=4
WORKER_CONNECTIONS=1000
KEEPALIVE=5
EOF
```

## Slack アプリケーションの設定

### 1. Slack App の作成

1. [api.slack.com/apps](https://api.slack.com/apps) にアクセス
2. 「Create New App」→「From an app manifest」を選択
3. 以下のマニフェストを使用：

```yaml
display_information:
  name: AI営業支援エージェント
  description: AIによる営業活動の支援とコーチング
  background_color: "#1A1A1A"
  
features:
  app_home:
    home_tab_enabled: true
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
    
  bot_user:
    display_name: AI営業支援
    always_online: true
    
  slash_commands:
    - command: /ai_help
      url: https://your-domain.com/api/v1/slack/commands
      description: ヘルプを表示
      should_escape: false
      
    - command: /ai_knowledge
      url: https://your-domain.com/api/v1/slack/commands
      description: ナレッジベースを検索
      usage_hint: "[検索キーワード]"
      should_escape: false
      
    - command: /ai_history
      url: https://your-domain.com/api/v1/slack/commands
      description: 成長履歴を表示
      should_escape: false

oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - channels:read
      - chat:write
      - commands
      - groups:history
      - groups:read
      - im:history
      - im:read
      - im:write
      - users:read

settings:
  event_subscriptions:
    request_url: https://your-domain.com/api/v1/slack/events
    bot_events:
      - app_mention
      - message.im
      
  interactivity:
    is_enabled: true
    request_url: https://your-domain.com/api/v1/slack/interactive
    
  org_deploy_enabled: false
  socket_mode_enabled: false
```

### 2. トークンの取得と設定

1. 「OAuth & Permissions」から Bot User OAuth Token を取得
2. 「Basic Information」から Signing Secret を取得
3. Socket Mode を有効にする場合は App-Level Token を生成
4. 取得したトークンを環境変数に設定

## サービスの起動と管理

### systemd サービスの作成

```bash
# サービスファイルの作成
sudo cat > /etc/systemd/system/ai-sales-agent.service << EOF
[Unit]
Description=AI Sales Agent API Service
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=salesai
Group=salesai
WorkingDirectory=/opt/ai-sales-agent/backend
Environment="PATH=/opt/ai-sales-agent/backend/venv/bin"
ExecStart=/opt/ai-sales-agent/backend/venv/bin/gunicorn \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/ai-sales-agent/access.log \
    --error-logfile /var/log/ai-sales-agent/error.log \
    app.main:app
    
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# サービスの有効化と起動
sudo systemctl daemon-reload
sudo systemctl enable ai-sales-agent
sudo systemctl start ai-sales-agent
```

### Nginx の設定

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Slack
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # タイムアウト設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静的ファイル
    location /static {
        alias /opt/ai-sales-agent/backend/static;
        expires 30d;
    }
}
```

## 監視とログ

### ログの設定

```python
# app/core/logging_config.py
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "/var/log/ai-sales-agent/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
            "level": "INFO"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
```

### モニタリング設定

```bash
# Prometheus メトリクスの有効化
pip install prometheus-client

# Grafana ダッシュボードの設定
docker run -d \
  -p 3000:3000 \
  --name=grafana \
  -v grafana-storage:/var/lib/grafana \
  grafana/grafana
```

### ヘルスチェック

```bash
# APIヘルスチェック
curl https://your-domain.com/api/v1/health

# 詳細なステータス
curl https://your-domain.com/api/v1/health/detailed
```

## バックアップとリストア

### 自動バックアップスクリプト

```bash
#!/bin/bash
# /opt/ai-sales-agent/scripts/backup.sh

BACKUP_DIR="/backup/ai-sales-agent"
DATE=$(date +%Y%m%d_%H%M%S)

# データベースバックアップ
pg_dump -U salesai_user -h localhost salesai_db > \
    ${BACKUP_DIR}/db_backup_${DATE}.sql

# Redisバックアップ
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb ${BACKUP_DIR}/redis_backup_${DATE}.rdb

# ナレッジベースファイルのバックアップ
tar -czf ${BACKUP_DIR}/knowledge_backup_${DATE}.tar.gz \
    /opt/ai-sales-agent/backend/data/knowledge

# 古いバックアップの削除（30日以上）
find ${BACKUP_DIR} -type f -mtime +30 -delete
```

### cron設定

```bash
# 毎日午前2時にバックアップ実行
0 2 * * * /opt/ai-sales-agent/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## セキュリティ設定

### 1. API レート制限

```python
# app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute", "1000 per hour"]
)
```

### 2. データ暗号化

```python
# 環境変数の暗号化
from cryptography.fernet import Fernet

# キーの生成
encryption_key = Fernet.generate_key()

# データの暗号化
fernet = Fernet(encryption_key)
encrypted_data = fernet.encrypt(sensitive_data.encode())
```

### 3. アクセス制御

- IPホワイトリスト設定
- Slack署名の検証
- APIキーのローテーション

## パフォーマンスチューニング

### 1. データベース最適化

```sql
-- インデックスの作成
CREATE INDEX idx_dialogue_sessions_user_id ON dialogue_sessions(user_id);
CREATE INDEX idx_dialogue_messages_session_id ON dialogue_messages(session_id);
CREATE INDEX idx_conversation_insights_user_id ON conversation_insights(user_id);

-- 定期的なVACUUM
VACUUM ANALYZE dialogue_sessions;
VACUUM ANALYZE dialogue_messages;
```

### 2. Redis設定

```conf
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### 3. アプリケーション設定

```python
# 非同期処理の最適化
app = FastAPI(
    title="AI Sales Agent",
    docs_url=None,  # 本番環境ではドキュメントを無効化
    redoc_url=None
)

# コネクションプーリング
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 40
REDIS_MAX_CONNECTIONS = 50
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. メモリ使用量が高い

```bash
# プロセスの確認
ps aux | grep gunicorn

# メモリ使用量の詳細
cat /proc/[PID]/status | grep -i vmsize

# 解決策
- ワーカー数を減らす
- メモリリークの確認
- Redisのmaxmemory設定
```

#### 2. レスポンスが遅い

```bash
# スロークエリの確認
tail -f /var/log/postgresql/postgresql.log | grep -i slow

# API応答時間の確認
grep "response_time" /var/log/ai-sales-agent/access.log | awk '{sum+=$NF} END {print sum/NR}'

# 解決策
- データベースインデックスの追加
- キャッシュの活用
- LLMタイムアウトの調整
```

#### 3. Slack接続エラー

```bash
# Slackイベントログの確認
grep "slack" /var/log/ai-sales-agent/app.log

# ネットワーク接続の確認
curl -I https://slack.com/api/api.test

# 解決策
- トークンの再生成
- ファイアウォール設定の確認
- Rate Limitの確認
```

## アップグレード手順

### 1. 計画的なアップグレード

```bash
# 現在のバージョン確認
python -c "import app; print(app.__version__)"

# バックアップの作成
./scripts/backup.sh

# 新バージョンの取得
git fetch origin
git checkout tags/v1.1.0
```

### 2. 依存関係の更新

```bash
# 仮想環境での更新
source venv/bin/activate
pip install -U -e ".[dev]"

# データベースマイグレーション
alembic upgrade head
```

### 3. サービスの再起動

```bash
# グレースフルな再起動
sudo systemctl reload ai-sales-agent

# 完全な再起動（必要な場合）
sudo systemctl restart ai-sales-agent
```

## サポートとリソース

### ドキュメント

- [API仕様書](./api_documentation.md)
- [開発者ガイド](./developer_guide.md)
- [FAQ](./faq.md)

### サポートチャネル

- 緊急時: ops-emergency@company.com
- 一般的な質問: ai-support@company.com
- Slack: #ai-sales-agent-ops

### 監視ダッシュボード

- Grafana: https://monitoring.company.com/d/ai-sales-agent
- Kibana: https://logs.company.com/app/kibana
- Sentry: https://sentry.company.com/projects/ai-sales-agent
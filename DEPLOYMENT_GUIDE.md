# 営業成長AI支援エージェント - デプロイメントガイド

## 🚀 デプロイメント概要

### サポート環境
- **開発環境**: ローカル開発 + Mock LLM
- **ステージング環境**: Docker + 実際のLLM
- **本番環境**: クラウドサービス + 完全機能

### 前提条件
- Python 3.11+
- Redis Server
- OpenAI API Account
- Slack App Setup
- ngrok (ローカル開発時)

## 🛠️ 環境別セットアップ

### 1. ローカル開発環境

#### 基本セットアップ
```bash
# リポジトリクローン
git clone <repository-url>
cd hackathon_agent/backend

# 仮想環境作成
uv venv
source .venv/bin/activate  # macOS/Linux
# or .venv\Scripts\activate  # Windows

# 依存関係インストール
uv pip install -e ".[dev]"
```

#### Redis セットアップ
```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows (WSL推奨)
sudo apt-get install redis-server
redis-server --daemonize yes
```

#### 環境変数設定
```bash
# .env ファイル作成
cat > .env << 'EOF'
# Application
APP_NAME="Sales Growth AI Backend"
DEBUG=true

# LLM設定
USE_MOCK_LLM=true
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Slack
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
LOG_LEVEL=DEBUG
EOF
```

#### サーバー起動
```bash
# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ヘルスチェック
curl http://localhost:8000/api/slack/health
```

#### ngrok 設定 (Slack Webhook用)
```bash
# ngrokインストール
brew install ngrok  # macOS
# or npm install -g ngrok

# トンネル作成
ngrok http 8000

# 出力されるHTTPS URLをSlack App設定で使用
# 例: https://abc123.ngrok.io/api/slack/events
```

### 2. ステージング環境 (Docker)

#### Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存関係
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv pip install --system -e ".[dev]"

# アプリケーションコード
COPY app/ ./app/
COPY .env ./

# ポート公開
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/slack/health || exit 1

# アプリケーション起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - USE_MOCK_LLM=false
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    env_file:
      - .env
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### Docker起動
```bash
# イメージビルド・起動
docker-compose up -d

# ログ確認
docker-compose logs -f app

# ヘルスチェック
curl http://localhost:8000/api/slack/health

# 停止
docker-compose down
```

### 3. 本番環境 (クラウドデプロイ)

#### 3.1 Heroku デプロイ

```bash
# Heroku CLI インストール・ログイン
brew install heroku/brew/heroku
heroku login

# アプリケーション作成
heroku create your-sales-ai-app

# Redis アドオン追加
heroku addons:create heroku-redis:premium-0

# 環境変数設定
heroku config:set USE_MOCK_LLM=false
heroku config:set OPENAI_API_KEY=your-openai-api-key
heroku config:set SLACK_BOT_TOKEN=your-slack-bot-token
heroku config:set SLACK_SIGNING_SECRET=your-signing-secret

# Procfile 作成
echo "web: uvicorn app.main:app --host=0.0.0.0 --port=\$PORT" > Procfile

# デプロイ
git add .
git commit -m "Initial deployment"
git push heroku main

# ログ確認
heroku logs --tail
```

#### 3.2 AWS ECS デプロイ

##### ECR Setup
```bash
# ECRリポジトリ作成
aws ecr create-repository --repository-name sales-ai-backend

# Docker login
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-west-2.amazonaws.com

# イメージビルド・プッシュ
docker build -t sales-ai-backend .
docker tag sales-ai-backend:latest 123456789.dkr.ecr.us-west-2.amazonaws.com/sales-ai-backend:latest
docker push 123456789.dkr.ecr.us-west-2.amazonaws.com/sales-ai-backend:latest
```

##### ECS Task Definition
```json
{
  "family": "sales-ai-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::123456789:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "sales-ai-backend",
      "image": "123456789.dkr.ecr.us-west-2.amazonaws.com/sales-ai-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "USE_MOCK_LLM", "value": "false"},
        {"name": "REDIS_URL", "value": "redis://redis-cluster.abc123.cache.amazonaws.com:6379/0"}
      ],
      "secrets": [
        {"name": "OPENAI_API_KEY", "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:openai-api-key"},
        {"name": "SLACK_BOT_TOKEN", "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:slack-bot-token"},
        {"name": "SLACK_SIGNING_SECRET", "valueFrom": "arn:aws:secretsmanager:us-west-2:123456789:secret:slack-signing-secret"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/sales-ai-backend",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3.3 Google Cloud Run デプロイ

```bash
# gcloud初期化
gcloud init
gcloud config set project your-project-id

# Container Registry設定
gcloud auth configure-docker

# イメージビルド・プッシュ
docker build -t gcr.io/your-project-id/sales-ai-backend .
docker push gcr.io/your-project-id/sales-ai-backend

# Cloud Run デプロイ
gcloud run deploy sales-ai-backend \
  --image gcr.io/your-project-id/sales-ai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars USE_MOCK_LLM=false \
  --set-env-vars REDIS_URL=redis://redis-ip:6379/0 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10
```

## 🔐 セキュリティ設定

### 1. 環境変数管理

#### 開発環境
```bash
# .env ファイル (Git管理外)
echo ".env" >> .gitignore
```

#### 本番環境
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name "sales-ai/openai-key" \
  --description "OpenAI API Key for Sales AI" \
  --secret-string "your-openai-api-key"

# HashiCorp Vault
vault kv put secret/sales-ai \
  openai_key="your-openai-api-key" \
  slack_token="your-slack-token"
```

### 2. ネットワークセキュリティ

#### CORS設定
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### Slack Webhook検証
```python
# app/api/slack_endpoints.py
def verify_slack_signature(body: bytes, signature: str, timestamp: str) -> bool:
    """Slack署名検証"""
    slack_signing_secret = settings.SLACK_SIGNING_SECRET
    # 実装済み
```

### 3. ログ・監視設定

#### 構造化ログ
```python
# app/core/logging.py
import structlog

logger = structlog.get_logger()
logger.info("User message processed", 
           session_id=session_id, 
           user_id=user_id,
           completeness_score=score)
```

#### プロメテウス メトリクス (オプション)
```python
# requirements追加: prometheus_client
from prometheus_client import Counter, Histogram

REQUESTS_TOTAL = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')
```

## 📊 監視・運用

### 1. ヘルスチェック

#### アプリケーション
```bash
# 基本ヘルスチェック
curl http://localhost:8000/api/slack/health

# 詳細ヘルスチェック
curl http://localhost:8000/api/test/health
```

#### インフラストラクチャ
```bash
# Redis接続確認
redis-cli -h localhost -p 6379 ping

# OpenAI API確認
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### 2. ログ管理

#### ローカル開発
```bash
# アプリケーションログ
tail -f app.log

# Uvicornログ
uvicorn app.main:app --log-level debug
```

#### 本番環境
```bash
# Docker logs
docker-compose logs -f app

# Heroku logs
heroku logs --tail

# AWS CloudWatch
aws logs tail /ecs/sales-ai-backend --follow
```

### 3. パフォーマンス監視

#### メトリクス例
```python
# 主要指標
- 対話セッション数/時間
- 平均応答時間
- エラー率
- Redis接続数
- OpenAI API使用量
```

#### アラート設定
```yaml
# Prometheus Alerting Rules
groups:
  - name: sales-ai
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowResponse
        expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Slow response time detected"
```

## 🔄 CI/CD パイプライン

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy Sales AI Backend

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install --system -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest --cov=app tests/
        
    - name: Run linting
      run: |
        black --check app tests
        ruff check app tests
        mypy app

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{secrets.HEROKU_API_KEY}}
        heroku_app_name: "your-sales-ai-app"
        heroku_email: "your-email@example.com"
```

## 📝 チェックリスト

### デプロイ前チェック

- [ ] 全テストがパス
- [ ] 環境変数が正しく設定されている
- [ ] Redis接続が確認できる
- [ ] OpenAI API キーが有効
- [ ] Slack App設定が完了
- [ ] CORS設定が適切
- [ ] ログレベルが適切に設定されている
- [ ] ヘルスチェックエンドポイントが応答する

### 本番デプロイ後チェック

- [ ] アプリケーションが起動している
- [ ] Slack Webhookが正常に受信できる
- [ ] AI対話が正常に動作する
- [ ] エラーログが異常でない
- [ ] パフォーマンスメトリクスが正常範囲内
- [ ] SSL証明書が有効
- [ ] 監視・アラートが設定されている

## 🆘 トラブルシューティング

### よくある問題

#### 1. Slack Events受信できない
```bash
# 診断手順
1. ngrok/プロキシURLの確認
2. Slack App設定のWebhook URLの確認
3. ファイアウォール・ネットワーク設定の確認
4. Signing Secretの確認

# ログ確認
curl -X POST http://localhost:8000/api/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type": "url_verification", "challenge": "test"}'
```

#### 2. OpenAI API エラー
```bash
# API Key確認
export OPENAI_API_KEY="your-key"
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# 使用量確認
# OpenAI Dashboard > Usage で確認
```

#### 3. Redis接続エラー
```bash
# Redis起動確認
redis-cli ping

# 接続テスト
redis-cli -h localhost -p 6379 info

# Docker環境での確認
docker-compose exec redis redis-cli ping
```

#### 4. メモリ・CPU使用量の問題
```bash
# コンテナリソース確認
docker stats

# プロセス確認
ps aux | grep uvicorn

# メモリリーク確認
top -p $(pgrep -f uvicorn)
```

---

適切なデプロイメント環境を選択し、段階的にテスト・検証を行ってください。本番環境では必ずバックアップとロールバック計画を準備してください。
# 新人営業マン成長支援AIエージェント システム設計書

## 1. システム概要

### 1.1 システム構成
本システムは、マイクロサービスアーキテクチャを採用し、各機能を独立したサービスとして実装する。

### 1.2 主要コンポーネント
1. **Webアプリケーション** - ユーザーインターフェース
2. **APIゲートウェイ** - リクエストルーティング、認証
3. **コアサービス** - ビジネスロジック実装
4. **AIサービス** - LLM連携、自然言語処理
5. **データストア** - データ永続化
6. **メッセージング** - 非同期処理

## 2. 詳細設計

### 2.1 Webアプリケーション

#### 2.1.1 技術スタック
- **フレームワーク**: Next.js 14 (App Router)
- **UI ライブラリ**: React 18
- **スタイリング**: Tailwind CSS
- **状態管理**: Zustand
- **フォーム管理**: React Hook Form
- **API通信**: Axios + React Query

#### 2.1.2 ディレクトリ構造
```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (main)/
│   │   ├── dashboard/
│   │   ├── sessions/
│   │   ├── chat/
│   │   ├── plans/
│   │   └── reports/
│   └── api/
├── components/
│   ├── common/
│   ├── features/
│   └── layouts/
├── hooks/
├── lib/
├── services/
└── types/
```

### 2.2 バックエンドサービス

#### 2.2.1 APIゲートウェイ
```python
# main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.middleware import AuthMiddleware, RateLimitMiddleware
from app.routers import auth, sessions, ai, plans

app = FastAPI(title="Sales Growth AI Agent API")

# ミドルウェア設定
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.add_middleware(AuthMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# ルーター登録
app.include_router(auth.router, prefix="/api/auth")
app.include_router(sessions.router, prefix="/api/sessions")
app.include_router(ai.router, prefix="/api/ai")
app.include_router(plans.router, prefix="/api/plans")
```

#### 2.2.2 コアサービス構造
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── models/
│   │   ├── user.py
│   │   ├── session.py
│   │   └── action_plan.py
│   ├── schemas/
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── session_service.py
│   │   └── ai_service.py
│   └── utils/
├── tests/
└── requirements.txt
```

### 2.3 AIサービス設計

#### 2.3.1 LLM統合レイヤー
```python
# services/llm_service.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def generate_questions(self, context: Dict[str, Any]) -> List[str]:
        pass
    
    @abstractmethod
    async def create_action_plan(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # GPT-4による解析実装
        pass

class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        # Claude 3による解析実装
        pass
```

#### 2.3.2 対話管理システム
```python
# services/dialogue_manager.py
class DialogueManager:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.context_store = ContextStore()
    
    async def start_session(self, session_id: str, initial_data: Dict):
        context = await self._build_initial_context(initial_data)
        await self.context_store.save(session_id, context)
        return await self._generate_initial_questions(context)
    
    async def process_response(self, session_id: str, response: str):
        context = await self.context_store.get(session_id)
        updated_context = await self._update_context(context, response)
        
        if self._is_sufficient_info(updated_context):
            return await self._generate_action_plan(updated_context)
        else:
            return await self._generate_followup_questions(updated_context)
```

### 2.4 データベース設計

#### 2.4.1 RDBスキーマ（PostgreSQL）
```sql
-- ユーザーテーブル
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    department VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1on1セッションテーブル
CREATE TABLE one_on_one_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    manager_id UUID REFERENCES users(id),
    session_date TIMESTAMP NOT NULL,
    raw_text TEXT,
    extracted_points JSONB,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- アクションプランテーブル
CREATE TABLE action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES one_on_one_sessions(id),
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- アクションアイテムテーブル
CREATE TABLE action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES action_plans(id),
    description TEXT NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20),
    due_date DATE,
    status VARCHAR(50) DEFAULT 'pending',
    metrics JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 対話履歴テーブル
CREATE TABLE dialogue_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES one_on_one_sessions(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.4.2 ベクトルデータベース設計（Pinecone）
```python
# Vector DB インデックス構造
index_config = {
    "name": "sales-growth-embeddings",
    "dimension": 1536,  # OpenAI embeddings
    "metric": "cosine",
    "metadata_config": {
        "indexed": ["user_id", "session_id", "category", "timestamp"]
    }
}

# ベクトル化するデータ
vector_data = {
    "id": "unique_id",
    "values": embedding_vector,
    "metadata": {
        "user_id": "user_123",
        "session_id": "session_456",
        "category": "communication_skill",
        "content": "original_text",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

### 2.5 セキュリティ設計

#### 2.5.1 認証・認可
```python
# core/security.py
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

class SecurityManager:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"])
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
    
    def create_access_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=30)
        payload = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise UnauthorizedException()
```

#### 2.5.2 データ暗号化
```python
# utils/encryption.py
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 2.6 非同期処理設計

#### 2.6.1 メッセージキュー構成
```python
# services/message_queue.py
import aio_pika
from typing import Callable

class MessageQueue:
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection = None
        self.channel = None
    
    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel()
    
    async def publish(self, queue_name: str, message: Dict):
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
    
    async def consume(self, queue_name: str, callback: Callable):
        queue = await self.channel.declare_queue(queue_name, durable=True)
        await queue.consume(callback, no_ack=False)
```

### 2.7 監視・ロギング設計

#### 2.7.1 ロギング構成
```python
# core/logging.py
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    logHandler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    logHandler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(logHandler)
    logger.setLevel(logging.INFO)
    
    return logger
```

#### 2.7.2 メトリクス収集
```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# メトリクス定義
request_count = Counter(
    'api_requests_total', 
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users_total',
    'Total active users'
)

llm_api_calls = Counter(
    'llm_api_calls_total',
    'Total LLM API calls',
    ['provider', 'operation']
)
```

### 2.8 エラーハンドリング

#### 2.8.1 例外階層
```python
# core/exceptions.py
class BaseAPIException(Exception):
    status_code = 500
    detail = "Internal server error"
    
class ValidationException(BaseAPIException):
    status_code = 400
    detail = "Validation error"
    
class UnauthorizedException(BaseAPIException):
    status_code = 401
    detail = "Unauthorized"
    
class NotFoundException(BaseAPIException):
    status_code = 404
    detail = "Resource not found"
    
class LLMServiceException(BaseAPIException):
    status_code = 503
    detail = "LLM service unavailable"
```

### 2.9 テスト設計

#### 2.9.1 テスト戦略
- **単体テスト**: pytest, coverage 90%以上
- **統合テスト**: API エンドポイントテスト
- **E2Eテスト**: Cypress
- **負荷テスト**: Locust

#### 2.9.2 テストコード例
```python
# tests/test_session_service.py
import pytest
from app.services import SessionService

@pytest.fixture
def session_service():
    return SessionService()

async def test_analyze_session_text(session_service, mock_llm):
    # Given
    text = "新人の田中さんは顧客とのコミュニケーションに課題がある"
    
    # When
    result = await session_service.analyze_text(text)
    
    # Then
    assert "improvement_points" in result
    assert len(result["improvement_points"]) > 0
    assert result["improvement_points"][0]["category"] == "communication"
```

## 3. インフラストラクチャ設計

### 3.1 AWS構成
```
VPC
├── Public Subnet
│   ├── ALB
│   └── NAT Gateway
├── Private Subnet 1
│   ├── ECS Cluster (Web App)
│   └── ECS Cluster (API)
├── Private Subnet 2
│   ├── RDS (Multi-AZ)
│   └── ElastiCache
└── Private Subnet 3
    └── ECS Cluster (AI Service)
```

### 3.2 CI/CD パイプライン
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster prod-cluster --service api-service --force-new-deployment
```

## 4. パフォーマンス最適化

### 4.1 キャッシング戦略
- **Redis キャッシュ**: セッションデータ、頻繁にアクセスされるマスタデータ
- **CDN**: 静的アセット配信
- **API レスポンスキャッシュ**: 変更頻度の低いデータ

### 4.2 データベース最適化
- インデックス設計
- クエリ最適化
- コネクションプーリング
- Read Replica活用

## 5. 今後の拡張計画

### 5.1 機能拡張
- 音声入力対応
- モバイルアプリ開発
- Slack/Teams連携
- 外部CRM連携

### 5.2 技術的改善
- GraphQL API追加
- リアルタイム通信（WebSocket）
- AI モデルのファインチューニング
- マルチテナント対応
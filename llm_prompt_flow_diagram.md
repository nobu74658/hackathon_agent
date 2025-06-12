# Sales Growth AI Agent - LLMプロンプトフロー図

## システム全体のプロンプトフロー

```mermaid
graph TB
    subgraph "ユーザー入力"
        A[1on1ミーティングテキスト入力]
    end
    
    
    subgraph "Backend フロー (FastAPI)"
        A --> F[DialogueManager.start_dialogue]
        F --> F1{初期対話プロンプト}
        F1 --> F2[初期質問生成<br/>3-5個の質問]
        
        F2 --> G[process_user_response]
        G --> G1{完全性評価プロンプト}
        G1 --> G2[情報充足度スコア<br/>0-100]
        
        G2 --> H{スコア評価}
        H -->|不十分| I[generate_followup_questions]
        I --> I1{フォローアップ質問プロンプト}
        I1 --> I2[追加質問生成]
        I2 --> G
        
        H -->|充分| J[generate_action_plan]
        J --> J1{アクションプラン生成プロンプト}
        J1 --> J2[包括的アクションプラン<br/>JSON形式]
        
        subgraph "メモリサービス"
            K[ConversationMemoryService]
            K --> K1{トピック抽出プロンプト}
            K1 --> K2[主要トピック抽出<br/>3-5個]
        end
        
        G --> K
        I --> K
        J --> K
    end

    subgraph "LLMサービス"
        L[RealLLMService]
        L --> L1{初期質問生成プロンプト}
        L --> L2{フォローアップ質問生成プロンプト}  
        L --> L3{情報充足度評価プロンプト}
        L --> L4{アクションプラン生成プロンプト}
        L --> L5{トピック抽出プロンプト}
        
        L1 --> L6[AIセールスコーチとして<br/>初期質問を1つ生成]
        L2 --> L7[会話履歴に基づく<br/>フォローアップ質問]
        L3 --> L8[0-100スケールで<br/>情報充足度評価]
        L4 --> L9[包括的アクションプラン<br/>JSON形式で出力]
        L5 --> L10[3-5個の主要トピック<br/>抽出]
    end

    style F1 fill:#fff3e0
    style G1 fill:#fff3e0
    style I1 fill:#fff3e0
    style J1 fill:#fff3e0
    style K1 fill:#f3e5f5
    style L1 fill:#e8f5e8
    style L2 fill:#e8f5e8
    style L3 fill:#e8f5e8
    style L4 fill:#e8f5e8
    style L5 fill:#e8f5e8
```

## プロンプトの種類と役割

### 1. 分析系プロンプト
```mermaid
graph LR
    subgraph "テキスト分析"
        A1[1on1テキスト] --> B1[テキスト分析プロンプト<br/>mvp/ai_service.py:12-34]
        B1 --> C1[改善点抽出<br/>+ 抽象度判定<br/>+ 具体化必要性]
    end
    
    subgraph "情報評価"
        A2[会話履歴] --> B2[情報充足度評価プロンプト<br/>backend/services/real_llm_service.py:188-199]
        B2 --> C2[0-100スコア<br/>5つの評価基準]
    end
    
    subgraph "トピック抽出"
        A3[会話内容] --> B3[トピック抽出プロンプト<br/>backend/services/conversation_memory.py:196-205]
        B3 --> C3[主要トピック3-5個<br/>JSON形式]
    end
```

### 2. 対話系プロンプト
```mermaid
graph LR
    subgraph "初期対話"
        A1[セッション開始] --> B1[初期対話プロンプト<br/>backend/services/dialogue_manager.py:55-66]
        B1 --> C1[AIアシスタント役割定義<br/>+ 現状把握質問]
    end
    
    subgraph "質問生成"
        A2[改善点 + 履歴] --> B2[質問生成プロンプト<br/>mvp/ai_service.py:56-75]
        B2 --> C2[具体化のための質問<br/>+ 完了判定]
    end
    
    subgraph "フォローアップ"
        A3[会話履歴] --> B3[フォローアップ質問プロンプト<br/>backend/services/real_llm_service.py:139-147]
        B3 --> C3[次の質問<br/>自然な会話継続]
    end
```

### 3. 計画系プロンプト
```mermaid
graph LR
    subgraph "MVPアクションプラン"
        A1[改善点 + 追加情報] --> B1[アクションプラン生成プロンプト<br/>mvp/ai_service.py:106-125]
        B1 --> C1[SMART目標<br/>+ 実行ステップ<br/>+ 成功指標]
    end
    
    subgraph "包括的アクションプラン"
        A2[会話履歴全体] --> B2[アクションプラン生成プロンプト<br/>backend/services/real_llm_service.py:223-245]
        B2 --> C2[JSON形式<br/>包括的プラン<br/>+ フォローアップ]
    end
```

## プロンプトの実行フロー詳細


### システムフロー（FastAPI）
```mermaid
sequenceDiagram
    participant User as ユーザー
    participant DM as DialogueManager
    participant LLM as LLMService
    participant Memory as MemoryService
    participant OpenAI as OpenAI API

    User->>DM: セッション開始
    DM->>LLM: start_dialogue()
    LLM->>OpenAI: 初期質問生成プロンプト
    OpenAI->>LLM: 初期質問リスト
    LLM->>DM: 3-5個の質問
    
    User->>DM: 回答送信
    DM->>Memory: 会話履歴保存
    DM->>LLM: evaluate_completeness()
    LLM->>OpenAI: 情報充足度評価プロンプト
    OpenAI->>LLM: スコア（0-100）
    
    alt スコア < 70
        LLM->>OpenAI: フォローアップ質問プロンプト
        OpenAI->>LLM: 追加質問
        LLM->>DM: 次の質問
    else スコア >= 70
        DM->>LLM: generate_action_plan()
        LLM->>OpenAI: アクションプラン生成プロンプト
        OpenAI->>LLM: 包括的プラン（JSON）
        LLM->>DM: 最終アクションプラン
    end
    
    DM->>Memory: extract_topics()
    Memory->>OpenAI: トピック抽出プロンプト
    OpenAI->>Memory: 主要トピック
    
    DM->>User: 結果返却
```

## プロンプトのシステム構成

### システムプロンプト（役割定義）
1. **経験豊富なセールスコーチ** (backend/services/real_llm_service.py)
2. **AIアシスタント** (backend/services/dialogue_manager.py)

### レスポンス形式指定
- **JSON Object**: 構造化された回答が必要な分析・評価系
- **自然言語**: 対話継続が必要な質問生成系
- **数値のみ**: スコア評価系（0-100）

### プロンプトの特徴
- **日本語最適化**: 全プロンプトが日本の営業環境に特化
- **段階的情報収集**: 初期→詳細→完全性評価→プラン生成
- **文脈保持**: 会話履歴を効果的に活用
- **実用性重視**: 実行可能で測定可能な成果を目指す
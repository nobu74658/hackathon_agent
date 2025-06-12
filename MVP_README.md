# 新人営業マン成長支援AIエージェント MVP

## MVP概要

最小限の機能で動作するプロトタイプを作成します。

### コア機能（MVPで実装）
1. **1on1テキスト入力** - シンプルなテキストエリアで入力
2. **AI解析** - 改善点の抽出（OpenAI API使用）
3. **対話型質問** - 改善点を具体化するための質問生成
4. **アクションプラン表示** - 具体的な行動計画の提示

### 技術スタック（シンプル化）
- **フロントエンド**: HTML + JavaScript（React不要）
- **バックエンド**: Python Flask（軽量）
- **データベース**: SQLite（ローカル動作）
- **AI**: OpenAI API（GPT-4）

## プロジェクト構成

```
mvp/
├── app.py              # Flaskアプリケーション
├── templates/
│   └── index.html      # メインページ
├── static/
│   ├── style.css       # スタイルシート
│   └── script.js       # フロントエンドロジック
├── database.py         # データベース操作
├── ai_service.py       # OpenAI API連携
├── requirements.txt    # Python依存関係
└── README.md          # セットアップ手順
```

## セットアップ手順

1. **環境準備**
```bash
# リポジトリクローン
git clone <repository>
cd mvp

# Python仮想環境作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

2. **環境変数設定**
```bash
# .envファイル作成
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

3. **データベース初期化**
```bash
python database.py init
```

4. **アプリケーション起動**
```bash
python app.py
```

5. **ブラウザでアクセス**
```
http://localhost:5000
```

## 使い方

1. ブラウザで http://localhost:5000 にアクセス
2. 1on1の内容をテキストエリアに入力
3. 「分析開始」ボタンをクリック
4. AIが改善点を抽出して表示
5. 各改善点について追加の質問に回答
6. 具体的なアクションプランが生成される

## 開発のポイント

- **シンプルさ重視**: 複雑な機能は後回し、まず動くものを
- **ローカル完結**: クラウドサービス不要、すぐに試せる
- **拡張可能**: MVPを基に機能追加しやすい設計

## 次のステップ

MVPが動作したら：
1. ユーザー認証の追加
2. データの永続化
3. UIの改善
4. クラウドデプロイ
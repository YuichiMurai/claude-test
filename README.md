# Claude Certified Architect 試験対策ハンズオン教材

このリポジトリは、**Claude Certified Architect (CCA)** 試験対策のための包括的なハンズオン教材です。
**Google Colab** での実行を前提として設計されており、環境構築不要ですぐに学習を始められます。

📖 参考記事: [Claude Certified Architectとは？](https://www.ai-souken.com/article/what-is-claude-certified-architect-cca-f)

---

## 🎯 Claude Certified Architect (CCA) 試験の概要

Claude Certified Architect は、Anthropic が提供する公式認定資格です。以下のスキルを証明します：

- Claude API の設計・実装能力
- セキュアなAIアプリケーションの構築
- プロンプトエンジニアリングのベストプラクティス
- エンタープライズレベルのアーキテクチャ設計

---

## ☁️ なぜ Google Colab での学習を推奨するのか

| メリット | 詳細 |
|---------|------|
| **環境構築不要** | Pythonや依存パッケージのインストール不要 |
| **無料で使える** | Googleアカウントがあれば無料で利用可能 |
| **ブラウザだけで完結** | どのPCからでもアクセス可能 |
| **GPU/TPU対応** | 必要に応じて高性能な計算資源を利用可能 |
| **共有が簡単** | URLを共有するだけでコードを共有可能 |

---

## 📚 学習の進め方（推奨順序）

```
01_basics/          ← まずここから（2-3時間）
02_prompt_engineering/  ← 基礎完了後（3-4時間）
03_secure_applications/ ← 中級者向け（4-5時間）
04_architecture/    ← 上級者向け（5-6時間）
mock_exam/          ← 仕上げ（2-3時間）
```

### 各セクションの説明

| セクション | 内容 | 学習時間目安 |
|-----------|------|------------|
| **01_basics/** | API接続、基本リクエスト、ストリーミング、会話履歴 | 2-3時間 |
| **02_prompt_engineering/** | プロンプト設計、Few-shot学習、Chain of Thought | 3-4時間 |
| **03_secure_applications/** | セキュリティ、レート制限、エラーハンドリング | 4-5時間 |
| **04_architecture/** | システム設計、スケーリング、コスト最適化 | 5-6時間 |
| **mock_exam/** | 模擬試験、解説 | 2-3時間 |

---

## 🚀 Google Colab でのセットアップ手順

### ステップ 1: Colab Secrets の設定方法

Anthropic API Key を安全に管理するために **Colab Secrets** を使用します。

1. [Google Colab](https://colab.research.google.com/) を開く
2. 左サイドバーの **🔑（鍵マーク）** をクリック
3. **「+ Add new secret」** をクリック
4. 以下を入力：
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: あなたのAnthropicのAPIキー
5. **「Notebook access」** のトグルをONにする

> ⚠️ APIキーをコードに直接書かないでください。必ずColab Secretsを使用してください。

### ステップ 2: パッケージのインストール

新しいColabノートブックを開いて、最初のセルで以下を実行：

```python
# 方法1: requirements.txtから直接インストール（推奨）
!pip install -r https://raw.githubusercontent.com/YuichiMurai/claude-test/main/requirements.txt -q

# 方法2: パッケージを直接インストール
!pip install anthropic python-dotenv -q
```

### ステップ 3: リポジトリのクローン方法

```python
# リポジトリをクローン
!git clone https://github.com/YuichiMurai/claude-test.git

# ディレクトリに移動
%cd claude-test

# ファイル一覧を確認
!ls
```

### ステップ 4: API Key の設定と動作確認

```python
# Colab SecretsからAPI Keyを取得
from google.colab import userdata
import os

os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

# 動作確認
from anthropic import Anthropic

client = Anthropic()
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[{"role": "user", "content": "こんにちは！"}]
)
print(message.content[0].text)
print("✅ セットアップ完了！")
```

---

## 🔑 Anthropic API Key の取得方法

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. アカウントを作成（またはログイン）
3. **「API Keys」** メニューを開く
4. **「Create Key」** をクリック
5. キーの名前を入力して生成
6. 生成されたキーをコピー（一度しか表示されません！）

> 💡 新規登録時には無料クレジットが付与される場合があります

---

## 📝 試験対策のポイント

### 重要トピック

1. **Messages API の理解**
   - `model`, `max_tokens`, `messages` パラメータ
   - `system` プロンプトの効果的な使い方
   - ストリーミングレスポンスの実装

2. **プロンプトエンジニアリング**
   - Few-shot プロンプティング
   - Chain of Thought (CoT)
   - Constitutional AI の原則

3. **セキュリティとベストプラクティス**
   - API Key の安全な管理
   - レート制限への対応
   - コスト最適化

4. **アーキテクチャ設計**
   - スケーラブルなシステム設計
   - エラーハンドリングとリトライ戦略
   - モニタリングとロギング

---

## 💻 ローカル環境での実行方法（オプション）

Google Colab 以外でローカル環境で実行する場合：

### 前提条件
- Python 3.9 以上
- pip

### セットアップ手順

```bash
# リポジトリをクローン
git clone https://github.com/YuichiMurai/claude-test.git
cd claude-test

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt

# API Key を設定
cp .env.example .env
# .env ファイルを編集して ANTHROPIC_API_KEY を設定
```

### .env ファイルの設定

```
ANTHROPIC_API_KEY=your_api_key_here
```

---

## 📁 リポジトリ構成

```
claude-test/
├── README.md               # このファイル
├── COLAB_SETUP.md          # Colab専用セットアップガイド
├── requirements.txt        # 依存パッケージ
├── .gitignore
├── 01_basics/              # 基礎編
│   ├── README.md
│   ├── 01_api_setup.py
│   ├── 02_first_request.py
│   ├── 03_streaming.py
│   ├── 04_message_history.py
│   └── exercises/
│       ├── README.md
│       ├── exercise_01.py
│       ├── exercise_02.py
│       └── exercise_03.py
├── 02_prompt_engineering/  # 応用編（Coming Soon）
├── 03_secure_applications/ # 実践編（Coming Soon）
├── 04_architecture/        # アーキテクト編（Coming Soon）
└── mock_exam/              # 模擬試験（Coming Soon）
```

---

## 🤝 貢献について

バグ報告や改善提案は Issue または Pull Request でお知らせください。

## 📄 ライセンス

MIT License

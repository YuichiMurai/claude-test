# 03_secure_applications - 実践編（セキュアなアプリケーション開発）

Claude API を使ったセキュアなアプリケーション開発の実践的な技術を学ぶセクションです。

---

## 🎯 このセクションの学習目標

このセクションを完了すると、以下ができるようになります：

- ユーザー入力を適切に検証・サニタイズしてプロンプトインジェクション攻撃を防げる
- 個人情報（PII）を自動検出してマスキングできる
- APIエラーに対してExponential backoff で堅牢にリトライできる
- トークンバケットアルゴリズムでレート制限を実装できる
- トークン数を管理してAPIコストを最適化できる
- CCA試験で問われるセキュリティ関連の最重要概念を理解できる

## ⏱️ 学習時間の目安

**4〜5時間**（練習問題を含む）

## 📋 前提知識

- **01_basics/** と **02_prompt_engineering/** の内容を理解していること
  - Anthropic APIクライアントの初期化
  - `messages.create()` の基本的な使い方
  - システムプロンプトとプロンプトエンジニアリングの概念
  - 会話履歴の管理

---

## 📁 各ファイルの説明と学習順序

| 順序 | ファイル | 内容 |
|------|---------|------|
| 1 | `01_input_validation.py` | 入力検証・サニタイゼーション・プロンプトインジェクション対策 |
| 2 | `02_pii_handling.py` | PII（個人情報）の検出・マスキング・データ匿名化 |
| 3 | `03_error_handling.py` | APIエラー処理・Exponential backoff・フォールバック戦略 |
| 4 | `04_rate_limiting.py` | トークンバケット・リクエストキューイング・スレッドセーフ実装 |
| 5 | `05_token_management.py` | トークンカウント・コスト計算・会話履歴の効率的な管理 |

---

## ☁️ Google Colabでの実行方法

### 最初にこれを実行（毎回セッション開始時）

```python
# 最初にこれを実行
!pip install anthropic python-dotenv -q

# API Key設定
from google.colab import userdata
import os
os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')
```

### ファイルを直接実行する場合

```python
# リポジトリをクローン
!git clone https://github.com/YuichiMurai/claude-test.git
%cd claude-test

# パッケージをインストール
!pip install -r requirements.txt -q

# API Key設定
from google.colab import userdata
import os
os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

# ファイルを実行（例）
!python 03_secure_applications/01_input_validation.py
```

---

## 🔐 セキュアなアプリケーション開発の重要性

Claude API を組み込んだアプリケーションには、一般的なWebアプリケーションのセキュリティリスクに加え、**AI特有のリスク**が存在します。

### なぜ重要なのか？

| リスク | 説明 | 対策 |
|--------|------|------|
| **プロンプトインジェクション** | 悪意のある入力でAIの動作を変更される | 入力検証・サニタイゼーション |
| **PII漏洩** | 個人情報がAIに渡り記録・学習される | PIIマスキング・データ匿名化 |
| **レート制限超過** | APIリクエストが制限を超えてサービス停止 | レート制限実装・キューイング |
| **コスト爆発** | トークン消費が想定外に増大 | トークン管理・コスト最適化 |
| **サービス断絶** | APIエラーでアプリが停止 | エラーハンドリング・リトライ |

### セキュアな設計の原則

```
セキュアなClaude APIアプリケーション
├── 入力層（Input Layer）
│   ├── 長さ制限                  ← 01_input_validation.py
│   ├── 禁止文字列フィルタリング   ← 01_input_validation.py
│   └── PIIマスキング             ← 02_pii_handling.py
│
├── 処理層（Processing Layer）
│   ├── エラーハンドリング         ← 03_error_handling.py
│   ├── リトライロジック           ← 03_error_handling.py
│   └── レート制限                ← 04_rate_limiting.py
│
└── 最適化層（Optimization Layer）
    ├── トークン管理               ← 05_token_management.py
    └── コスト最適化              ← 05_token_management.py
```

---

## 🎓 CCA試験での出題ポイント

### 重要度の高いトピック

#### 1. 入力検証とプロンプトインジェクション対策
- ✅ プロンプトインジェクションとは何か、その危険性
- ✅ ユーザー入力のサニタイゼーション方法
- ✅ システムプロンプトとユーザー入力を明確に分離する手法

#### 2. 個人情報（PII）の取り扱い
- ✅ APIに個人情報を送信するリスク
- ✅ 正規表現を使った PII 検出と自動マスキング
- ✅ データ匿名化のベストプラクティス

#### 3. エラーハンドリング
- ✅ `anthropic.APIStatusError` の種類（429, 500, 529 など）
- ✅ Exponential backoff の実装パターン
- ✅ タイムアウトとフォールバック戦略

#### 4. レート制限
- ✅ Anthropic API のレート制限の仕組み（TPM, RPM）
- ✅ トークンバケットアルゴリズムの概念
- ✅ 429 エラーの適切な処理方法

#### 5. トークン管理
- ✅ プロンプトとレスポンスのトークン数計算
- ✅ `max_tokens` の適切な設定
- ✅ 長い会話履歴のトークン数管理

### 試験対策チェックリスト

- [ ] プロンプトインジェクションの原理と対策を説明できる
- [ ] PII の自動検出とマスキングを実装できる
- [ ] 429 エラーを受け取ったときの適切なリトライを実装できる
- [ ] Exponential backoff のアルゴリズムを理解している
- [ ] トークンバケットアルゴリズムを実装できる
- [ ] 会話履歴のトークン数を管理してコストを最適化できる

---

## 📝 練習問題の進め方

`exercises/` ディレクトリに3つの練習問題があります。

| 練習問題 | タイトル | 難易度 |
|----------|---------|--------|
| `exercise_01.py` | セキュアなチャットボットの実装 | ⭐⭐⭐ 中上級 |
| `exercise_02.py` | リトライ機能付きAPIクライアント | ⭐⭐⭐ 中上級 |
| `exercise_03.py` | コスト最適化システム | ⭐⭐⭐ 中上級 |

### 推奨する学習方法

1. **コードを読む**: 各ファイルの日本語コメントを読みながら理解する
2. **実行する**: Google Colab でコードを実行して出力を確認する
3. **改変する**: パラメータを変えて動作の変化を観察する
4. **練習問題に挑戦する**: `exercises/` の TODO を埋めて動作させる

詳細は `exercises/README.md` を参照してください。

---

## 🔗 参考資料

- [Anthropic API エラーハンドリング](https://docs.anthropic.com/en/api/errors)
- [Claude の安全な利用ガイド](https://docs.anthropic.com/en/docs/resources/responsible-use-policy)
- [Anthropic API レート制限](https://docs.anthropic.com/en/api/rate-limits)
- [Claude API Documentation](https://docs.anthropic.com/en/api/getting-started)

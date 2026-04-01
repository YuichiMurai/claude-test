# 04_architecture - アーキテクト編（スケーラブルなシステム設計）

Claude API を使ったスケーラブルなシステム設計のベストプラクティスを学ぶセクションです。

---

## 🎯 このセクションの学習目標

このセクションを完了すると、以下ができるようになります：

- LRUキャッシュやTTL付きキャッシュを実装してAPIコールを最適化できる
- asyncio を使って複数のリクエストを並行処理し、パフォーマンスを向上できる
- Python logging モジュールで構造化ログを実装し、システムを可観測にできる
- ワーカーキュー・サーキットブレーカー・バッチ処理などのスケーラブルパターンを実装できる
- CCA試験で問われるアーキテクチャ関連の最重要概念を理解できる

## ⏱️ 学習時間の目安

**4〜5時間**（練習問題を含む）

## 📋 前提知識

以下のセクションの内容を理解していること：

- **01_basics/** - Anthropic APIクライアントの初期化と基本操作
- **02_prompt_engineering/** - システムプロンプトとプロンプト設計
- **03_secure_applications/** - エラーハンドリング、レート制限、トークン管理

---

## 📁 各ファイルの説明と学習順序

| 順序 | ファイル | 内容 |
|------|---------|------|
| 1 | `01_caching_strategy.py` | LRUキャッシュ・TTL・キャッシュ無効化・ヒット率測定 |
| 2 | `02_async_processing.py` | asyncio・並行リクエスト・タイムアウト・パフォーマンス比較 |
| 3 | `03_monitoring.py` | 構造化ログ・メトリクス収集・エラートラッキング・ログファイル出力 |
| 4 | `04_scalable_design.py` | ワーカーキュー・バッチ処理・サーキットブレーカー・フェイルオーバー |

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
!python 04_architecture/01_caching_strategy.py
```

### ⚠️ 非同期処理（02_async_processing.py）の注意事項

Google Colab はすでにイベントループが動いているため、通常の `asyncio.run()` が使えません。
以下のようにして実行します：

```python
import nest_asyncio
nest_asyncio.apply()

import asyncio
asyncio.run(main())
```

または `await` を直接使います：

```python
# Colab のセルで直接 await を使う
await main()
```

---

## 🏗️ スケーラブルなアーキテクチャの重要性

Claude API を本番環境で使う場合、単純な実装では限界があります。
以下の課題に対処するためのアーキテクチャが必要です：

### スケーラビリティの課題

| 課題 | 問題 | 解決策 |
|------|------|--------|
| **APIコスト** | 同じリクエストを何度も送信するとコストが増大 | キャッシング |
| **レスポンス速度** | 同期処理では複数リクエストが直列実行になる | 非同期処理 |
| **障害検知** | エラーが発生してもどこで何が起きたか分からない | モニタリング |
| **高負荷対応** | リクエストが集中するとシステムが崩壊 | スケーラブル設計 |

### スケーラブルなシステムの構造

```
スケーラブルなClaude APIシステム
├── キャッシュ層（Cache Layer）
│   ├── LRUキャッシュ              ← 01_caching_strategy.py
│   ├── TTLキャッシュ              ← 01_caching_strategy.py
│   └── キャッシュ無効化            ← 01_caching_strategy.py
│
├── 並行処理層（Concurrency Layer）
│   ├── 非同期APIコール            ← 02_async_processing.py
│   ├── 並行リクエスト             ← 02_async_processing.py
│   └── タイムアウト管理            ← 02_async_processing.py
│
├── 観測可能性層（Observability Layer）
│   ├── 構造化ログ                ← 03_monitoring.py
│   ├── パフォーマンスメトリクス    ← 03_monitoring.py
│   └── エラートラッキング          ← 03_monitoring.py
│
└── スケーラブル設計層（Scalable Design Layer）
    ├── ワーカーキュー             ← 04_scalable_design.py
    ├── サーキットブレーカー         ← 04_scalable_design.py
    └── バッチ処理                 ← 04_scalable_design.py
```

---

## 🎓 CCA試験での出題ポイント

### 重要度の高いトピック

#### 1. キャッシング戦略
- ✅ LRUキャッシュの仕組みと `functools.lru_cache` の使い方
- ✅ TTL（Time To Live）キャッシュの実装
- ✅ キャッシュキーの設計（同一リクエストの判定方法）
- ✅ キャッシュ無効化のタイミングと戦略

#### 2. 非同期処理
- ✅ `asyncio` の基本（event loop, coroutine, await）
- ✅ `asyncio.gather()` による並行実行
- ✅ `asyncio.wait_for()` によるタイムアウト
- ✅ 同期処理と非同期処理のパフォーマンス比較

#### 3. モニタリングとロギング
- ✅ Python `logging` モジュールのログレベル（DEBUG/INFO/WARNING/ERROR）
- ✅ 構造化ログ（JSON形式）のメリットと実装
- ✅ メトリクス収集（レスポンスタイム、トークン数、エラー率）
- ✅ アラートの実装方法

#### 4. スケーラブル設計パターン
- ✅ ワーカーキューパターン（Producer-Consumer）
- ✅ サーキットブレーカーの状態遷移（CLOSED → OPEN → HALF_OPEN）
- ✅ バッチ処理による効率化
- ✅ フェイルオーバー戦略

### 試験対策チェックリスト

- [ ] LRUキャッシュとTTLキャッシュの違いを説明できる
- [ ] `asyncio.gather()` で並行処理するコードを書ける
- [ ] Python `logging` でログレベルを設定し構造化ログを実装できる
- [ ] サーキットブレーカーの CLOSED/OPEN/HALF_OPEN 状態を説明できる
- [ ] バッチ処理で効率を改善するシナリオを説明できる

---

## 📝 練習問題の進め方

`exercises/` ディレクトリに3つの練習問題があります（難易度：上級）。

| 練習問題 | タイトル | 難易度 |
|----------|---------|--------|
| `exercise_01.py` | 高性能APIクライアントの設計 | ⭐⭐⭐⭐ 上級 |
| `exercise_02.py` | モニタリングシステムの実装 | ⭐⭐⭐⭐ 上級 |
| `exercise_03.py` | スケーラブルアーキテクチャの構築 | ⭐⭐⭐⭐ 上級 |

### 推奨する学習方法

1. **コードを読む**: 各ファイルの日本語コメントを読みながら理解する
2. **実行する**: Google Colab でコードを実行して出力を確認する
3. **改変する**: パラメータを変えて動作の変化を観察する
4. **練習問題に挑戦する**: `exercises/` の TODO を埋めて動作させる

詳細は `exercises/README.md` を参照してください。

---

## 🔗 参考資料

- [Anthropic API ドキュメント](https://docs.anthropic.com/en/api/getting-started)
- [Python asyncio ドキュメント](https://docs.python.org/ja/3/library/asyncio.html)
- [Python logging ドキュメント](https://docs.python.org/ja/3/library/logging.html)
- [Python functools.lru_cache](https://docs.python.org/ja/3/library/functools.html#functools.lru_cache)

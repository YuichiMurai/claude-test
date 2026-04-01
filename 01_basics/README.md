# 01_basics - 基礎編

Claude API の基本的な使い方を学ぶセクションです。

---

## 🎯 学習目標

このセクションを完了すると、以下ができるようになります：

- Anthropic API クライアントの初期化と設定
- 基本的なメッセージ送受信
- ストリーミングレスポンスの実装
- マルチターン会話（会話履歴の管理）

## ⏱️ 学習時間の目安

**2〜3時間**（練習問題を含む）

## 📋 前提知識

- Python の基本文法（変数、関数、クラス、例外処理）
- Google Colab の基本的な使い方

---

## 📁 各ファイルの説明と学習順序

| 順序 | ファイル | 内容 |
|------|---------|------|
| 1 | `01_api_setup.py` | API接続の設定・初期化・接続テスト |
| 2 | `02_first_request.py` | 基本的なメッセージ送受信・パラメータ解説 |
| 3 | `03_streaming.py` | ストリーミングレスポンスの実装 |
| 4 | `04_message_history.py` | 会話履歴の管理・マルチターン会話 |
| 5 | `exercises/` | 練習問題（3問） |

---

## ☁️ Google Colab での実行方法

### 最初にこれを実行（毎回セッション開始時）

```python
# ステップ1: パッケージをインストール
!pip install anthropic python-dotenv -q

# ステップ2: API Key設定
from google.colab import userdata
import os
os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

print("✅ 準備完了！")
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

# ファイルを実行
!python 01_basics/01_api_setup.py
```

---

## 📝 練習問題の進め方

1. `exercises/README.md` で問題の概要を確認
2. `exercises/exercise_XX.py` のテンプレートファイルを開く
3. `# TODO:` コメントの箇所を実装する
4. 実行して期待通りの出力が得られるか確認

---

## 💡 学習のヒント

- コードを読むだけでなく、実際に変更して動作を確認しましょう
- エラーが発生したら、エラーメッセージをよく読んで原因を特定しましょう
- わからないことは [Anthropic Docs](https://docs.anthropic.com/) を参照しましょう

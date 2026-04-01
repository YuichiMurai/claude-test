# 02_prompt_engineering - 応用編: Prompt Engineering

Claude API を使ったプロンプトエンジニアリングの応用テクニックを学ぶセクションです。

---

## 🎯 学習目標

このセクションを完了すると、以下ができるようになります：

- システムプロンプトを活用してClaudeの振る舞いをカスタマイズする
- Few-shot learning で高精度な分類・変換タスクを実装する
- Chain of Thought プロンプティングで複雑な推論を引き出す
- XML タグを使って入力データを構造化し、複数ドキュメントを処理する

## ⏱️ 学習時間の目安

**3〜4時間**（練習問題を含む）

## 📋 前提知識

- `01_basics/` の内容を理解していること
  - Claude API クライアントの初期化
  - 基本的なメッセージ送受信
  - システムプロンプトの基本的な使い方

---

## 📁 各ファイルの説明と学習順序

| 順序 | ファイル | 内容 |
|------|---------|------|
| 1 | `01_system_prompts.py` | システムプロンプトの設計・ペルソナ設定・制約の指定 |
| 2 | `02_few_shot_learning.py` | Few-shot learning・感情分析・カテゴリ分類 |
| 3 | `03_chain_of_thought.py` | Chain of Thought・数学問題・論理パズル |
| 4 | `04_xml_tags.py` | XML タグによる入力構造化・複数ドキュメント処理 |
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
!python 02_prompt_engineering/01_system_prompts.py
```

---

## 💡 Prompt Engineering の重要性

プロンプトエンジニアリングとは、AIモデルから最高の結果を引き出すために、入力（プロンプト）を設計・最適化する技術です。

### なぜ重要なのか？

| 観点 | 説明 |
|------|------|
| **品質向上** | 適切なプロンプトにより、回答の精度・一貫性が大幅に向上する |
| **コスト削減** | 無駄なトークンを削減し、API コストを最適化できる |
| **一貫性確保** | 同じ形式での出力を保証し、下流処理を安定させる |
| **安全性** | 不適切な応答を防ぎ、アプリケーションの安全性を高める |

### 主要なテクニック

1. **システムプロンプト設計**: Claudeの役割・制約・出力形式を定義
2. **Few-shot learning**: 例を示すことで期待する出力パターンを学習させる
3. **Chain of Thought**: 段階的に考えさせることで複雑な推論を可能にする
4. **XML タグ**: 構造化されたデータを明確に伝えるためにタグを活用する

---

## 📝 練習問題の進め方

1. `exercises/README.md` で問題の概要を確認
2. `exercises/exercise_XX.py` のテンプレートファイルを開く
3. `# TODO:` コメントの箇所を実装する
4. 実行して期待通りの出力が得られるか確認

---

## 🏆 CCA 試験での出題ポイント

Claude Certified Architect 試験では、以下のトピックが頻出です：

### システムプロンプト
- システムプロンプトとユーザープロンプトの役割の違い
- 効果的なシステムプロンプトの構成要素
- ペルソナ設定と制約の指定方法

### Few-shot Learning
- ゼロショット・ワンショット・Few-shot の違い
- 例の選び方と順序の影響
- 分類・変換タスクへの応用

### Chain of Thought
- CoT プロンプティングの効果と適用場面
- 「ステップバイステップで考えて」の効果
- 複雑な推論タスクでの活用

### XML タグ
- 構造化入力によるモデルのパフォーマンス向上
- 複数ドキュメントの処理方法
- タグの命名規則とベストプラクティス

---

## 💡 学習のヒント

- コードを読むだけでなく、プロンプトを変更して動作の違いを確認しましょう
- [Anthropic Prompt Library](https://docs.anthropic.com/ja/prompt-library/) に多くの実例があります
- [Prompt Engineering Guide](https://docs.anthropic.com/ja/docs/build-with-claude/prompt-engineering/overview) も参照してください

# 02_prompt_engineering - 応用編（プロンプトエンジニアリング）

Claude API を活用するためのプロンプトエンジニアリング技術を学ぶセクションです。

---

## 🎯 このセクションの学習目標

このセクションを完了すると、以下ができるようになります：

- 効果的なシステムプロンプトを設計・実装できる
- Few-shot learning によりClaudeの出力品質を向上させられる
- Chain of Thought プロンプティングで複雑な推論を実現できる
- XMLタグを使ったプロンプトの構造化ができる
- CCA試験で問われるプロンプトエンジニアリングの最重要概念を理解できる

## ⏱️ 学習時間の目安

**3〜4時間**（練習問題を含む）

## 📋 前提知識

- **01_basics/** の内容を理解していること
  - Anthropic APIクライアントの初期化
  - `messages.create()` の基本的な使い方
  - `system` プロンプトの概念
  - 会話履歴の管理

---

## 📁 各ファイルの説明と学習順序

| 順序 | ファイル | 内容 |
|------|---------|------|
| 1 | `01_system_prompts.py` | システムプロンプトの設計・ロールベース・トーン制御・出力形式指定 |
| 2 | `02_few_shot_learning.py` | Zero-shot vs Few-shot・感情分析・分類・テキスト要約 |
| 3 | `03_chain_of_thought.py` | Zero-shot CoT・Few-shot CoT・数学・論理・複雑な推論 |
| 4 | `04_xml_tags.py` | XMLタグによる構造化・ドキュメント処理・タスク定義 |

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
!python 02_prompt_engineering/01_system_prompts.py
```

---

## 💡 プロンプトエンジニアリングの重要性

プロンプトエンジニアリングとは、AIモデルから望む出力を引き出すためにプロンプト（入力テキスト）を設計・最適化する技術です。

### なぜ重要なのか？

| 理由 | 説明 |
|------|------|
| **品質向上** | 適切なプロンプトにより回答の精度・品質が大幅に向上する |
| **コスト削減** | 無駄なやり取りを減らし、トークン消費を最適化できる |
| **一貫性の確保** | 同じ形式・スタイルの出力を安定して得られる |
| **タスク特化** | 特定のユースケースに最適化された動作を実現できる |

### プロンプトエンジニアリングの主要技術

```
基本技術
├── システムプロンプト設計    ← 01_system_prompts.py
├── Few-shot Learning         ← 02_few_shot_learning.py
├── Chain of Thought (CoT)    ← 03_chain_of_thought.py
└── 構造化（XMLタグ）         ← 04_xml_tags.py

応用技術（他セクションで学習）
├── Constitutional AI
├── Tool Use / Function Calling
└── RAG (Retrieval-Augmented Generation)
```

---

## 🎓 CCA試験での出題ポイント

### 重要度の高いトピック

#### 1. システムプロンプト
- ✅ ロール定義の効果的な方法
- ✅ `system` パラメータと `messages` の使い分け
- ✅ トーンと出力形式の制御

#### 2. Few-shot Learning
- ✅ Zero-shot と Few-shot の違いと使い分け
- ✅ 良い例の選び方（多様性、明確さ）
- ✅ 例の数と品質のトレードオフ

#### 3. Chain of Thought
- ✅ 「ステップバイステップで考えてください」の効果
- ✅ CoT が有効なタスクの種類（数学、論理、多段階推論）
- ✅ Zero-shot CoT vs Few-shot CoT

#### 4. XMLタグによる構造化
- ✅ Anthropicが推奨するXMLタグの活用
- ✅ 複数ドキュメントの処理方法
- ✅ タスク定義と入力データの分離

### 試験対策チェックリスト

- [ ] システムプロンプトでClaudeの振る舞いを制御できる
- [ ] Few-shot の例を効果的に設計できる
- [ ] Chain of Thought で複雑な問題を解かせられる
- [ ] XMLタグでプロンプトを構造化できる
- [ ] 各技術のメリット・デメリットを説明できる
- [ ] 適切な技術を選択・組み合わせできる

---

## 📝 練習問題の進め方

このセクションには練習問題はありませんが、各ファイルのコードを実際に動かして変更してみることを推奨します。

### 推奨する学習方法

1. **コードを読む**: 各ファイルの日本語コメントを読みながら理解する
2. **実行する**: Google Colab でコードを実行して出力を確認する
3. **改変する**: プロンプトを変えて出力の変化を観察する
4. **比較する**: 技術あり・なしの出力を比較する

### 学習を深めるための改変例

```python
# 01_system_prompts.py を試す
# → system プロンプトの文言を変えて出力の変化を観察する

# 02_few_shot_learning.py を試す
# → 例の数（1-shot, 2-shot, 3-shot）を変えて精度の変化を確認する

# 03_chain_of_thought.py を試す
# → CoT あり・なしで複雑な問題を解かせて比較する

# 04_xml_tags.py を試す
# → XMLタグの有無でプロンプトの解釈がどう変わるか確認する
```

---

## 🔗 参考資料

- [Anthropic Prompt Engineering Guide](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview)
- [Claude API Documentation](https://docs.anthropic.com/en/api/getting-started)
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)

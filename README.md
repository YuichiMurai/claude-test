# Claude Certified Architect 試験対策ハンズオン

このリポジトリは、**Claude Certified Architect (CCA)** 試験対策のための包括的なPythonハンズオン教材です。

## 📖 試験概要

Claude Certified Architect (CCA) は、Anthropicが提供するClaude AIを活用したシステム設計・実装スキルを認定する資格です。

参考記事: [Claude Certified Architect (CCA) とは？](https://www.ai-souken.com/article/what-is-claude-certified-architect-cca-f)

### 試験で問われる主なスキル
- Claude APIの基本操作と理解
- 効果的なプロンプトエンジニアリング
- セキュアなアプリケーション設計
- スケーラブルなアーキテクチャ設計
- コスト最適化と運用設計

---

## 🗂️ ディレクトリ構成

```
claude-test/
├── README.md                    # このファイル
├── requirements.txt             # 必要なPythonパッケージ
├── .env.example                 # 環境変数テンプレート
├── .gitignore
├── 01_basics/                   # 基礎編（約2時間）
├── 02_prompt_engineering/       # 応用編（約3時間）
├── 03_secure_applications/      # 実践編（約4時間）
├── 04_architecture/             # アーキテクト編（約4時間）
└── mock_exam/                   # 模擬試験（各90分）
```

---

## 📚 学習の進め方（推奨順序）

| ステップ | セクション | 学習時間目安 | 難易度 |
|---------|-----------|------------|--------|
| 1 | 01_basics（基礎編） | 約2時間 | ⭐ 初級 |
| 2 | 02_prompt_engineering（応用編） | 約3時間 | ⭐⭐ 中級 |
| 3 | 03_secure_applications（実践編） | 約4時間 | ⭐⭐⭐ 中上級 |
| 4 | 04_architecture（アーキテクト編） | 約4時間 | ⭐⭐⭐⭐ 上級 |
| 5 | mock_exam（模擬試験） | 各90分 | ⭐⭐⭐⭐⭐ 総合 |

---

## 🚀 環境セットアップ手順

### 1. リポジトリのクローン
```bash
git clone https://github.com/YuichiMurai/claude-test.git
cd claude-test
```

### 2. Python仮想環境の作成
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

### 5. 動作確認
```bash
python 01_basics/01_api_setup.py
```

---

## 🔑 Anthropic API Keyの取得方法

1. [Anthropic Console](https://console.anthropic.com/) にアクセス
2. アカウントを作成またはログイン
3. 「API Keys」セクションで新しいAPIキーを作成
4. `.env`ファイルに設定：
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx
   ```

> ⚠️ **注意**: APIキーは絶対にGitにコミットしないでください！

---

## 📋 各セクションの説明

### 01_basics/（基礎編）
Claude APIの基本的な使い方を学びます。
- API接続の基本設定
- 初めてのリクエスト送信
- ストリーミングレスポンス
- 会話履歴の管理

### 02_prompt_engineering/（応用編）
効果的なプロンプト設計技術を習得します。
- システムプロンプトの設計
- Few-shot学習
- Chain-of-Thought推論
- XMLタグを使った構造化

### 03_secure_applications/（実践編）
セキュアなアプリケーション開発を学びます。
- 入力検証とサニタイゼーション
- 個人情報の検出とマスキング
- エラーハンドリングとリトライ
- レート制限対応
- トークン管理とコスト最適化

### 04_architecture/（アーキテクト編）
スケーラブルなシステム設計を学びます。
- キャッシング戦略
- 非同期処理
- モニタリングとロギング
- スケーラブルな設計パターン

### mock_exam/（模擬試験）
実際の試験に近い形式でスキルを試します。
- シナリオ1：カスタマーサポートチャットボット
- シナリオ2：ドキュメント要約システム
- シナリオ3：コンテンツ分類・モデレーションシステム

---

## 💡 試験対策のポイント

1. **APIの理解を深める**: パラメータ（temperature, max_tokens等）の効果を実際に試す
2. **プロンプト設計**: XMLタグ、Few-shot、CoTを使いこなす
3. **セキュリティ**: インジェクション攻撃、PII処理、入力検証を理解する
4. **コスト意識**: トークン管理、キャッシング、バッチ処理を活用する
5. **スケーラビリティ**: 非同期処理、負荷分散、監視の実装パターンを学ぶ
6. **エラーハンドリング**: リトライロジック、フォールバック戦略を実装できる

---

## ⚠️ 注意事項

- すべてのコードは**教育目的**であり、本番環境での使用前には適切なレビューが必要です
- APIキーは絶対にコミットしないでください（`.gitignore`で除外済み）
- コスト管理のため、実行時は小さな`max_tokens`から始めることを推奨します
- 各ファイルの実行には有効なAnthropic APIキーが必要です

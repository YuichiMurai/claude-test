# Google Colab セットアップガイド

Claude Certified Architect 試験対策ハンズオン教材を **Google Colab** で実行するための詳細ガイドです。

---

## ステップ 1: Colab Secrets の設定

### Colab Secrets とは？

Colab Secrets は Google Colab が提供するセキュアなシークレット管理機能です。
API Key などの機密情報をコードに直接書かずに安全に管理できます。

### 設定手順

1. **Google Colab** (https://colab.research.google.com/) を開く

2. 新しいノートブックを作成するか、既存のノートブックを開く

3. 左サイドバーの **🔑（鍵マーク）** アイコンをクリック
   - サイドバーが表示されていない場合は、左端のアイコンをクリックして展開

4. **「+ Add new secret」** ボタンをクリック

5. 以下の情報を入力：
   ```
   Name:  ANTHROPIC_API_KEY
   Value: sk-ant-xxxxxxxxxxxx（あなたのAPIキー）
   ```

6. **「Notebook access」** のトグルを **ON** にする
   - これにより、このノートブックからシークレットにアクセスできるようになります

7. **「Save」** をクリックして保存

### APIキーの安全な管理方法

```python
# ✅ 推奨: Colab Secretsを使用
from google.colab import userdata
import os

os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

# ❌ 非推奨: コードに直接書く（絶対にやらない！）
# os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-xxxxxxxxxxxx'
```

> ⚠️ **重要**: APIキーをコードに直接書いてGitHubにpushすると、キーが漏洩します。
> 必ずColab Secretsを使用してください。

---

## ステップ 2: パッケージのインストール

### 方法1: requirements.txtから直接インストール（推奨）

```python
# GitHubのrequirements.txtから直接インストール
!pip install -r https://raw.githubusercontent.com/YuichiMurai/claude-test/main/requirements.txt -q

print("✅ パッケージインストール完了！")
```

### 方法2: パッケージを直接インストール

```python
# 必要なパッケージを直接インストール
!pip install anthropic>=0.18.0 python-dotenv>=1.0.0 -q

print("✅ パッケージインストール完了！")
```

### インストール確認

```python
# インストールされたバージョンを確認
import anthropic
print(f"anthropic version: {anthropic.__version__}")
```

---

## ステップ 3: 最初のテスト実行

### 完全なセットアップコード

新しいノートブックで以下のセルを順番に実行してください：

#### セル1: パッケージインストール

```python
# パッケージをインストール
!pip install anthropic python-dotenv -q
print("✅ パッケージインストール完了！")
```

#### セル2: API Key設定

```python
# Colab SecretsからAPI Keyを取得
from google.colab import userdata
import os

os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')
print("✅ API Key設定完了！")
```

#### セル3: クライアント初期化

```python
# Anthropicクライアントを初期化
from anthropic import Anthropic

client = Anthropic()
print("✅ クライアント初期化完了！")
```

#### セル4: テスト実行

```python
# 簡単なメッセージを送信してテスト
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "こんにちは！一言で自己紹介してください。"}
    ]
)

print("Claudeの返答:")
print(message.content[0].text)
print("\n✅ テスト成功！学習を始めましょう！")
```

---

## トラブルシューティング

### よくあるエラーと解決方法

#### エラー1: `ModuleNotFoundError: No module named 'anthropic'`

**原因**: anthropicパッケージがインストールされていない

**解決方法**:
```python
!pip install anthropic -q
```

---

#### エラー2: `SecretNotFoundError` または `KeyError: 'ANTHROPIC_API_KEY'`

**原因**: Colab Secretsに `ANTHROPIC_API_KEY` が設定されていない

**解決方法**:
1. 左サイドバーの🔑アイコンをクリック
2. `ANTHROPIC_API_KEY` が存在するか確認
3. 存在しない場合は「+ Add new secret」で追加
4. 「Notebook access」のトグルがONになっているか確認

---

#### エラー3: `AuthenticationError: 401`

**原因**: APIキーが無効または期限切れ

**解決方法**:
1. [Anthropic Console](https://console.anthropic.com/) でAPIキーを確認
2. 新しいAPIキーを生成
3. Colab Secretsのキーを更新

---

#### エラー4: `RateLimitError: 429`

**原因**: APIの利用制限に達した

**解決方法**:
```python
import time

# リトライ処理の例
import anthropic

def safe_request(client, **kwargs):
    """レート制限に対応したリクエスト"""
    max_retries = 3
    for i in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if i < max_retries - 1:
                wait_time = 2 ** i  # 指数バックオフ
                print(f"レート制限。{wait_time}秒待機中...")
                time.sleep(wait_time)
            else:
                raise
```

---

#### エラー5: Colab セッションが切れた

**原因**: 長時間操作しないとセッションがタイムアウトする

**解決方法**:
- セッションが切れたら、すべてのセルを最初から再実行
- 「ランタイム」→「すべてのセルを実行」を使うと便利

---

## 便利なColab機能

### ファイルのアップロード

```python
from google.colab import files

# ファイルをアップロード
uploaded = files.upload()
```

### Google Drive のマウント

```python
from google.colab import drive

# Google Driveをマウント
drive.mount('/content/drive')

# マウント後のパス例
# /content/drive/MyDrive/claude-test/
```

### リポジトリのクローン

```python
# GitHubからリポジトリをクローン
!git clone https://github.com/YuichiMurai/claude-test.git

# ディレクトリを移動
%cd claude-test

# ファイル一覧を確認
!ls -la
```

---

## 次のステップ

セットアップが完了したら、`01_basics/` から学習を始めましょう！

```python
# 01_basics/ の内容を確認
!ls 01_basics/
```

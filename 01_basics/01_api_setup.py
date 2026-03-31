"""
01_api_setup.py - Claude API接続の基本設定

このファイルの目的:
- Anthropic Clientの初期化方法を学ぶ
- API Keyの安全な管理方法を理解する
- 接続テストを実施する

【Google Colabでの実行方法】
1. 最初にパッケージをインストール:
   !pip install anthropic python-dotenv -q

2. Colab Secretsを設定:
   - 左サイドバーの🔑アイコンをクリック
   - "Add new secret"をクリック
   - Name: ANTHROPIC_API_KEY
   - Value: あなたのAPIキーを貼り付け

3. このコードを実行
"""

import os
from anthropic import Anthropic


def setup_client() -> Anthropic:
    """
    Claude APIクライアントをセットアップする

    Returns:
        Anthropic: 初期化されたクライアント

    Raises:
        ValueError: API Keyが設定されていない場合
    """
    # Google Colabの場合
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
        print("✅ Colab SecretsからAPI Keyを取得しました")
    except ImportError:
        # ローカル環境の場合
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')
        print("✅ 環境変数からAPI Keyを取得しました")

    if not api_key:
        raise ValueError(
            "API Keyが設定されていません。\n"
            "Google Colabの場合: Colab Secretsに ANTHROPIC_API_KEY を設定してください\n"
            "ローカル環境の場合: .env ファイルに ANTHROPIC_API_KEY を設定してください"
        )

    # クライアントを初期化
    client = Anthropic(api_key=api_key)
    print("✅ Claude APIクライアントを初期化しました")

    return client


def test_connection(client: Anthropic) -> None:
    """
    API接続をテストする

    Args:
        client: Anthropicクライアント
    """
    try:
        # シンプルなリクエストで接続テスト
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Hello!"}
            ]
        )
        print("✅ API接続テスト成功！")
        print(f"レスポンス: {message.content[0].text}")

    except Exception as e:
        print(f"❌ API接続テスト失敗: {e}")
        raise


# 実行例
if __name__ == "__main__":
    print("=" * 50)
    print("Claude API セットアップ")
    print("=" * 50)

    # クライアントをセットアップ
    client = setup_client()

    # 接続テスト
    test_connection(client)

    print("\n✅ セットアップ完了！次のファイルに進んでください。")

"""
01_api_setup.py - Anthropic API接続の基本設定

このファイルでは以下を学びます：
- Anthropic Pythonクライアントの初期化
- 環境変数からのAPIキー読み込み
- 接続テストの実施
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def initialize_client() -> Anthropic:
    """
    Anthropicクライアントを初期化する。

    環境変数 ANTHROPIC_API_KEY からAPIキーを読み込み、
    クライアントインスタンスを返す。

    Returns:
        Anthropic: 初期化済みのAnthropicクライアント

    Raises:
        ValueError: APIキーが設定されていない場合
    """
    # .envファイルから環境変数を読み込む
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY が設定されていません。"
            ".envファイルを確認してください。"
        )

    # Anthropicクライアントを初期化
    # api_keyを明示的に渡すことも可能だが、環境変数から自動取得も可能
    client = Anthropic(api_key=api_key)
    return client


def test_connection(client: Anthropic) -> bool:
    """
    API接続をテストする。

    簡単なリクエストを送信して接続が正常か確認する。

    Args:
        client: 初期化済みのAnthropicクライアント

    Returns:
        bool: 接続成功時True
    """
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(f"✅ 接続成功！モデル: {response.model}")
        print(f"   レスポンス: {response.content[0].text[:50]}")
        return True
    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        return False


def main() -> None:
    """メイン処理：クライアント初期化と接続テスト。"""
    print("=== Anthropic API 接続テスト ===\n")

    try:
        client = initialize_client()
        print("✅ クライアント初期化成功\n")
        test_connection(client)
    except ValueError as e:
        print(f"❌ 設定エラー: {e}")


if __name__ == "__main__":
    main()

"""
02_first_request.py - 基本的なメッセージ送受信

このファイルの目的:
- Messages APIの基本的な使い方を学ぶ
- リクエストパラメータの意味を理解する
- レスポンスオブジェクトの構造を把握する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 01_basics/02_first_request.py
   または、コードをColabのセルに貼り付けて実行
"""

import os
from anthropic import Anthropic


def get_client() -> Anthropic:
    """
    APIクライアントを取得する（Colab・ローカル両対応）

    Returns:
        Anthropic: 初期化されたクライアント
    """
    try:
        from google.colab import userdata
        os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()

    return Anthropic()


def basic_request(client: Anthropic) -> None:
    """
    基本的なメッセージリクエストの例

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 基本的なリクエスト ---")

    # Messages APIの基本的な呼び出し
    message = client.messages.create(
        # モデルの指定
        # claude-3-5-sonnet-20241022: 高性能・バランス型（推奨）
        # claude-3-5-haiku-20241022: 高速・低コスト
        # claude-3-opus-20240229: 最高性能
        model="claude-3-5-sonnet-20241022",

        # 最大トークン数: レスポンスの最大長
        # 1トークン ≈ 0.75単語（英語の場合）
        # 日本語は1文字 ≈ 1-2トークン
        max_tokens=1024,

        # メッセージのリスト: 会話の履歴
        messages=[
            {
                "role": "user",           # ユーザーのメッセージ
                "content": "Pythonとは何ですか？3文で簡潔に説明してください。"
            }
        ]
    )

    # レスポンスの内容を表示
    print(f"Claudeの回答:\n{message.content[0].text}")


def request_with_system(client: Anthropic) -> None:
    """
    systemプロンプトを使ったリクエストの例

    systemプロンプトはClaudeの振る舞いや役割を定義するために使用します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- systemプロンプト付きリクエスト ---")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,

        # systemプロンプト: Claudeの役割・振る舞いを定義
        system="あなたはプログラミング初心者向けの優しい先生です。"
               "専門用語を避け、分かりやすい言葉で説明してください。"
               "例えを使って説明することを心がけてください。",

        messages=[
            {"role": "user", "content": "APIとは何ですか？"}
        ]
    )

    print(f"Claudeの回答:\n{message.content[0].text}")


def inspect_response(client: Anthropic) -> None:
    """
    レスポンスオブジェクトの詳細を確認する

    Args:
        client: Anthropicクライアント
    """
    print("\n--- レスポンスオブジェクトの詳細 ---")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "1+1は？"}
        ]
    )

    # レスポンスオブジェクトの各フィールドを確認
    print(f"id: {message.id}")
    print(f"type: {message.type}")
    print(f"role: {message.role}")
    print(f"model: {message.model}")
    print(f"stop_reason: {message.stop_reason}")

    # トークン使用量: APIコストの計算に使用
    print(f"\nトークン使用量:")
    print(f"  input_tokens: {message.usage.input_tokens}")
    print(f"  output_tokens: {message.usage.output_tokens}")

    # コンテンツ
    print(f"\nコンテンツ:")
    for i, block in enumerate(message.content):
        print(f"  [{i}] type: {block.type}, text: {block.text}")


def different_parameters(client: Anthropic) -> None:
    """
    異なるパラメータの効果を確認する

    Args:
        client: Anthropicクライアント
    """
    print("\n--- パラメータの効果比較 ---")

    question = "今日の天気はどうですか？"

    # temperature: 応答のランダム性（0.0=決定的, 1.0=ランダム）
    # デフォルト値は1.0
    for temp in [0.0, 1.0]:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            # temperature=temp,  # 現在のAPIではサポート外の場合あり
            messages=[{"role": "user", "content": question}]
        )
        print(f"\n質問: {question}")
        print(f"回答: {message.content[0].text[:100]}...")
        break  # 1回だけ実行


if __name__ == "__main__":
    print("=" * 50)
    print("基本的なメッセージ送受信")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    basic_request(client)
    request_with_system(client)
    inspect_response(client)
    different_parameters(client)

    print("\n✅ 完了！次は03_streaming.pyに進んでください。")

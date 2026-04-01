"""
03_streaming.py - ストリーミングレスポンスの実装

このファイルの目的:
- ストリーミングAPIの使い方を学ぶ
- リアルタイムでテキストを表示する方法を理解する
- Google Colab環境での出力方法を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 01_basics/03_streaming.py
   または、コードをColabのセルに貼り付けて実行

【ストリーミングとは？】
通常のAPIリクエストはレスポンス全体が完成してから返ってきます。
ストリーミングを使うと、生成されたテキストをリアルタイムで受け取れます。
これにより、ユーザー体験が大幅に向上します。
"""

import os
import sys
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


def basic_streaming(client: Anthropic) -> None:
    """
    基本的なストリーミングの例

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 基本的なストリーミング ---")
    print("Claudeの回答（リアルタイム）:")
    print("-" * 40)

    # stream=True でストリーミングを有効化
    # with文を使うことでリソースが確実に解放される
    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": "Pythonでリスト内包表記の使い方を3つの例で説明してください。"}
        ]
    ) as stream:
        # テキストが生成されるたびにチャンクが届く
        for text in stream.text_stream:
            # end="" で改行を抑制、flush=True でバッファをすぐに出力
            print(text, end="", flush=True)

    # ストリーミング完了後に改行
    print("\n" + "-" * 40)

    # ストリーミング完了後にメッセージ全体を取得することも可能
    final_message = stream.get_final_message()
    print(f"\n[メタデータ]")
    print(f"stop_reason: {final_message.stop_reason}")
    print(f"入力トークン: {final_message.usage.input_tokens}")
    print(f"出力トークン: {final_message.usage.output_tokens}")


def streaming_with_system(client: Anthropic) -> None:
    """
    systemプロンプト付きストリーミングの例

    Args:
        client: Anthropicクライアント
    """
    print("\n--- systemプロンプト付きストリーミング ---")
    print("Claudeの回答（リアルタイム）:")
    print("-" * 40)

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system="あなたはプロのプログラミング講師です。"
               "コードは必ず実行可能な完全な形で提示してください。"
               "説明は簡潔明瞭にしてください。",
        messages=[
            {"role": "user", "content": "Pythonで辞書を使った簡単なキャッシュの実装例を見せてください。"}
        ]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

    print("\n" + "-" * 40)


def streaming_collect_full_text(client: Anthropic) -> str:
    """
    ストリーミングしながらテキスト全体を収集する例

    Args:
        client: Anthropicクライアント

    Returns:
        str: 収集した全テキスト
    """
    print("\n--- ストリーミングしながらテキストを収集 ---")
    print("Claudeの回答（リアルタイム）:")
    print("-" * 40)

    collected_text = ""

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[
            {"role": "user", "content": "「機械学習」を一言で説明してください。"}
        ]
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
            collected_text += text  # テキストを収集

    print("\n" + "-" * 40)
    print(f"\n[収集したテキスト全体]")
    print(f'"{collected_text}"')
    print(f"文字数: {len(collected_text)}")

    return collected_text


def colab_friendly_streaming(client: Anthropic) -> None:
    """
    Google Colab環境に最適化したストリーミング表示

    Colabでは通常のflush=Trueが効かない場合があるため、
    IPython.displayを使って表示する方法も示します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Colab対応ストリーミング ---")

    # Colabかどうかを確認
    is_colab = False
    try:
        import google.colab  # noqa: F401
        is_colab = True
    except ImportError:
        pass

    if is_colab:
        # Colab環境: IPython.displayを使って更新表示
        from IPython.display import display, clear_output
        import time

        print("IPython displayを使用したストリーミング表示:")
        full_text = ""

        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[
                {"role": "user", "content": "AIとは何か、2文で説明してください。"}
            ]
        ) as stream:
            for text in stream.text_stream:
                full_text += text
                clear_output(wait=True)
                print(full_text)
                time.sleep(0.01)
    else:
        # 通常環境: 標準的なストリーミング
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            messages=[
                {"role": "user", "content": "AIとは何か、2文で説明してください。"}
            ]
        ) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
        print()


if __name__ == "__main__":
    print("=" * 50)
    print("ストリーミングレスポンスの実装")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    basic_streaming(client)
    streaming_with_system(client)
    streaming_collect_full_text(client)

    print("\n✅ 完了！次は04_message_history.pyに進んでください。")

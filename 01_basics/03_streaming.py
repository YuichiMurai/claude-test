"""
03_streaming.py - ストリーミングレスポンス

このファイルでは以下を学びます：
- ストリーミングレスポンスの実装
- リアルタイム表示
- ストリーミングのメリットとユースケース
"""

import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv


def stream_response(client: Anthropic, user_message: str) -> str:
    """
    ストリーミングでレスポンスを受信してリアルタイム表示する。

    ストリーミングのメリット:
    - ユーザーが最初のトークンをすぐに見られる（体感速度向上）
    - 長い回答でも待ち時間が少ない
    - 必要に応じて途中でキャンセル可能

    Args:
        client: Anthropicクライアント
        user_message: ユーザーメッセージ

    Returns:
        str: 完全なレスポンステキスト
    """
    full_text = ""

    # stream=True でストリーミングモードを有効化
    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        # text_stream でテキストチャンクを順次受信
        for text_chunk in stream.text_stream:
            print(text_chunk, end="", flush=True)
            full_text += text_chunk

    print()  # 改行
    return full_text


def stream_with_metadata(client: Anthropic, user_message: str) -> dict:
    """
    ストリーミングしながらメタデータも取得する。

    Args:
        client: Anthropicクライアント
        user_message: ユーザーメッセージ

    Returns:
        dict: テキストとメタデータ
    """
    full_text = ""

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system="簡潔に日本語で回答してください。",
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for text_chunk in stream.text_stream:
            print(text_chunk, end="", flush=True)
            full_text += text_chunk

        # ストリーム完了後にメタデータを取得
        final_message = stream.get_final_message()

    print()
    return {
        "text": full_text,
        "input_tokens": final_message.usage.input_tokens,
        "output_tokens": final_message.usage.output_tokens,
    }


def main() -> None:
    """メイン処理：ストリーミングの実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== ストリーミングレスポンス ===\n")
    print("質問: Pythonの主な特徴を説明してください。\n")
    print("回答（リアルタイム表示）:")
    stream_response(client, "Pythonの主な特徴を5つ説明してください。")

    print("\n=== メタデータ付きストリーミング ===\n")
    print("質問: AIの倫理的課題とは？\n")
    print("回答（リアルタイム表示）:")
    result = stream_with_metadata(client, "AIの倫理的課題を3つ挙げてください。")
    print(f"\n入力トークン: {result['input_tokens']}")
    print(f"出力トークン: {result['output_tokens']}")


if __name__ == "__main__":
    main()

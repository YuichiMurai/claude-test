"""
04_message_history.py - 会話履歴の管理

このファイルでは以下を学びます：
- 会話履歴の管理方法
- マルチターン会話の実装
- コンテキストウィンドウの管理
"""

import os
from typing import List
from anthropic import Anthropic
from dotenv import load_dotenv


MessageHistory = List[dict]


def create_conversation() -> MessageHistory:
    """空の会話履歴を作成する。"""
    return []


def add_user_message(history: MessageHistory, content: str) -> MessageHistory:
    """会話履歴にユーザーメッセージを追加する。"""
    history.append({"role": "user", "content": content})
    return history


def send_and_record(
    client: Anthropic,
    history: MessageHistory,
    system_prompt: str = "",
) -> str:
    """
    メッセージを送信し、レスポンスを履歴に記録する。

    Args:
        client: Anthropicクライアント
        history: 会話履歴
        system_prompt: システムプロンプト

    Returns:
        str: Claudeの回答テキスト
    """
    kwargs = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 1024,
        "messages": history,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    response = client.messages.create(**kwargs)
    assistant_text = response.content[0].text

    # アシスタントの返答を履歴に追加
    history.append({"role": "assistant", "content": assistant_text})
    return assistant_text


def chat(
    client: Anthropic,
    history: MessageHistory,
    user_input: str,
    system_prompt: str = "",
) -> str:
    """
    会話を1ターン進める。

    Args:
        client: Anthropicクライアント
        history: 会話履歴（更新される）
        user_input: ユーザーの入力
        system_prompt: システムプロンプト

    Returns:
        str: Claudeの回答
    """
    add_user_message(history, user_input)
    return send_and_record(client, history, system_prompt)


def trim_history(history: MessageHistory, max_turns: int = 10) -> MessageHistory:
    """
    会話履歴が長くなりすぎた場合にトリミングする。

    コンテキストウィンドウの制限に対応するため、
    古い会話を削除して最新のものだけ保持する。

    Args:
        history: 会話履歴
        max_turns: 保持するターン数の最大値

    Returns:
        MessageHistory: トリミングされた履歴
    """
    # 1ターン = user + assistant で2エントリ
    max_messages = max_turns * 2
    if len(history) > max_messages:
        return history[-max_messages:]
    return history


def main() -> None:
    """メイン処理：マルチターン会話のデモ。"""
    load_dotenv()
    client = Anthropic()

    system_prompt = "あなたは親切なPythonの先生です。分かりやすく教えてください。"

    print("=== マルチターン会話のデモ ===\n")
    history: MessageHistory = create_conversation()

    # ターン1
    user1 = "Pythonのリストとタプルの違いを教えてください。"
    print(f"ユーザー: {user1}")
    response1 = chat(client, history, user1, system_prompt)
    print(f"Claude: {response1}\n")

    # ターン2（前の文脈を参照）
    user2 = "どちらを使うべきか判断する基準は？"
    print(f"ユーザー: {user2}")
    response2 = chat(client, history, user2, system_prompt)
    print(f"Claude: {response2}\n")

    # ターン3
    user3 = "具体的なコード例を見せてください。"
    print(f"ユーザー: {user3}")
    response3 = chat(client, history, user3, system_prompt)
    print(f"Claude: {response3}\n")

    print(f"会話履歴のターン数: {len(history) // 2}")


if __name__ == "__main__":
    main()

"""
02_first_request.py - 初めてのリクエスト

このファイルでは以下を学びます：
- 基本的なメッセージ送信
- レスポンスの解析
- モデルパラメータの説明（temperature, max_tokensなど）
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def send_basic_request(client: Anthropic, user_message: str) -> str:
    """
    基本的なメッセージを送信してレスポンスを返す。

    Args:
        client: Anthropicクライアント
        user_message: ユーザーからのメッセージ

    Returns:
        str: Claudeからのレスポンステキスト
    """
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        # max_tokens: 生成する最大トークン数（必須）
        max_tokens=1024,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # レスポンスの構造:
    # response.id          - メッセージID
    # response.model       - 使用したモデル名
    # response.content     - コンテンツブロックのリスト
    # response.usage       - トークン使用量
    # response.stop_reason - 停止理由（end_turn, max_tokens等）
    return response.content[0].text


def send_request_with_params(client: Anthropic, user_message: str) -> dict:
    """
    各種パラメータを設定してリクエストを送信する。

    主なパラメータの説明:
    - model: 使用するモデル（claude-3-5-sonnet-20241022等）
    - max_tokens: 最大出力トークン数（必須、コスト管理に重要）
    - temperature: 創造性の度合い（0.0〜1.0、デフォルト1.0）
                   0に近いほど決定的、1に近いほど多様な回答
    - system: システムプロンプト（Claudeの振る舞いを定義）
    - stop_sequences: 生成を停止するシーケンスのリスト

    Args:
        client: Anthropicクライアント
        user_message: ユーザーメッセージ

    Returns:
        dict: レスポンスの詳細情報
    """
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        # temperature=0.0: 一貫した回答が必要な場合（分類、抽出等）
        # temperature=1.0: 創造的な回答が必要な場合（文章生成等）
        temperature=0.7,
        system="あなたは親切な日本語アシスタントです。簡潔に回答してください。",
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    return {
        "text": response.content[0].text,
        "model": response.model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }


def main() -> None:
    """メイン処理：様々なリクエスト方法を実演する。"""
    load_dotenv()
    client = Anthropic()

    print("=== 基本リクエスト ===\n")

    # シンプルなリクエスト
    text = send_basic_request(client, "Pythonとは何ですか？一文で説明してください。")
    print(f"回答: {text}\n")

    print("=== パラメータ付きリクエスト ===\n")

    # 詳細情報付きリクエスト
    result = send_request_with_params(client, "機械学習の活用例を3つ教えてください。")
    print(f"回答: {result['text']}")
    print(f"\n--- メタデータ ---")
    print(f"モデル: {result['model']}")
    print(f"入力トークン: {result['input_tokens']}")
    print(f"出力トークン: {result['output_tokens']}")
    print(f"停止理由: {result['stop_reason']}")


if __name__ == "__main__":
    main()

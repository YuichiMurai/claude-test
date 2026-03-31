"""
exercise_03.py - 練習問題3: ストリーミングを使ったリアルタイム翻訳

【課題】
ストリーミングAPIを使って、入力テキストをリアルタイムで翻訳するシステムを実装してください。
翻訳結果が1文字ずつ表示される様子を体験します。

【学習目標】
- ストリーミングAPIの使い方を習得する
- リアルタイム表示の実装方法を理解する
- システムプロンプトによるロール設定を学ぶ

【参考ファイル】
- 01_basics/03_streaming.py: ストリーミングレスポンスの実装
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def translate_streaming(
    client: Anthropic,
    text: str,
    target_language: str,
) -> str:
    """
    テキストをストリーミングでリアルタイム翻訳する。

    【TODO】
    以下を実装してください：
    1. client.messages.stream() を使ってストリーミングを有効化する
    2. システムプロンプトで翻訳専門家のロールを設定する
       - 翻訳のみ出力し、説明や前置きを含めない
       - 指定された言語に翻訳する
    3. ストリーミングで受信したテキストチャンクをリアルタイム表示する
       （print(text_chunk, end="", flush=True) を使用）
    4. 完全な翻訳テキストを返す

    Args:
        client: Anthropicクライアント
        text: 翻訳するテキスト
        target_language: 翻訳先言語（例: "英語", "日本語", "フランス語"）

    Returns:
        str: 翻訳されたテキスト全体
    """
    # --- ここから実装 ---
    system_prompt = (
        f"あなたはプロの翻訳者です。"
        f"ユーザーが入力したテキストを{target_language}に翻訳してください。"
        f"翻訳文のみを出力し、説明や前置き、補足は一切含めないでください。"
    )

    full_text = ""

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": text}],
    ) as stream:
        for text_chunk in stream.text_stream:
            print(text_chunk, end="", flush=True)
            full_text += text_chunk

    print()  # 改行
    return full_text
    # --- ここまで実装 ---


def translate_multiple(
    client: Anthropic,
    texts: list,
    target_language: str,
) -> list:
    """
    複数のテキストを順次ストリーミング翻訳する。

    【TODO】
    以下を実装してください：
    1. 空の結果リストを作成する
    2. texts の各テキストに対して translate_streaming() を呼び出す
    3. 翻訳結果をリストに追加して返す

    Args:
        client: Anthropicクライアント
        texts: 翻訳するテキストのリスト
        target_language: 翻訳先言語

    Returns:
        list: 翻訳結果のリスト
    """
    # --- ここから実装 ---
    results = []
    for text in texts:
        translated = translate_streaming(client, text, target_language)
        results.append(translated)
    return results
    # --- ここまで実装 ---


def main() -> None:
    """メイン処理：日英・英日のリアルタイム翻訳を実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== 練習問題3: リアルタイム翻訳システム ===\n")

    # 日本語 → 英語
    ja_texts = [
        "人工知能は私たちの生活を大きく変えています。",
        "機械学習モデルは大量のデータから学習します。",
    ]

    print("【日本語 → 英語】\n")
    for text in ja_texts:
        print(f"原文: {text}")
        print("翻訳（リアルタイム）: ", end="")
        translate_streaming(client, text, "英語")
        print()

    # 英語 → 日本語
    en_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Cloud computing enables on-demand access to shared resources.",
    ]

    print("【英語 → 日本語】\n")
    for text in en_texts:
        print(f"原文: {text}")
        print("翻訳（リアルタイム）: ", end="")
        translate_streaming(client, text, "日本語")
        print()

    # 複数テキストの一括翻訳
    print("【複数テキストの一括翻訳（日本語 → 英語）】\n")
    batch_texts = [
        "今日は晴れています。",
        "プログラミングは楽しいです。",
        "技術の進歩は止まりません。",
    ]

    print("翻訳するテキスト:")
    for i, text in enumerate(batch_texts, 1):
        print(f"  {i}. {text}")
    print()

    translations = translate_multiple(client, batch_texts, "英語")

    print("翻訳結果:")
    for i, (original, translated) in enumerate(zip(batch_texts, translations), 1):
        print(f"  {i}. {original}")
        print(f"     → {translated}")


if __name__ == "__main__":
    main()

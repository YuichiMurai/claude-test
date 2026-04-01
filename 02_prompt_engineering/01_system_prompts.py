"""
01_system_prompts.py - システムプロンプトの設計

このファイルの目的:
- システムプロンプトでClaudeの振る舞いをカスタマイズする方法を学ぶ
- ペルソナ設定・制約・出力形式の指定方法を理解する
- 目的別のシステムプロンプト設計パターンを習得する

【Google Colabでの実行方法】
1. 最初にこれを実行:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/01_system_prompts.py
   または、コードをColabのセルに貼り付けて実行

【CCA試験ポイント】
- システムプロンプトはユーザーメッセージより高い優先度を持つ
- ペルソナ・制約・出力形式を明確に定義することが重要
- 一貫した振る舞いを保証するために使用する
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


def demonstrate_persona(client: Anthropic) -> None:
    """
    ペルソナ設定の例

    システムプロンプトでClaudeに特定の役割・専門性・個性を与える。
    同じ質問でも、ペルソナによって回答スタイルが大きく変わる。

    Args:
        client: Anthropicクライアント
    """
    print("\n" + "=" * 60)
    print("ペルソナ設定の例")
    print("=" * 60)

    question = "機械学習とは何ですか？"

    personas = [
        {
            "name": "小学生向け先生",
            "system": (
                "あなたは小学生に分かりやすく説明することが得意な先生です。"
                "難しい言葉は使わず、身近な例えを使って説明してください。"
                "絵文字を適度に使い、楽しく学べる雰囲気を作ってください。"
            ),
        },
        {
            "name": "エンジニア向け専門家",
            "system": (
                "あなたはML/AIエンジニア向けの技術的なアドバイザーです。"
                "専門用語を適切に使い、数学的な背景も含めて説明してください。"
                "実装上の考慮点やトレードオフも言及してください。"
            ),
        },
    ]

    for persona in personas:
        print(f"\n【ペルソナ: {persona['name']}】")
        print(f"質問: {question}")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            system=persona["system"],
            messages=[
                {"role": "user", "content": question}
            ]
        )

        print(f"回答:\n{message.content[0].text}")


def demonstrate_constraints(client: Anthropic) -> None:
    """
    制約の指定例

    システムプロンプトで応答に制約をかける。
    出力形式・長さ・内容の範囲などを制御できる。

    Args:
        client: Anthropicクライアント
    """
    print("\n" + "=" * 60)
    print("制約の指定例")
    print("=" * 60)

    # 出力形式を JSON に制限する例
    system_json = """あなたはテキスト分析アシスタントです。
ユーザーが入力したテキストを分析し、必ず以下のJSON形式のみで応答してください。

{
  "sentiment": "positive/negative/neutral のいずれか",
  "confidence": 0.0〜1.0 の数値,
  "keywords": ["キーワード1", "キーワード2"],
  "summary": "1文での要約"
}

JSON以外の文字は絶対に出力しないでください。"""

    text = "今日は天気が良く、新しいプロジェクトも順調に進んでいます。とても充実した一日でした。"

    print(f"分析対象テキスト: {text}")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        system=system_json,
        messages=[
            {"role": "user", "content": text}
        ]
    )

    print(f"\nJSON形式の分析結果:\n{message.content[0].text}")


def demonstrate_output_format(client: Anthropic) -> None:
    """
    出力形式の制御例

    システムプロンプトで特定のフォーマットでの出力を指示する。
    マークダウン・番号付きリスト・表形式など様々な形式を制御できる。

    Args:
        client: Anthropicクライアント
    """
    print("\n" + "=" * 60)
    print("出力形式の制御例")
    print("=" * 60)

    # 構造化された報告書形式での出力を指示
    system_report = """あなたは技術調査のアナリストです。
情報を求められたとき、必ず以下の構造で回答してください：

## 概要
（2〜3文で簡潔に）

## 主要なポイント
1. （最重要ポイント）
2. （2番目のポイント）
3. （3番目のポイント）

## 注意事項
（注意すべき点や制限事項）

上記の構造以外での回答はしないでください。"""

    topic = "Pythonの非同期処理（asyncio）について"

    print(f"調査トピック: {topic}")

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system=system_report,
        messages=[
            {"role": "user", "content": topic}
        ]
    )

    print(f"\n構造化された回答:\n{message.content[0].text}")


def demonstrate_multilingual_support(client: Anthropic) -> None:
    """
    多言語対応の例

    システムプロンプトで応答言語を制御する。
    ユーザーの言語に関わらず、特定の言語で応答させることができる。

    Args:
        client: Anthropicクライアント
    """
    print("\n" + "=" * 60)
    print("多言語対応の例")
    print("=" * 60)

    # 常に日本語で応答するよう指定
    system_japanese = (
        "You are a helpful assistant. "
        "Always respond in Japanese, regardless of the language used in the query. "
        "Be concise and friendly."
    )

    questions = [
        "What is Python?",           # 英語の質問
        "Pythonとは何ですか？",       # 日本語の質問
    ]

    for q in questions:
        print(f"\n質問（{('英語' if q[0].isascii() else '日本語')}）: {q}")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=128,
            system=system_japanese,
            messages=[{"role": "user", "content": q}]
        )

        print(f"回答（常に日本語）: {message.content[0].text}")


if __name__ == "__main__":
    print("=" * 60)
    print("システムプロンプトの設計")
    print("=" * 60)

    # クライアントを初期化
    client = get_client()

    # 各デモを実行
    demonstrate_persona(client)
    demonstrate_constraints(client)
    demonstrate_output_format(client)
    demonstrate_multilingual_support(client)

    print("\n✅ 完了！次は02_few_shot_learning.pyに進んでください。")

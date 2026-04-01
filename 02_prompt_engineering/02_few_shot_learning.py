"""
02_few_shot_learning.py - Few-shot Learning の実装

このファイルの目的:
- Few-shot learning（少数例学習）の概念と実装方法を学ぶ
- 例を示すことで期待する出力パターンをClaudeに学習させる
- 感情分析・カテゴリ分類への応用を習得する

【Google Colabでの実行方法】
1. 最初にこれを実行:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/02_few_shot_learning.py
   または、コードをColabのセルに貼り付けて実行

【CCA試験ポイント】
- ゼロショット: 例なしでタスクを指示
- ワンショット: 1つの例を提示
- Few-shot: 複数の例（通常3〜5個）を提示
- 例の選び方・多様性・順序がパフォーマンスに影響する
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


def zero_shot_sentiment(client: Anthropic, text: str) -> str:
    """
    ゼロショット感情分析

    例を一切示さずに感情分析を依頼する。
    シンプルだが、出力形式が不安定になる場合がある。

    Args:
        client: Anthropicクライアント
        text: 分析対象テキスト

    Returns:
        str: 感情分析結果
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=64,
        messages=[
            {
                "role": "user",
                "content": f"次のテキストの感情を分析してください: {text}"
            }
        ]
    )
    return message.content[0].text


def few_shot_sentiment(client: Anthropic, text: str) -> str:
    """
    Few-shot 感情分析

    複数の例を示すことで、一貫した形式の出力を得る。
    「positive / negative / neutral」という特定ラベルで返すよう誘導できる。

    Args:
        client: Anthropicクライアント
        text: 分析対象テキスト

    Returns:
        str: 感情ラベル（positive/negative/neutral）
    """
    # Few-shot の例をメッセージとして構築する
    # 各例は user（入力）と assistant（期待する出力）のペアで表現する
    messages = [
        # 例1: ポジティブな例
        {
            "role": "user",
            "content": "テキスト: 今日は最高の天気で、友達とピクニックを楽しみました！\n感情:"
        },
        {
            "role": "assistant",
            "content": "positive"
        },
        # 例2: ネガティブな例
        {
            "role": "user",
            "content": "テキスト: 電車が遅延して大事な会議に遅刻してしまいました。最悪です。\n感情:"
        },
        {
            "role": "assistant",
            "content": "negative"
        },
        # 例3: ニュートラルな例
        {
            "role": "user",
            "content": "テキスト: 今日の会議は9時から11時まで行われる予定です。\n感情:"
        },
        {
            "role": "assistant",
            "content": "neutral"
        },
        # 実際のタスク
        {
            "role": "user",
            "content": f"テキスト: {text}\n感情:"
        }
    ]

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16,
        messages=messages
    )
    return message.content[0].text.strip()


def few_shot_category_classification(client: Anthropic, text: str) -> str:
    """
    Few-shot カテゴリ分類

    サポートチケットをカテゴリ分類する実用的な例。
    Few-shot で具体的なカテゴリラベルを学習させる。

    カテゴリ: billing（請求）/ technical（技術）/ account（アカウント）/ other（その他）

    Args:
        client: Anthropicクライアント
        text: 分類対象のサポートチケットテキスト

    Returns:
        str: カテゴリラベル
    """
    messages = [
        # 例1: 請求関連
        {
            "role": "user",
            "content": (
                "チケット: 先月の請求書に見覚えのない料金が含まれています。"
                "確認と返金をお願いします。\nカテゴリ:"
            )
        },
        {"role": "assistant", "content": "billing"},

        # 例2: 技術的な問題
        {
            "role": "user",
            "content": (
                "チケット: アプリがクラッシュして起動できません。"
                "エラーコード: 0x80004005\nカテゴリ:"
            )
        },
        {"role": "assistant", "content": "technical"},

        # 例3: アカウント関連
        {
            "role": "user",
            "content": (
                "チケット: パスワードを忘れてしまい、"
                "リセットメールが届きません。\nカテゴリ:"
            )
        },
        {"role": "assistant", "content": "account"},

        # 例4: その他
        {
            "role": "user",
            "content": (
                "チケット: 御社のサービスに大変満足しています。"
                "ありがとうございました。\nカテゴリ:"
            )
        },
        {"role": "assistant", "content": "other"},

        # 実際のタスク
        {
            "role": "user",
            "content": f"チケット: {text}\nカテゴリ:"
        }
    ]

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16,
        messages=messages
    )
    return message.content[0].text.strip()


def few_shot_format_conversion(client: Anthropic, address: str) -> str:
    """
    Few-shot フォーマット変換

    住所の表記形式を変換する例。
    Few-shot で入出力のフォーマットパターンを示す。

    Args:
        client: Anthropicクライアント
        address: 変換対象の住所

    Returns:
        str: 変換後の住所（英語表記）
    """
    messages = [
        # 例1
        {
            "role": "user",
            "content": "住所（日本語）: 東京都渋谷区渋谷1-1-1\n住所（英語）:"
        },
        {
            "role": "assistant",
            "content": "1-1-1 Shibuya, Shibuya-ku, Tokyo, Japan"
        },
        # 例2
        {
            "role": "user",
            "content": "住所（日本語）: 大阪府大阪市北区梅田2-5-10\n住所（英語）:"
        },
        {
            "role": "assistant",
            "content": "2-5-10 Umeda, Kita-ku, Osaka-shi, Osaka, Japan"
        },
        # 実際のタスク
        {
            "role": "user",
            "content": f"住所（日本語）: {address}\n住所（英語）:"
        }
    ]

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=128,
        messages=messages
    )
    return message.content[0].text.strip()


if __name__ == "__main__":
    print("=" * 60)
    print("Few-shot Learning の実装")
    print("=" * 60)

    client = get_client()

    # --- 感情分析の比較 ---
    print("\n【感情分析: ゼロショット vs Few-shot の比較】")

    test_texts = [
        "新しいプロジェクトが成功して、チーム全員で喜びました！",
        "システム障害でデータが失われ、一週間分の作業が無駄になりました。",
        "明日の定例ミーティングは10時から開始します。",
    ]

    for text in test_texts:
        print(f"\n対象: {text}")
        zero = zero_shot_sentiment(client, text)
        few = few_shot_sentiment(client, text)
        print(f"  ゼロショット: {zero[:80]}")
        print(f"  Few-shot   : {few}")

    # --- カテゴリ分類 ---
    print("\n\n【サポートチケット分類（Few-shot）】")

    tickets = [
        "クレジットカードへの請求が二重になっています。",
        "ログインしようとするとエラーが表示されます。",
        "メールアドレスを変更したいのですが方法が分かりません。",
    ]

    for ticket in tickets:
        category = few_shot_category_classification(client, ticket)
        print(f"チケット: {ticket}")
        print(f"  分類: {category}\n")

    # --- フォーマット変換 ---
    print("\n【住所フォーマット変換（Few-shot）】")

    addresses = [
        "神奈川県横浜市中区山下町1番地",
        "北海道札幌市中央区大通西3丁目",
    ]

    for addr in addresses:
        converted = few_shot_format_conversion(client, addr)
        print(f"日本語: {addr}")
        print(f"英語  : {converted}\n")

    print("✅ 完了！次は03_chain_of_thought.pyに進んでください。")

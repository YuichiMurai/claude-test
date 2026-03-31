"""
02_few_shot_learning.py - Few-shot学習

このファイルでは以下を学びます：
- Few-shot learningの基本概念と実装
- 例示（examples）を使った精度向上
- 感情分析やカテゴリ分類への応用
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def zero_shot_classification(client: Anthropic, text: str) -> str:
    """
    Zero-shot分類: 例示なしで分類を行う（比較用）。

    Few-shotと比較するためのベースラインとして使用。

    Args:
        client: Anthropicクライアント
        text: 分類するテキスト

    Returns:
        str: 分類結果
    """
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=64,
        system="テキストの感情を「ポジティブ」「ネガティブ」「ニュートラル」のいずれかで分類してください。分類ラベルのみ出力してください。",
        messages=[{"role": "user", "content": text}],
    )
    return response.content[0].text.strip()


def few_shot_sentiment_analysis(client: Anthropic, text: str) -> str:
    """
    Few-shot感情分析: 例示を使って感情を分類する。

    Few-shotでは、入力の前に具体的な例（入力と正解のペア）を提示することで、
    モデルが期待する出力形式と判断基準を学習できる。

    Args:
        client: Anthropicクライアント
        text: 感情分析するテキスト

    Returns:
        str: 感情ラベル（ポジティブ/ネガティブ/ニュートラル）
    """
    # Few-shotの例示をユーザーメッセージとアシスタントメッセージの形式で構築
    # この形式により、期待する出力パターンを明確に示す
    messages = [
        # 例1: ポジティブ
        {"role": "user", "content": "テキスト: この映画は最高でした！感動して泣いてしまいました。"},
        {"role": "assistant", "content": "ポジティブ"},
        # 例2: ネガティブ
        {"role": "user", "content": "テキスト: サービスが最悪で、二度と使いたくないです。"},
        {"role": "assistant", "content": "ネガティブ"},
        # 例3: ニュートラル
        {"role": "user", "content": "テキスト: 今日は会議が3つありました。"},
        {"role": "assistant", "content": "ニュートラル"},
        # 例4: ポジティブ（少し複雑な例）
        {"role": "user", "content": "テキスト: 思ったより難しかったけど、やり遂げることができて良かった。"},
        {"role": "assistant", "content": "ポジティブ"},
        # 実際に分類したいテキスト
        {"role": "user", "content": f"テキスト: {text}"},
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16,
        system="テキストの感情を「ポジティブ」「ネガティブ」「ニュートラル」のいずれかで分類してください。ラベルのみ出力してください。",
        messages=messages,
    )
    return response.content[0].text.strip()


def few_shot_category_classification(client: Anthropic, text: str) -> str:
    """
    Few-shotカテゴリ分類: ニュース記事のカテゴリを分類する。

    カテゴリ: テクノロジー / ビジネス / スポーツ / エンタメ / 政治

    Args:
        client: Anthropicクライアント
        text: 分類するニュース記事のテキスト

    Returns:
        str: カテゴリ名
    """
    messages = [
        # 例1: テクノロジー
        {
            "role": "user",
            "content": "記事: 新型スマートフォンが発売され、AIカメラ機能が大幅に向上した。",
        },
        {"role": "assistant", "content": "テクノロジー"},
        # 例2: ビジネス
        {
            "role": "user",
            "content": "記事: 大手自動車メーカーが第3四半期の決算を発表し、純利益が前年比20%増加した。",
        },
        {"role": "assistant", "content": "ビジネス"},
        # 例3: スポーツ
        {
            "role": "user",
            "content": "記事: サッカー日本代表がワールドカップ予選で3-1の勝利を収めた。",
        },
        {"role": "assistant", "content": "スポーツ"},
        # 例4: エンタメ
        {
            "role": "user",
            "content": "記事: 人気アニメの劇場版が公開初日に興行収入10億円を突破した。",
        },
        {"role": "assistant", "content": "エンタメ"},
        # 例5: 政治
        {
            "role": "user",
            "content": "記事: 国会で新たな環境政策法案が審議され、与野党の議論が続いている。",
        },
        {"role": "assistant", "content": "政治"},
        # 分類対象
        {"role": "user", "content": f"記事: {text}"},
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=16,
        system="ニュース記事を「テクノロジー」「ビジネス」「スポーツ」「エンタメ」「政治」のいずれかに分類してください。カテゴリ名のみ出力してください。",
        messages=messages,
    )
    return response.content[0].text.strip()


def few_shot_format_conversion(client: Anthropic, text: str) -> str:
    """
    Few-shotフォーマット変換: 非構造化テキストを構造化データに変換する。

    自然言語で書かれた情報を決まったフォーマットに変換する例。

    Args:
        client: Anthropicクライアント
        text: 変換する非構造化テキスト

    Returns:
        str: 構造化されたテキスト
    """
    messages = [
        # 例1
        {
            "role": "user",
            "content": "田中太郎、35歳、エンジニア、東京在住、メール: tanaka@example.com",
        },
        {
            "role": "assistant",
            "content": "名前: 田中太郎\n年齢: 35歳\n職業: エンジニア\n居住地: 東京\nメール: tanaka@example.com",
        },
        # 例2
        {
            "role": "user",
            "content": "佐藤花子、28歳、デザイナー、大阪在住、連絡先: sato.hanako@mail.jp",
        },
        {
            "role": "assistant",
            "content": "名前: 佐藤花子\n年齢: 28歳\n職業: デザイナー\n居住地: 大阪\nメール: sato.hanako@mail.jp",
        },
        # 変換対象
        {"role": "user", "content": text},
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=128,
        system="提供された個人情報を指定のフォーマットに変換してください。",
        messages=messages,
    )
    return response.content[0].text.strip()


def compare_zero_vs_few_shot(client: Anthropic) -> None:
    """
    Zero-shotとFew-shotの結果を比較する。

    同じ入力に対して両手法の結果を比較し、
    Few-shotの効果を視覚的に確認する。
    """
    print("【Zero-shot vs Few-shot 比較】\n")

    test_texts = [
        "予想外のサプライズで驚いたけど、嬉しかったです！",
        "商品は届いたが、説明書が入っていなかった。",
        "今年の夏は例年より気温が高いそうです。",
    ]

    for text in test_texts:
        zero_result = zero_shot_classification(client, text)
        few_result = few_shot_sentiment_analysis(client, text)
        print(f"テキスト: {text}")
        print(f"  Zero-shot: {zero_result}")
        print(f"  Few-shot:  {few_result}")
        print()


def main() -> None:
    """メイン処理：Few-shot learningの各テクニックを実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== Few-shot Learning ===\n")

    # Zero-shot vs Few-shot の比較
    compare_zero_vs_few_shot(client)

    # カテゴリ分類の例
    print("【ニュース記事のカテゴリ分類】\n")
    news_articles = [
        "量子コンピュータの研究が進み、実用化に向けた実験が成功した。",
        "プロ野球のシーズン開幕戦が行われ、満員御礼の盛況となった。",
        "中央銀行が金利を0.25%引き上げ、市場に影響を与えた。",
        "人気バンドの全国ツアーのチケットが発売開始と同時に完売した。",
    ]

    for article in news_articles:
        category = few_shot_category_classification(client, article)
        print(f"記事: {article[:40]}...")
        print(f"カテゴリ: {category}\n")

    # フォーマット変換の例
    print("【非構造化テキストの構造化変換】\n")
    test_data = [
        "鈴木一郎、42歳、マネージャー、名古屋在住、連絡先: ichiro.suzuki@corp.co.jp",
        "山田美咲、31歳、マーケター、福岡在住、メール: misaki.yamada@brand.com",
    ]

    for data in test_data:
        print(f"入力: {data}")
        structured = few_shot_format_conversion(client, data)
        print(f"変換後:\n{structured}\n")

    print("\n【まとめ: Few-shot Learningのポイント】")
    print("1. 例示の数: 2〜8例が一般的（多すぎるとコスト増加）")
    print("2. 例示の質: 多様で代表的な例を選ぶ")
    print("3. 一貫性: 入力と出力の形式を統一する")
    print("4. 順序: 難しい例は後に配置する傾向がある")
    print("5. Zero-shotで十分な場合は例示不要（コスト削減）")


if __name__ == "__main__":
    main()

"""
01_system_prompts.py - システムプロンプトの設計

このファイルでは以下を学びます：
- 効果的なシステムプロンプトの設計方法
- ロール設定のパターン（カスタマーサポート、技術アドバイザーなど）
- システムプロンプトのベストプラクティス
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


# =========================================================
# システムプロンプトの例
# =========================================================

# カスタマーサポート担当者のシステムプロンプト
CUSTOMER_SUPPORT_PROMPT = """あなたは株式会社TechMartのカスタマーサポート担当者「アシスタントAI」です。

【役割】
- お客様の問題を丁寧かつ迅速に解決する
- 製品やサービスに関する正確な情報を提供する

【行動指針】
- 常に敬語で、親切かつプロフェッショナルな対応をする
- 問題が解決できない場合は、上位サポートへのエスカレーション方法を案内する
- 個人情報の取り扱いには十分注意する

【制約】
- 競合他社の製品を否定的に評価しない
- 確認できない情報については「確認してご連絡します」と回答する
- 返金・補償の約束は行わない（担当者に引き継ぐ）"""


# 技術アドバイザーのシステムプロンプト
TECHNICAL_ADVISOR_PROMPT = """あなたはシニアソフトウェアエンジニアとして、技術的な質問に回答します。

【専門領域】
- Python, JavaScript, TypeScript
- クラウドアーキテクチャ（AWS, GCP, Azure）
- データベース設計とSQL最適化
- APIデザインとマイクロサービス

【回答スタイル】
- コード例を積極的に示す
- パフォーマンスや保守性の観点からベストプラクティスを提案する
- 複数のアプローチがある場合は選択肢とトレードオフを説明する

【出力形式】
- コードはマークダウンのコードブロックで記述する
- 重要なポイントは箇条書きで整理する
- 専門用語は必要に応じて説明を補足する"""


# 教育コーチのシステムプロンプト
EDUCATION_COACH_PROMPT = """あなたは中学生・高校生向けの学習コーチです。

【指導方針】
- 難しい概念を身近な例えで説明する
- 一方的に教えるのではなく、考えさせる質問を投げかける
- 間違いを指摘する際は励ましの言葉を添える

【回答形式】
- 短く分かりやすい文章を使う
- 専門用語は使わず、必要な場合は丁寧に説明する
- 学習意欲を高めるポジティブな言葉を使う

【禁止事項】
- 宿題の答えをそのまま教えることはしない
- ヒントを出して自分で解決できるよう導く"""


def demonstrate_role_setting(client: Anthropic) -> None:
    """
    異なるロール設定によって回答がどう変わるかを実演する。

    同じ質問に対して、システムプロンプトを変えることで
    応答のトーンや内容が変わることを確認する。
    """
    question = "パスワードを忘れてしまいました。どうすればいいですか？"

    print("【同じ質問、異なるロール設定の比較】")
    print(f"質問: {question}\n")

    roles = [
        ("カスタマーサポート担当者", CUSTOMER_SUPPORT_PROMPT),
        ("技術アドバイザー", TECHNICAL_ADVISOR_PROMPT),
    ]

    for role_name, system_prompt in roles:
        print(f"--- {role_name}として ---")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        )
        print(response.content[0].text)
        print()


def demonstrate_output_format_control(client: Anthropic) -> None:
    """
    システムプロンプトで出力形式をコントロールする例。

    JSON形式、箇条書き、段落形式など、
    異なる出力形式を指定する方法を示す。
    """
    print("【出力形式のコントロール】\n")

    question = "Pythonの主な特徴を教えてください"

    # JSON形式で出力を要求
    json_system = """あなたはデータ抽出の専門家です。
回答は必ずJSON形式で返してください。
形式: {"features": [{"name": "特徴名", "description": "説明"}]}
JSON以外のテキストは含めないでください。"""

    print("JSON形式での出力:")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system=json_system,
        messages=[{"role": "user", "content": question}],
    )
    print(response.content[0].text)
    print()

    # 箇条書き形式
    bullet_system = """回答は必ず以下の形式で返してください：
- 各特徴を箇条書きで3点にまとめる
- 各項目は「特徴名: 説明」の形式で書く
- 余分な前置きや後書きは不要"""

    print("箇条書き形式での出力:")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        system=bullet_system,
        messages=[{"role": "user", "content": question}],
    )
    print(response.content[0].text)
    print()


def demonstrate_constraints(client: Anthropic) -> None:
    """
    制約条件をシステムプロンプトで設定する例。

    回答の長さ、トピックの制限、言語の指定など
    様々な制約の設定方法を示す。
    """
    print("【制約条件の設定】\n")

    # 回答を1文に制限
    constrained_system = """あなたは簡潔さを重視するアシスタントです。
どんな質問も必ず1文（句点1つ）で回答してください。"""

    questions = [
        "機械学習とは何ですか？",
        "クラウドコンピューティングの利点は？",
    ]

    print("1文制限での回答:")
    for q in questions:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=128,
            system=constrained_system,
            messages=[{"role": "user", "content": q}],
        )
        print(f"Q: {q}")
        print(f"A: {response.content[0].text}\n")


def best_practices_demo(client: Anthropic) -> None:
    """
    システムプロンプトのベストプラクティスを示す。

    良い例と悪い例を比較して、効果的な書き方を学ぶ。
    """
    print("【システムプロンプトのベストプラクティス】\n")

    question = "このコードのレビューをしてください:\ndef add(a, b): return a+b"

    # 悪い例: 曖昧で指示が不明確
    bad_system = "コードを見てください。"

    # 良い例: 具体的で構造化されている
    good_system = """あなたはシニアエンジニアとしてコードレビューを行います。

レビュー観点:
1. コードの正確性（バグ・エラー）
2. 可読性（命名規則、コメント）
3. パフォーマンス
4. セキュリティ上の懸念

出力形式:
- 各観点について評価（問題なし/要改善/重大な問題）
- 改善提案があれば具体的なコード例を示す
- 最後に総合評価を一言で述べる"""

    print("❌ 悪いシステムプロンプトの例:")
    print(f'  "{bad_system}"')
    response_bad = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        system=bad_system,
        messages=[{"role": "user", "content": question}],
    )
    print(f"回答: {response_bad.content[0].text[:150]}...\n")

    print("✅ 良いシステムプロンプトの例:")
    print("  (詳細なロール・観点・出力形式を指定)")
    response_good = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system=good_system,
        messages=[{"role": "user", "content": question}],
    )
    print(f"回答:\n{response_good.content[0].text}\n")


def main() -> None:
    """メイン処理：システムプロンプトの各テクニックを実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== システムプロンプトの設計 ===\n")

    demonstrate_role_setting(client)
    demonstrate_output_format_control(client)
    demonstrate_constraints(client)
    best_practices_demo(client)

    print("\n【まとめ: システムプロンプトのポイント】")
    print("1. 具体的なロールと責任を明示する")
    print("2. 出力形式を明確に指定する")
    print("3. 制約条件や禁止事項を列挙する")
    print("4. 曖昧な表現を避け、具体的な指示を書く")
    print("5. 長すぎるシステムプロンプトはコストが増加するので適切な長さにする")


if __name__ == "__main__":
    main()

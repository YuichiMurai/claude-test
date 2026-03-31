"""
04_xml_tags.py - XMLタグを使った入力の構造化

このファイルでは以下を学びます：
- XMLタグを使った入力の構造化
- 複数ドキュメントの処理
- 構造化プロンプトによる精度向上
- 複雑なタスクの整理された記述方法
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def analyze_single_document(client: Anthropic, document: str, question: str) -> str:
    """
    XMLタグで構造化されたドキュメントを分析する。

    XMLタグを使うことで、Claudeがどの部分がドキュメント本文で
    どの部分が質問なのかを明確に区別できる。

    Args:
        client: Anthropicクライアント
        document: 分析対象のドキュメント
        question: ドキュメントに対する質問

    Returns:
        str: 分析結果
    """
    # XMLタグを使って入力を構造化する
    # <document> タグでドキュメントを囲み、<question> タグで質問を囲む
    prompt = f"""以下のドキュメントを読んで、質問に答えてください。

<document>
{document}
</document>

<question>
{question}
</question>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system="ドキュメントの内容に基づいて、質問に正確に回答してください。",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def analyze_multiple_documents(
    client: Anthropic,
    documents: list,
    question: str,
) -> str:
    """
    複数のドキュメントをXMLタグで構造化して処理する。

    複数ドキュメントを処理する場合、XMLタグで各ドキュメントを
    識別することで、どのドキュメントからの情報かを明確にできる。

    Args:
        client: Anthropicクライアント
        documents: ドキュメントのリスト（各要素は辞書: {"title": str, "content": str}）
        question: 複数ドキュメントに対する質問

    Returns:
        str: 分析結果
    """
    # 複数ドキュメントをXMLタグで構造化
    docs_xml = ""
    for i, doc in enumerate(documents, 1):
        docs_xml += f"""<document id="{i}" title="{doc['title']}">
{doc['content']}
</document>

"""

    prompt = f"""以下の複数のドキュメントを参照して、質問に答えてください。

<documents>
{docs_xml.strip()}
</documents>

<question>
{question}
</question>

回答には、どのドキュメント（ID）からの情報かを明示してください。"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=768,
        system="複数のドキュメントを分析し、質問に対して根拠となるドキュメントを示しながら回答してください。",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def structured_task_prompt(
    client: Anthropic,
    task: str,
    context: str,
    constraints: list,
    output_format: str,
) -> str:
    """
    複雑なタスクをXMLタグで整理して記述する。

    タスク、コンテキスト、制約条件、出力形式を
    XMLタグで分けて記述することで、複雑な指示を明確に伝える。

    Args:
        client: Anthropicクライアント
        task: 実行するタスクの説明
        context: タスクのコンテキスト情報
        constraints: 制約条件のリスト
        output_format: 出力形式の指定

    Returns:
        str: タスクの実行結果
    """
    # 制約条件をXMLリストに変換
    constraints_xml = "\n".join(f"  <constraint>{c}</constraint>" for c in constraints)

    prompt = f"""<task>
{task}
</task>

<context>
{context}
</context>

<constraints>
{constraints_xml}
</constraints>

<output_format>
{output_format}
</output_format>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=768,
        system="指定されたタスクを、コンテキストと制約条件を考慮しながら実行してください。",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def code_review_with_xml(
    client: Anthropic,
    code: str,
    language: str,
    review_focus: list,
) -> str:
    """
    XMLタグを使ったコードレビューの構造化。

    コードと指示をXMLタグで整理し、
    どの観点でレビューするかを明確に指定する。

    Args:
        client: Anthropicクライアント
        code: レビューするコード
        language: プログラミング言語
        review_focus: レビューの観点リスト

    Returns:
        str: コードレビュー結果
    """
    focus_items = "\n".join(f"  <focus_item>{item}</focus_item>" for item in review_focus)

    prompt = f"""以下のコードをレビューしてください。

<code language="{language}">
{code}
</code>

<review_focus>
{focus_items}
</review_focus>

<output_format>
各観点について評価し、改善提案をコード例と共に示してください。
</output_format>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system="コードレビューの専門家として、指定された観点から詳細なレビューを提供してください。",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main() -> None:
    """メイン処理：XMLタグを使った構造化の各テクニックを実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== XMLタグを使った入力の構造化 ===\n")

    # 単一ドキュメントの分析
    print("【単一ドキュメントの分析】\n")
    document = """
    クラウドコンピューティングとは、インターネットを通じてコンピューティングリソース
    （サーバー、ストレージ、データベース、ネットワーク、ソフトウェアなど）を
    オンデマンドで提供するサービスです。

    主なメリット：
    1. 初期投資の削減：物理的なハードウェアへの投資が不要
    2. スケーラビリティ：必要に応じてリソースを拡張・縮小できる
    3. 可用性：世界中のデータセンターから24時間365日サービスを提供
    4. 最新技術へのアクセス：常に最新のインフラを利用可能

    主要なサービスモデル：
    - IaaS（Infrastructure as a Service）：インフラ全体をクラウドで提供
    - PaaS（Platform as a Service）：開発・実行環境をクラウドで提供
    - SaaS（Software as a Service）：アプリケーションをクラウドで提供
    """

    question = "クラウドコンピューティングのサービスモデルを3つ挙げ、それぞれを一文で説明してください。"
    print(f"質問: {question}\n")
    answer = analyze_single_document(client, document, question)
    print(f"回答:\n{answer}\n")
    print("-" * 60)

    # 複数ドキュメントの処理
    print("\n【複数ドキュメントの処理】\n")
    documents = [
        {
            "title": "AWS公式資料",
            "content": "AWSはAmazonが提供するクラウドサービスで、200以上のサービスを提供しています。EC2（仮想サーバー）、S3（オブジェクトストレージ）、RDS（マネージドデータベース）が主要サービスです。市場シェアは約33%で世界首位です。",
        },
        {
            "title": "GCP技術ドキュメント",
            "content": "Google Cloud Platform（GCP）はGoogleが提供するクラウドサービスです。BigQuery（データウェアハウス）、Kubernetes Engine（コンテナ管理）、Vertex AI（機械学習）が強みです。AIと機械学習分野で特に優れています。",
        },
        {
            "title": "Azure製品カタログ",
            "content": "Microsoft Azureはマイクロソフトのクラウドサービスです。既存のMicrosoft製品（Office 365、Windows Server）との統合が得意です。Azure DevOpsやActive Directoryとの連携で企業向け市場を中心に成長しています。",
        },
    ]

    multi_question = "各クラウドプロバイダーの最も得意な分野は何ですか？比較してください。"
    print(f"質問: {multi_question}\n")
    multi_answer = analyze_multiple_documents(client, documents, multi_question)
    print(f"回答:\n{multi_answer}\n")
    print("-" * 60)

    # 構造化されたタスクプロンプト
    print("\n【構造化タスクプロンプト】\n")
    task_result = structured_task_prompt(
        client,
        task="スタートアップ向けの技術スタック選定レポートを作成してください",
        context="10人規模のSaaS系スタートアップ。Webアプリケーション開発。チームはPythonに慣れている。",
        constraints=[
            "予算は最初の1年間で月額10万円以内",
            "開発者が5人以下でも管理できる構成",
            "スケールアップが容易であること",
            "日本語のドキュメントまたはサポートが充実していること",
        ],
        output_format="フロントエンド・バックエンド・データベース・インフラの4カテゴリで、各推奨技術とその理由を簡潔に記述",
    )
    print(f"技術スタック選定レポート:\n{task_result}\n")
    print("-" * 60)

    # コードレビューの例
    print("\n【XMLタグを使ったコードレビュー】\n")
    sample_code = """
def get_user_data(user_id):
    import sqlite3
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)
    result = cursor.fetchone()
    return result
"""
    review_result = code_review_with_xml(
        client,
        code=sample_code,
        language="Python",
        review_focus=[
            "セキュリティ（SQLインジェクション等）",
            "エラーハンドリング",
            "リソース管理（接続のクローズ）",
            "コードの可読性",
        ],
    )
    print(f"コードレビュー結果:\n{review_result}\n")

    print("\n【まとめ: XMLタグ構造化のポイント】")
    print("1. 入力の区別: ドキュメント本文と指示を明確に分離する")
    print("2. 複数データ: id属性などで各要素を識別できるようにする")
    print("3. タスク分解: task/context/constraints/output_formatで整理する")
    print("4. 一貫性: プロジェクト内でタグ名を統一する")
    print("5. 特殊文字: XMLの特殊文字（<>&）はエスケープを検討する")


if __name__ == "__main__":
    main()

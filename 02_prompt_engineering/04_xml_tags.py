"""
04_xml_tags.py - XML タグを使った入力の構造化

このファイルの目的:
- XML タグで入力データを構造化してClaudeのパフォーマンスを向上させる
- 複数ドキュメントを整理してまとめて処理する方法を学ぶ
- 複雑なプロンプトにおける明確な区切り方を習得する

【Google Colabでの実行方法】
1. 最初にこれを実行:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/04_xml_tags.py
   または、コードをColabのセルに貼り付けて実行

【CCA試験ポイント】
- XML タグは Anthropic が推奨する構造化手法
- タグで囲むことで Claude が各部分の役割を明確に認識できる
- 複数のドキュメントや長いコンテンツを扱う際に特に有効
- タグ名は分かりやすい名前を使う（例: <document>, <instructions>, <context>）
- タグはネスト（入れ子）にすることもできる
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


def summarize_single_document(client: Anthropic, document: str, instructions: str) -> str:
    """
    XML タグを使った単一ドキュメントの要約

    <document> タグと <instructions> タグを使って、
    処理対象のデータと指示を明確に分離する。

    Args:
        client: Anthropicクライアント
        document: 要約するドキュメントのテキスト
        instructions: 要約の指示（長さ・形式など）

    Returns:
        str: 要約テキスト
    """
    # XML タグを使ってドキュメントと指示を明確に区別する
    prompt = f"""<document>
{document}
</document>

<instructions>
{instructions}
</instructions>

上記の <document> の内容を、<instructions> に従って処理してください。"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def process_multiple_documents(
    client: Anthropic,
    documents: list[dict[str, str]],
    task: str
) -> str:
    """
    複数ドキュメントの処理

    <documents> タグの中に複数の <document> タグを入れて
    複数のファイルや記事を一度に処理する。

    Args:
        client: Anthropicクライアント
        documents: ドキュメントのリスト（各要素は title と content を持つ辞書）
        task: 実行するタスクの説明

    Returns:
        str: 処理結果
    """
    # 複数ドキュメントを構造化して組み立てる
    docs_xml = ""
    for i, doc in enumerate(documents, 1):
        docs_xml += f"""<document index="{i}">
  <title>{doc['title']}</title>
  <content>{doc['content']}</content>
</document>
"""

    prompt = f"""<documents>
{docs_xml}</documents>

<task>
{task}
</task>

上記の <documents> を参照しながら、<task> を実行してください。"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def extract_structured_info(client: Anthropic, text: str) -> str:
    """
    XML タグを使った構造化情報の抽出

    非構造化テキストから特定の情報を抽出する際に
    XML タグで抽出項目を明示することで精度が向上する。

    Args:
        client: Anthropicクライアント
        text: 情報を抽出するテキスト

    Returns:
        str: 抽出された構造化情報（XML形式）
    """
    prompt = f"""<input_text>
{text}
</input_text>

<extraction_schema>
以下の情報を抽出してください：
- 人物名（存在する場合）
- 日付・時刻（存在する場合）
- 場所（存在する場合）
- 金額（存在する場合）
- 主要なアクション
</extraction_schema>

<output_format>
以下のXML形式で出力してください：
<extracted_info>
  <persons>（人物名をカンマ区切りで。なければ「なし」）</persons>
  <dates>（日付・時刻をカンマ区切りで。なければ「なし」）</dates>
  <locations>（場所をカンマ区切りで。なければ「なし」）</locations>
  <amounts>（金額をカンマ区切りで。なければ「なし」）</amounts>
  <actions>（主要なアクションを箇条書きで）</actions>
</extracted_info>
</output_format>"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def compare_code_reviews(client: Anthropic, original: str, revised: str) -> str:
    """
    2つのコードを比較してレビューする

    <original> と <revised> タグを使って2つのバージョンを明確に区別し
    差分の説明や改善点の分析を依頼する。

    Args:
        client: Anthropicクライアント
        original: 元のコード
        revised: 改訂後のコード

    Returns:
        str: 比較・レビュー結果
    """
    prompt = f"""<original_code>
{original}
</original_code>

<revised_code>
{revised}
</revised_code>

<review_criteria>
以下の観点でコードの変更点をレビューしてください：
1. 可読性の改善点
2. パフォーマンスへの影響
3. 潜在的なバグや問題点
4. 全体的な評価
</review_criteria>

<original_code> から <revised_code> への変更を上記の基準でレビューしてください。"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=768,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


if __name__ == "__main__":
    print("=" * 60)
    print("XML タグを使った入力の構造化")
    print("=" * 60)

    client = get_client()

    # --- 単一ドキュメントの要約 ---
    print("\n【単一ドキュメントの要約】")

    article = """
人工知能（AI）技術は近年急速に進化しており、様々な産業に大きな変革をもたらしています。
特に大規模言語モデル（LLM）の登場により、自然言語処理の精度が飛躍的に向上しました。
医療分野では診断支援、金融分野ではリスク管理、製造業では品質管理など、
AIの活用範囲は拡大し続けています。
一方で、AIの倫理的な活用、プライバシー保護、雇用への影響といった課題も
社会的な議論になっています。2024年には多くの国でAI規制の法整備が進み、
責任あるAI開発・活用のガイドラインが策定されました。
"""

    instructions = "3つの箇条書きポイントで、重要な点を簡潔に要約してください。"
    summary = summarize_single_document(client, article, instructions)
    print(f"要約結果:\n{summary}")

    # --- 複数ドキュメントの処理 ---
    print("\n\n【複数ドキュメントの比較分析】")

    documents = [
        {
            "title": "製品Aのレビュー",
            "content": (
                "使いやすいインターフェースで初心者でも簡単に使いこなせます。"
                "処理速度が速く、バッテリーの持ちも良好です。"
                "ただし価格がやや高めです。"
            )
        },
        {
            "title": "製品Bのレビュー",
            "content": (
                "コストパフォーマンスが非常に高く、機能も充実しています。"
                "UIは少し複雑ですが慣れれば問題ありません。"
                "サポートが充実していて安心感があります。"
            )
        },
        {
            "title": "製品Cのレビュー",
            "content": (
                "デザインがスタイリッシュで持ち運びやすいです。"
                "処理速度は平均的ですが日常使いには十分です。"
                "価格と品質のバランスが取れています。"
            )
        },
    ]

    comparison_task = (
        "3つの製品を比較して、"
        "それぞれの長所・短所をまとめ、"
        "どのようなユーザーに各製品が向いているか推薦してください。"
    )

    result = process_multiple_documents(client, documents, comparison_task)
    print(f"比較分析結果:\n{result}")

    # --- 構造化情報の抽出 ---
    print("\n\n【構造化情報の抽出】")

    news_text = (
        "田中社長は2024年3月15日、東京本社にて記者会見を開き、"
        "新製品「AIアシスタント Pro」を5万円で発売すると発表しました。"
        "山田副社長と鈴木取締役も同席し、大阪と名古屋での展示会も予定していると述べました。"
    )

    print(f"入力テキスト: {news_text}")
    print("\n抽出結果:")
    print(extract_structured_info(client, news_text))

    # --- コードレビュー ---
    print("\n\n【コードレビュー比較】")

    original_code = """def calc(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b"""

    revised_code = """def calculate(a: float, b: float, operator: str) -> float:
    \"\"\"四則演算を実行する\"\"\"
    operations = {
        '+': lambda x, y: x + y,
        '-': lambda x, y: x - y,
        '*': lambda x, y: x * y,
        '/': lambda x, y: x / y if y != 0 else float('inf'),
    }
    if operator not in operations:
        raise ValueError(f"未対応の演算子: {operator}")
    return operations[operator](a, b)"""

    print(compare_code_reviews(client, original_code, revised_code))

    print("\n✅ 完了！exercises/ の練習問題に進んでください。")

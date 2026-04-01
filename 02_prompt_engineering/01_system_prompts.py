"""
01_system_prompts.py - システムプロンプトの設計

このファイルの目的:
- システムプロンプトの基本的な使い方を学ぶ
- ロールベースのシステムプロンプトを設計する
- トーン（カジュアル vs フォーマル）をコントロールする
- 出力形式を指定してClaudeの振る舞いを制御する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/01_system_prompts.py
   または、コードをColabのセルに貼り付けて実行

【システムプロンプトとは？】
システムプロンプトはClaudeの振る舞い・役割・制約を定義するための特別な入力です。
会話が始まる前に設定され、その会話全体を通じてClaudeの動作に影響します。
messagesリストのuser/assistantとは別に、systemパラメータとして渡します。
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


def basic_system_prompt(client: Anthropic) -> None:
    """
    基本的なシステムプロンプトの例

    システムプロンプトなし vs ありの違いを比較します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 基本的なシステムプロンプト ---")

    question = "機械学習とは何ですか？"

    # システムプロンプトなし: 汎用的な回答
    print("\n【システムプロンプトなし】")
    response_no_system = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(f"回答: {response_no_system.content[0].text[:200]}...")

    # システムプロンプトあり: 役割を定義して回答を特化させる
    print("\n【システムプロンプトあり（小学生向け先生）】")
    response_with_system = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        # systemプロンプトでClaudeの役割と制約を定義
        system=(
            "あなたは小学生に教える先生です。"
            "難しい専門用語は使わず、身近な例えを使って説明してください。"
            "子どもが「なるほど！」と思えるような、楽しい説明を心がけてください。"
        ),
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(f"回答: {response_with_system.content[0].text[:200]}...")


def role_based_system_prompts(client: Anthropic) -> None:
    """
    ロールベースのシステムプロンプトの例

    異なる役割を設定することで、同じ質問に対して
    専門性の異なる回答を得られます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- ロールベースのシステムプロンプト ---")

    question = "Pythonのエラーハンドリングのベストプラクティスを教えてください。"

    # ロールの定義リスト
    roles = [
        {
            "name": "カスタマーサポート担当者",
            "system": (
                "あなたは丁寧なカスタマーサポート担当者です。"
                "ユーザーの問題を分かりやすく解決に導いてください。"
                "専門用語を避け、ステップバイステップで説明してください。"
                "常に親切で忍耐強い態度で接してください。"
            )
        },
        {
            "name": "シニアエンジニア（技術レビュアー）",
            "system": (
                "あなたはGoogle出身のシニアソフトウェアエンジニアです。"
                "コードの品質、パフォーマンス、セキュリティを重視します。"
                "業界のベストプラクティスと設計パターンに基づいて回答してください。"
                "必要に応じてコード例を含めてください。"
            )
        },
        {
            "name": "プログラミング初心者向けメンター",
            "system": (
                "あなたはプログラミング初学者を支援するメンターです。"
                "挫折しないよう励ましながら、基礎からていねいに教えてください。"
                "「なぜそうするのか」という理由を必ず説明してください。"
                "コード例は最もシンプルな形で示してください。"
            )
        },
    ]

    for role in roles:
        print(f"\n【役割: {role['name']}】")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            system=role["system"],
            messages=[
                {"role": "user", "content": question}
            ]
        )
        # 最初の200文字だけ表示して比較
        print(f"回答: {response.content[0].text[:200]}...")


def tone_control(client: Anthropic) -> None:
    """
    トーン（カジュアル vs フォーマル）のコントロール例

    システムプロンプトでコミュニケーションスタイルを制御できます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- トーンのコントロール ---")

    question = "APIキーはどこに保存すればいいですか？"

    # カジュアルなトーン
    print("\n【カジュアルなトーン（友達感覚）】")
    casual_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        system=(
            "友達に話しかけるようなカジュアルなトーンで回答してください。"
            "「〜だよ」「〜だね」などの話し言葉を使ってください。"
            "絵文字を1〜2個使ってもOKです。"
        ),
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(f"回答: {casual_response.content[0].text}")

    # フォーマルなトーン
    print("\n【フォーマルなトーン（ビジネス文書）】")
    formal_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        system=(
            "ビジネス文書のような丁寧でフォーマルなトーンで回答してください。"
            "「〜でございます」「〜いたします」などの敬語を使用してください。"
            "箇条書きや番号付きリストで整理して説明してください。"
        ),
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(f"回答: {formal_response.content[0].text}")


def output_format_control(client: Anthropic) -> None:
    """
    出力形式の指定例

    システムプロンプトで出力フォーマットを細かく制御できます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 出力形式の指定 ---")

    question = "Pythonのデータ型（int, float, str, list, dict）について説明してください。"

    # マークダウン形式
    print("\n【マークダウン形式で出力】")
    markdown_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=400,
        system=(
            "回答はMarkdown形式で出力してください。"
            "見出し（##）、箇条書き（-）、コードブロック（```python）を適切に使用してください。"
            "各データ型についてコード例を必ず含めてください。"
        ),
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(markdown_response.content[0].text)

    # JSON形式
    print("\n【JSON形式で出力】")
    json_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=400,
        system=(
            "回答は必ずJSON形式のみで出力してください。"
            "以下の構造で出力してください:\n"
            "{\n"
            '  "data_types": [\n'
            '    {\n'
            '      "name": "型名",\n'
            '      "description": "説明",\n'
            '      "example": "コード例"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "JSONの前後にテキストを追加しないでください。"
        ),
        messages=[
            {"role": "user", "content": question}
        ]
    )
    print(json_response.content[0].text)


def multi_constraint_system_prompt(client: Anthropic) -> None:
    """
    複数の制約を組み合わせたシステムプロンプトの例

    実際のプロダクションでは複数の制約を組み合わせて使います

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 複数制約の組み合わせ ---")

    # 実際のプロダクションで使いそうな複合システムプロンプト
    system_prompt = """あなたは「TechBot」という技術サポートチャットボットです。

# 役割と目的
- ソフトウェア開発者の技術的な質問に回答する
- 正確で実用的な情報を提供する

# 制約事項
- 回答は日本語で行う
- 300文字以内で簡潔に回答する
- コードを含む場合は必ずPythonで示す
- 不確かな情報は「〜と思われますが、公式ドキュメントを確認してください」と明記する
- セキュリティに関わる情報は慎重に扱う

# 出力形式
1. 直接回答（1-2文）
2. コード例（必要な場合）
3. 補足情報（必要な場合）"""

    print(f"システムプロンプト:\n{system_prompt}\n")

    questions = [
        "Pythonでファイルを読み込むにはどうすればいいですか？",
        "パスワードはどうやって安全に保存しますか？",
    ]

    for question in questions:
        print(f"\n質問: {question}")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=512,
            system=system_prompt,
            messages=[
                {"role": "user", "content": question}
            ]
        )
        print(f"TechBot: {response.content[0].text}")


def system_prompt_best_practices() -> None:
    """
    システムプロンプトのベストプラクティスを表示する

    APIリクエストを行わず、ベストプラクティスの解説のみ行います
    """
    print("\n--- システムプロンプトのベストプラクティス ---")

    best_practices = """
【✅ 良いシステムプロンプトの特徴】

1. 役割を明確に定義する
   悪い例: 「あなたはアシスタントです」
   良い例: 「あなたはPythonの専門家で、初心者にコードレビューを行います」

2. 具体的な制約を設ける
   悪い例: 「分かりやすく説明してください」
   良い例: 「専門用語を使う場合は必ず括弧内で解説してください。回答は500文字以内にしてください」

3. 出力形式を指定する
   悪い例: 「構造化して回答してください」
   良い例: 「見出し、箇条書き、コードブロックを使いMarkdown形式で出力してください」

4. 何をすべきでないかも明記する
   例: 「個人情報や機密情報は絶対に出力しないでください」
       「競合他社の製品を肯定的に評価しないでください」

5. コンテキストと背景を提供する
   例: 「このシステムはB2Bの法人向けサービスです。ユーザーはITリテラシーの高いエンジニアです」

【⚠️ よくある間違い】

1. 曖昧すぎる指示
   → 「良い回答をしてください」では効果なし

2. 矛盾する指示
   → 「短く答えてください」と「詳しく説明してください」を同時に指定しない

3. 過度に長いシステムプロンプト
   → 重要なことに絞る（長すぎると重要な指示が埋もれる）

4. ユーザーメッセージに入れるべき内容をsystemに入れる
   → 会話ごとに変わる内容はmessagesに入れる

【💡 CCA試験のポイント】
- systemパラメータはAPIリクエストのトップレベルに設定する
- システムプロンプトはすべてのターンに適用される
- ユーザーはシステムプロンプトを見ることができない（隠しておける）
- 適切なシステムプロンプトによりトークン消費を削減できる
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 50)
    print("システムプロンプトの設計")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    basic_system_prompt(client)
    role_based_system_prompts(client)
    tone_control(client)
    output_format_control(client)
    multi_constraint_system_prompt(client)
    system_prompt_best_practices()

    print("\n✅ 完了！次は02_few_shot_learning.pyに進んでください。")

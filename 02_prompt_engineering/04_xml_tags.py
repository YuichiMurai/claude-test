"""
04_xml_tags.py - XMLタグを使ったプロンプトの構造化

このファイルの目的:
- XMLタグを使ってプロンプトを構造化する方法を学ぶ
- 単一・複数ドキュメントの処理方法を理解する
- タスク構造化と入出力フォーマットの制御を習得する

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/04_xml_tags.py
   または、コードをColabのセルに貼り付けて実行

【XMLタグとは？】
Anthropicが推奨するプロンプト構造化のベストプラクティスです。
XMLタグを使ってプロンプトの各部分を明確に区別することで:
- プロンプトの解釈精度が向上する
- 複数の入力データを明確に分離できる
- 出力形式を細かく制御できる
- プロンプトの可読性・保守性が高まる

例:
<document>
ここに処理対象のテキストが入ります
</document>

<instructions>
上記のドキュメントを要約してください
</instructions>
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


def single_document_processing(client: Anthropic) -> None:
    """
    単一ドキュメントの処理例

    XMLタグを使って入力データと指示を明確に分離します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 単一ドキュメントの処理 ---")

    document = """
    人工知能（AI）は急速に進化しており、私たちの日常生活やビジネスに
    大きな影響を与えています。特に自然言語処理の分野では、GPTやClaudeなどの
    大規模言語モデルが登場し、文章生成、翻訳、要約などのタスクで
    人間に匹敵するパフォーマンスを発揮しています。

    一方で、AIの発展には課題も伴います。プライバシーの問題、
    著作権の扱い、AIによる誤情報の拡散などが社会問題として
    議論されています。また、AIが人間の仕事を奪うのではないかという
    懸念も根強くあります。

    しかし、多くの専門家は、AIは人間の仕事を補完するものであり、
    新たな職業や産業を生み出す可能性が高いと考えています。
    重要なのは、AIと共存するためのリテラシーを身につけることです。
    """

    # XMLタグなし（構造化されていないプロンプト）
    print("【XMLタグなし】")
    response_no_xml = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                "content": f"以下の文章を3つの箇条書きで要約してください。\n\n{document}"
            }
        ]
    )
    print(f"出力:\n{response_no_xml.content[0].text}")

    # XMLタグあり（構造化されたプロンプト）
    print("\n【XMLタグあり】")
    response_with_xml = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=200,
        messages=[
            {
                "role": "user",
                # XMLタグでドキュメントと指示を明確に分離する
                "content": f"""<document>
{document}
</document>

<instructions>
上記のdocumentを以下の形式で要約してください:
- 要点を3つの箇条書きで示す
- 各箇条書きは1文で完結させる
- 専門用語は避けてわかりやすく書く
</instructions>"""
            }
        ]
    )
    print(f"出力:\n{response_with_xml.content[0].text}")


def multiple_documents_processing(client: Anthropic) -> None:
    """
    複数ドキュメントの処理例（id属性付き）

    id属性を使って複数のドキュメントを明確に識別します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 複数ドキュメントの処理（id属性付き） ---")

    # 複数のドキュメントをid属性で識別する
    documents = [
        {
            "id": "review_001",
            "content": "このスマートフォンは本当に素晴らしいです。カメラの性能が特に優秀で、夜景もきれいに撮影できます。バッテリーの持ちも良く、一日中使えます。"
        },
        {
            "id": "review_002",
            "content": "期待していたほどではありませんでした。確かに機能は多いですが、動作が重く感じます。カスタマーサポートの対応も今ひとつでした。"
        },
        {
            "id": "review_003",
            "content": "価格と性能のバランスが良いと思います。デザインもスタイリッシュで気に入っています。ただ、充電器が付属していないのは少し残念でした。"
        },
    ]

    # XMLタグとid属性を使って複数ドキュメントを構造化する
    documents_xml = "\n".join([
        f'<document id="{doc["id"]}">\n{doc["content"]}\n</document>'
        for doc in documents
    ])

    prompt = f"""<documents>
{documents_xml}
</documents>

<instructions>
上記の3つのレビューを分析して、以下の情報を提供してください:

1. 各レビュー（id別）の感情: ポジティブ/ネガティブ/ミックス
2. 全レビューに共通するポジティブな点
3. 全レビューに共通するネガティブな点
4. 総合評価（5点満点）とその理由

出力は以下のXML形式で返してください:
<analysis>
  <review id="review_001">
    <sentiment>感情</sentiment>
  </review>
  ...
  <common_positives>共通のポジティブ点</common_positives>
  <common_negatives>共通のネガティブ点</common_negatives>
  <overall_rating>X/5 - 理由</overall_rating>
</analysis>
</instructions>"""

    print(f"入力ドキュメント数: {len(documents)}")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f"分析結果:\n{response.content[0].text}")


def task_structuring_with_xml(client: Anthropic) -> None:
    """
    XMLタグを使ったタスク構造化の例

    instructions, context, examples, input タグを使って
    複雑なタスクを明確に定義します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- XMLタグによるタスク構造化 ---")

    # 複雑なタスクをXMLで構造化する
    structured_prompt = """<instructions>
顧客のフィードバックメッセージを分析して、以下の情報を抽出してください:
1. 感情スコア: 1（非常にネガティブ）〜 5（非常にポジティブ）
2. 主な問題点（あれば）
3. 主な称賛ポイント（あれば）
4. 優先度: High（即対応必要）/ Medium（通常対応）/ Low（記録のみ）
5. 担当部門: 技術サポート / 商品開発 / カスタマーサービス / 配送・物流
</instructions>

<context>
このシステムはECサイトのカスタマーサービス部門で使用されます。
High優先度の問題は24時間以内に担当者がフォローアップします。
顧客満足度を最重要指標として扱っています。
</context>

<examples>
入力: 「商品が壊れた状態で届きました。すぐに交換をお願いします！」
出力:
- 感情スコア: 1
- 主な問題点: 破損した商品の配送
- 主な称賛ポイント: なし
- 優先度: High
- 担当部門: 配送・物流, カスタマーサービス

入力: 「使い方が少し分かりにくいですが、機能自体はとても良いです。」
出力:
- 感情スコア: 4
- 主な問題点: UIの使いやすさ
- 主な称賛ポイント: 機能の質
- 優先度: Low
- 担当部門: 商品開発
</examples>

<input>
注文してから1週間以上経ちますが、まだ商品が届きません。
追跡番号で確認しても「配送中」のままで変わりません。
プレゼント用に購入したので、期日までに届かないと困ります。
早急な対応をお願いします。
</input>"""

    print("構造化されたプロンプトを処理中...")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {"role": "user", "content": structured_prompt}
        ]
    )
    print(f"分析結果:\n{response.content[0].text}")


def output_format_with_xml(client: Anthropic) -> None:
    """
    XMLタグを使った出力フォーマット制御の例

    出力形式をXMLで指定して、プログラムで処理しやすい
    構造化された出力を得ます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- XMLタグによる出力フォーマット制御 ---")

    code_to_review = """
def calculate_average(numbers):
    total = 0
    for n in numbers:
        total = total + n
    average = total / len(numbers)
    return average

result = calculate_average([1, 2, 3, 4, 5])
print(result)
"""

    prompt = f"""<code>
{code_to_review}
</code>

<instructions>
上記のPythonコードをレビューして、結果を以下のXML形式で出力してください。
XMLの前後に余分なテキストを追加しないでください。
</instructions>

<output_format>
<review>
  <summary>コードの概要（1文）</summary>
  <issues>
    <issue severity="high|medium|low">
      <description>問題の説明</description>
      <suggestion>改善提案</suggestion>
    </issue>
  </issues>
  <improvements>
    <improved_code>改善後のコード</improved_code>
  </improvements>
  <score>X/10</score>
</review>
</output_format>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=600,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f"コードレビュー結果:\n{response.content[0].text}")


def cot_with_xml_tags(client: Anthropic) -> None:
    """
    Chain of Thought と XMLタグの組み合わせ例

    <thinking>タグで推論過程を分離し、
    <answer>タグで最終回答を明確にします

    Args:
        client: Anthropicクライアント
    """
    print("\n--- CoT + XMLタグの組み合わせ ---")

    problem = """
    ある会社の売上データ:
    - 1月: 100万円
    - 2月: 120万円
    - 3月: 90万円
    - 4月: 150万円
    - 5月: 130万円

    Q1: 5ヶ月間の平均月次売上はいくらですか？
    Q2: 最も売上が高かった月と低かった月の差はいくらですか？
    Q3: 前月比で最も大きく売上が増加したのはどの月ですか？
    """

    prompt = f"""<problem>
{problem}
</problem>

<instructions>
<thinking>タグ内で各質問をステップバイステップで考え、
<answer>タグ内に最終的な答えのみを記載してください。

出力形式:
<thinking>
Q1の計算過程...
Q2の計算過程...
Q3の計算過程...
</thinking>
<answer>
Q1: X万円
Q2: Y万円
Q3: Z月（前月比+W万円）
</answer>
</instructions>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f"問題:\n{problem}")
    print(f"回答（推論過程付き）:\n{response.content[0].text}")


def xml_tags_best_practices() -> None:
    """
    XMLタグのベストプラクティスを表示する

    APIリクエストを行わず、ベストプラクティスの解説のみ行います
    """
    print("\n--- XMLタグのベストプラクティス ---")

    best_practices = """
【✅ XMLタグの効果的な使い方】

1. よく使うタグとその用途
   <document>       → 処理対象のテキスト・データ
   <documents>      → 複数ドキュメントのコンテナ
   <instructions>   → Claudeへの指示
   <context>        → 背景情報・前提条件
   <examples>       → Few-shot の例
   <input>          → 実際に処理する入力データ
   <output_format>  → 出力形式の指定
   <thinking>       → 推論過程（CoTと組み合わせる）
   <answer>         → 最終的な回答

2. id属性を使って複数ドキュメントを管理する
   <document id="doc_001">...</document>
   <document id="doc_002">...</document>
   → Claudeが各ドキュメントを個別に参照・処理できる

3. タスクを構成要素に分解する
   <instructions>  ← 何をするか
   <context>       ← なぜするか・背景
   <examples>      ← どのようにするか（例）
   <input>         ← 何を処理するか

4. 出力フォーマットをXMLで指定する
   → プログラムで解析しやすい構造化出力が得られる
   → 後処理（XMLパース）との連携が容易になる

【💡 Anthropicが推奨する理由】

- Claudeのトレーニングデータに大量のXMLが含まれている
- XMLタグはテキストとデータを明確に区別できる
- ネストされた構造を直感的に表現できる
- 将来の変更・拡張がしやすい

【⚠️ よくある間違い】

1. タグが対称でない
   悪い例: <document>内容</docs>
   良い例: <document>内容</document>

2. タグ名に不適切な文字を使う
   悪い例: <my document>  ← スペースはNG
   良い例: <my_document>  ← アンダースコアを使う

3. プロンプト内の実際のデータにXMLが含まれる場合
   → エスケープ（&lt;, &gt;）を使うか、異なる構造化方法を選ぶ

【💡 CCA試験のポイント】
- Anthropicはプロンプト設計においてXMLタグの使用を公式に推奨
- <document>タグは長いテキストの処理に特に有効
- 出力フォーマットをXMLで指定すると後処理が容易
- CoTとの組み合わせ（<thinking>タグ）は複雑な推論タスクに有効
- プロンプトの各部分を明確に分離することで誤解を防げる
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 50)
    print("XMLタグを使ったプロンプトの構造化")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    single_document_processing(client)
    multiple_documents_processing(client)
    task_structuring_with_xml(client)
    output_format_with_xml(client)
    cot_with_xml_tags(client)
    xml_tags_best_practices()

    print("\n✅ 完了！02_prompt_engineering セクションを全て学習しました。")
    print("次は 03_secure_applications/ に進んでください。")

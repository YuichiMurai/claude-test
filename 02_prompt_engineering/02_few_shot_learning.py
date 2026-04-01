"""
02_few_shot_learning.py - Few-shot Learning の実装

このファイルの目的:
- Zero-shot と Few-shot プロンプティングの違いを理解する
- Few-shot Learning でClaudeの出力品質を向上させる
- 感情分析・テキスト分類・要約などのタスクへの応用を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/02_few_shot_learning.py
   または、コードをColabのセルに貼り付けて実行

【Few-shot Learning とは？】
AIモデルに「例」を見せることで、望ましい出力形式や推論パターンを
学習させる技術です。

- Zero-shot: 例なしで直接タスクを指示する
- One-shot:  例を1つ提示してからタスクを指示する
- Few-shot:  例を複数（2〜8個程度）提示してからタスクを指示する

例の数が増えるほどモデルはタスクを理解しやすくなりますが、
トークン消費も増えるためバランスが重要です。
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


def zero_shot_vs_few_shot_comparison(client: Anthropic) -> None:
    """
    Zero-shot と Few-shot の比較例

    同じタスクをZero-shotとFew-shotで実行して、
    出力の違いを確認します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Zero-shot vs Few-shot の比較 ---")

    # タスク: 商品レビューの感情分析
    test_review = "配送が思ったより遅かったですが、商品自体は満足しています。"

    # Zero-shot: 例を一切提示せずにタスクを指示する
    print("\n【Zero-shot】")
    zero_shot_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {
                "role": "user",
                # 指示だけでタスクを定義する
                "content": f"以下のレビューの感情を分析してください。\n\nレビュー: {test_review}"
            }
        ]
    )
    print(f"入力: {test_review}")
    print(f"出力: {zero_shot_response.content[0].text}")

    # Few-shot: 例を3つ提示してからタスクを指示する
    print("\n【Few-shot（3-shot）】")
    few_shot_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[
            {
                "role": "user",
                # 例を含めてタスクを定義する（Few-shotの核心）
                "content": (
                    "レビューの感情を分析して「ポジティブ」「ネガティブ」「ミックス」の"
                    "いずれかと、その理由を1文で答えてください。\n\n"
                    # 例1: ポジティブの例
                    "例1:\n"
                    "レビュー: とても使いやすくて気に入っています！また購入したいです。\n"
                    "感情: ポジティブ。満足感と再購入意向が明確に表れているため。\n\n"
                    # 例2: ネガティブの例
                    "例2:\n"
                    "レビュー: 品質が悪く、すぐに壊れてしまいました。二度と買いません。\n"
                    "感情: ネガティブ。品質への不満と否定的な評価が明確なため。\n\n"
                    # 例3: ミックスの例
                    "例3:\n"
                    "レビュー: デザインは素晴らしいですが、価格が少し高いと感じました。\n"
                    "感情: ミックス。デザインへの好評価と価格への不満が共存しているため。\n\n"
                    # 実際のタスク
                    f"レビュー: {test_review}\n"
                    "感情:"
                )
            }
        ]
    )
    print(f"入力: {test_review}")
    print(f"出力: {few_shot_response.content[0].text}")

    print("\n💡 Few-shotの方が指定した形式（ポジティブ/ネガティブ/ミックス）で"
          "一貫した出力が得られます。")


def sentiment_analysis_few_shot(client: Anthropic) -> None:
    """
    Few-shot Learning を使った感情分析の例

    商品レビューをポジティブ/ネガティブ/ニュートラルに分類します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Few-shot 感情分析 ---")

    # Few-shotの例（学習用データとして機能する）
    examples = [
        ("最高の買い物でした！期待以上の品質で大満足です。", "ポジティブ"),
        ("全然使えない。お金の無駄でした。", "ネガティブ"),
        ("普通です。特に良くも悪くもありません。", "ニュートラル"),
        ("梱包が丁寧で迅速な対応に感謝します！商品も申し分なし！", "ポジティブ"),
        ("説明と全く違う商品が届きました。返品します。", "ネガティブ"),
    ]

    # 分析対象のレビュー
    test_reviews = [
        "思ったより小さかったですが、機能は問題なく使えています。",
        "友人へのプレゼントにしました。とても喜んでもらえました！",
        "3回使ったら壊れました。品質管理に問題があると思います。",
    ]

    # Few-shotプロンプトを構築する
    # 各例を「入力 → 出力」の形式で並べる
    few_shot_prompt = (
        "商品レビューの感情を「ポジティブ」「ネガティブ」「ニュートラル」の"
        "いずれかに分類してください。分類結果のみを出力してください。\n\n"
    )

    # 例を追加（これがFew-shotの核心部分）
    for review, label in examples:
        few_shot_prompt += f"レビュー: {review}\n感情: {label}\n\n"

    print("分析対象のレビューを分類します:")
    for review in test_reviews:
        # 各レビューに対して同じFew-shotプロンプトに新しいレビューを追加
        prompt = few_shot_prompt + f"レビュー: {review}\n感情:"

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=20,  # ラベルのみなので短くて良い
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        label = response.content[0].text.strip()
        print(f"  [{label}] {review}")


def news_category_classification(client: Anthropic) -> None:
    """
    Few-shot Learning を使ったニュースカテゴリ分類の例

    ニュースの見出しを自動的にカテゴリに分類します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Few-shot ニュースカテゴリ分類 ---")

    # カテゴリ: テクノロジー、スポーツ、政治、経済、エンタメ
    examples = [
        ("Apple、新型iPhoneを発表。AIチップを搭載し処理速度が2倍に",
         "テクノロジー"),
        ("日本代表、W杯予選で3-0の快勝。次戦はブラジルと対戦",
         "スポーツ"),
        ("参議院選挙、与党が過半数を維持。野党は議席を増やす",
         "政治"),
        ("日経平均株価、3万5千円を突破。半導体株が牽引",
         "経済"),
        ("人気俳優が新映画主演決定。来年春に全国公開予定",
         "エンタメ"),
        ("Google、量子コンピューター新技術を発表。従来比100倍の性能",
         "テクノロジー"),
    ]

    test_headlines = [
        "テスラ、完全自動運転機能を日本市場で提供開始",
        "大谷翔平、今季30号ホームランを達成",
        "政府、来年度予算案を閣議決定。過去最大規模の110兆円",
        "人気バンドが解散を発表。ファンに衝撃走る",
    ]

    # Few-shotプロンプトを構築
    few_shot_prompt = (
        "ニュースの見出しを以下のカテゴリに分類してください:\n"
        "テクノロジー、スポーツ、政治、経済、エンタメ\n\n"
        "カテゴリ名のみを出力してください。\n\n"
    )

    for headline, category in examples:
        few_shot_prompt += f"見出し: {headline}\nカテゴリ: {category}\n\n"

    print("ニュース見出しを分類します:")
    for headline in test_headlines:
        prompt = few_shot_prompt + f"見出し: {headline}\nカテゴリ:"

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=20,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        category = response.content[0].text.strip()
        print(f"  [{category}] {headline}")


def text_summarization_few_shot(client: Anthropic) -> None:
    """
    Few-shot Learning を使ったテキスト要約の例

    長い文章を指定した形式・長さで要約します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Few-shot テキスト要約 ---")

    # 要約の例（入力文章と期待される要約）
    examples = [
        {
            "text": (
                "Pythonは1991年にGuido van Rossum氏によって開発された"
                "プログラミング言語です。シンプルで読みやすい文法が特徴で、"
                "機械学習、Web開発、データ分析など幅広い分野で使用されています。"
                "現在、世界で最も人気のあるプログラミング言語の一つです。"
            ),
            "summary": "Python: 1991年開発・シンプル文法・機械学習/Web/データ分析に広く使われる人気言語。"
        },
        {
            "text": (
                "機械学習とは、コンピュータがデータから自動的にパターンを学習する"
                "技術です。明示的にプログラムすることなく、大量のデータから"
                "規則性を発見し、予測や分類などのタスクを実行できるようになります。"
                "ディープラーニングはその一分野で、特に画像認識や自然言語処理で"
                "革新的な成果を上げています。"
            ),
            "summary": "機械学習: データからパターン自動学習・予測/分類を実現。DLは画像認識・NLPで顕著な成果。"
        },
    ]

    test_text = (
        "クラウドコンピューティングとは、インターネット経由でコンピュータ資源を"
        "提供するサービスです。サーバー、ストレージ、データベース、ネットワーキングなどの"
        "ITリソースをオンデマンドで利用できます。AWS、Google Cloud、Microsoft Azureが"
        "主要プロバイダーです。初期投資が不要で、使った分だけ料金が発生するため、"
        "スタートアップから大企業まで幅広く採用されています。"
    )

    # Few-shotプロンプトで要約の形式・スタイルを学習させる
    few_shot_prompt = (
        "以下の文章を1〜2文の簡潔な要約にしてください。"
        "重要なキーワードを含め、箇条書きではなく文として出力してください。\n\n"
    )

    for example in examples:
        few_shot_prompt += (
            f"文章: {example['text']}\n"
            f"要約: {example['summary']}\n\n"
        )

    prompt = few_shot_prompt + f"文章: {test_text}\n要約:"

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=150,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    print(f"元の文章:\n{test_text}\n")
    print(f"要約結果:\n{response.content[0].text}")


def few_shot_best_practices() -> None:
    """
    Few-shot Learning のベストプラクティスを表示する

    APIリクエストを行わず、ベストプラクティスの解説のみ行います
    """
    print("\n--- Few-shot のベストプラクティス ---")

    best_practices = """
【✅ 良いFew-shot例の条件】

1. 多様性を持たせる
   - すべてのカテゴリ・ケースをカバーする
   - 境界線上のケースも含める
   悪い例: ポジティブなレビューばかり5つ用意する
   良い例: ポジティブ2、ネガティブ2、ミックス1 をバランスよく用意する

2. 明確で典型的な例を使う
   - 曖昧さのない、明確なパターンの例を選ぶ
   - エッジケースより典型例を優先する

3. 例の順序に注意する
   - 最後の例がモデルに最も影響しやすい
   - ランダムに並べるか、多様性を意識して順序を決める

4. 適切な数の例を使う
   - 一般的に3〜8例が効果的
   - 例が多すぎるとトークン消費が増加し、重要な例が薄まる
   - 例が少なすぎるとパターンが不明確になる

5. タスクの説明も明確にする
   - 例だけでなく、タスクの説明（Zero-shot部分）も重要
   - 「何を」「どの形式で」出力するかを明示する

【💡 CCA試験のポイント】
- Few-shot は Fine-tuning よりも手軽にモデルの動作を調整できる
- 例の品質は量よりも重要（低品質な例は逆効果になることも）
- Few-shot はシステムプロンプトやXMLタグと組み合わせると効果的
- 出力形式の一貫性を確保するには Few-shot が特に有効

【⚠️ よくある間違い】

1. 偏った例
   → 一方のラベルの例ばかりを使うとバイアスが生じる

2. 矛盾する例
   → 同じ入力に異なる出力を示す例は混乱を招く

3. 例と実際のタスクの形式が異なる
   → 例は実際の入力と同じ形式・難易度にする

4. 例が長すぎる
   → 長すぎる例はトークンを消費し過ぎる。簡潔さを心がける
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 50)
    print("Few-shot Learning の実装")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    zero_shot_vs_few_shot_comparison(client)
    sentiment_analysis_few_shot(client)
    news_category_classification(client)
    text_summarization_few_shot(client)
    few_shot_best_practices()

    print("\n✅ 完了！次は03_chain_of_thought.pyに進んでください。")

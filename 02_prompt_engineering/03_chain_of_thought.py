"""
03_chain_of_thought.py - Chain of Thought プロンプティングの実装

このファイルの目的:
- Chain of Thought（CoT）プロンプティングの概念を理解する
- Zero-shot CoT と Few-shot CoT の実装方法を学ぶ
- 数学・論理・複雑な推論タスクへの応用を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/03_chain_of_thought.py
   または、コードをColabのセルに貼り付けて実行

【Chain of Thought（CoT）とは？】
Claudeに「ステップバイステップで考えさせる」ことで、
複雑な推論タスクの精度を大幅に向上させる技術です。

人間が難しい問題を解くとき、頭の中で段階的に考えるのと同じように、
AIモデルも中間的な推論ステップを踏むことでより正確な答えに辿り着けます。

【CoTの種類】
- Zero-shot CoT: 「ステップバイステップで考えてください」と指示するだけ
- Few-shot CoT:  段階的な推論の例をいくつか示してからタスクを実行させる
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


def zero_shot_cot_basic(client: Anthropic) -> None:
    """
    Zero-shot CoT の基本例

    「ステップバイステップで考えてください」という
    シンプルな一文でCoTを発動させます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Zero-shot CoT の基本 ---")

    math_problem = (
        "太郎さんは最初に50個のリンゴを持っていました。"
        "友達に15個あげ、その後お店で30個買いました。"
        "さらに妹から8個もらいました。"
        "最終的に太郎さんは何個のリンゴを持っていますか？"
    )

    # CoTなし: 直接答えを要求する
    print("【CoTなし】")
    response_no_cot = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=50,
        messages=[
            {"role": "user", "content": math_problem}
        ]
    )
    print(f"問題: {math_problem}")
    print(f"回答: {response_no_cot.content[0].text}")

    # Zero-shot CoT: 「ステップバイステップ」の一文を追加するだけ
    print("\n【Zero-shot CoT あり】")
    response_with_cot = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                # 「ステップバイステップで考えてください」が魔法の言葉
                "content": math_problem + "\n\nステップバイステップで考えてください。"
            }
        ]
    )
    print(f"問題: {math_problem}")
    print(f"回答:\n{response_with_cot.content[0].text}")


def zero_shot_cot_with_system(client: Anthropic) -> None:
    """
    システムプロンプトでZero-shot CoTを設定する例

    システムプロンプトにCoTの指示を入れることで、
    すべての質問に対して自動的に段階的推論を行わせます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- システムプロンプトによるZero-shot CoT ---")

    # システムプロンプトでCoTを常時有効化
    system_prompt = (
        "あなたは問題解決の専門家です。"
        "すべての問題に対して以下の手順で回答してください:\n"
        "1. 問題を整理する\n"
        "2. 解法を考える\n"
        "3. ステップバイステップで計算・推論する\n"
        "4. 最終的な答えを明確に示す\n"
        "中間の計算過程を省略しないでください。"
    )

    problems = [
        "1から100までの整数の合計はいくつですか？",
        "時速60kmで走る車が2時間30分で走れる距離は何kmですか？",
    ]

    for problem in problems:
        print(f"\n問題: {problem}")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            system=system_prompt,
            messages=[
                {"role": "user", "content": problem}
            ]
        )
        print(f"回答:\n{response.content[0].text}")
        print("-" * 40)


def few_shot_cot_math(client: Anthropic) -> None:
    """
    Few-shot CoT を使った数学の文章問題の例

    段階的な推論の例を示すことで、より精度の高い回答を得ます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Few-shot CoT: 数学の文章問題 ---")

    # Few-shot CoTの例（問題→段階的推論→答え）
    few_shot_examples = """以下の問題をステップバイステップで解いてください。

例1:
問題: リンゴが3袋あり、それぞれの袋に4個のリンゴが入っています。
      全部で何個のリンゴがありますか？
解法:
  ステップ1: 袋の数を確認する → 3袋
  ステップ2: 1袋あたりのリンゴの数を確認する → 4個
  ステップ3: 全体のリンゴの数を計算する → 3 × 4 = 12個
答え: 12個

例2:
問題: ある店でTシャツが1,200円、ズボンが2,800円です。
      3割引のセールをしています。
      Tシャツとズボンをそれぞれ1枚ずつ買うと合計いくらですか？
解法:
  ステップ1: 定価の合計を計算する → 1,200 + 2,800 = 4,000円
  ステップ2: 割引率を確認する → 30%引き = 70%の価格
  ステップ3: セール価格を計算する → 4,000 × 0.70 = 2,800円
答え: 2,800円

"""

    # 実際に解かせる問題
    test_problem = """問題: 花子さんは毎日30分間読書をします。
      1週間で何時間読書をしますか？
      また、1ヶ月（30日）では何時間になりますか？"""

    prompt = few_shot_examples + test_problem + "\n解法:"

    print(f"問題:\n{test_problem}\n")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=400,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(f"回答:\n{response.content[0].text}")


def few_shot_cot_logic_puzzle(client: Anthropic) -> None:
    """
    Few-shot CoT を使った論理パズルの例

    論理的な推論を段階的に示す例で、
    複雑な論理問題への対処法を学びます

    Args:
        client: Anthropicクライアント
    """
    print("\n--- Few-shot CoT: 論理パズル ---")

    few_shot_cot_prompt = """論理パズルを解いてください。各ステップを明確に示してください。

例:
パズル: AはBより背が高い。CはAより背が高い。BはDより背が高い。
        背の高い順に並べてください。
推論:
  ステップ1: 与えられた関係を整理する
    - A > B（AはBより高い）
    - C > A（CはAより高い）
    - B > D（BはDより高い）
  ステップ2: 推移的関係を導く
    - C > A > B > D
  ステップ3: 順序を確定する
    - 最も高い: C
    - 次に高い: A
    - 3番目: B
    - 最も低い: D
答え: C > A > B > D

問題: 田中さん、鈴木さん、佐藤さん、山田さんの4人がいます。
      田中さんは鈴木さんより年上です。
      佐藤さんは田中さんより年上です。
      山田さんは鈴木さんより年下です。
      年齢の高い順に並べてください。
推論:"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=400,
        messages=[
            {"role": "user", "content": few_shot_cot_prompt}
        ]
    )
    print(response.content[0].text)


def complex_reasoning_cot(client: Anthropic) -> None:
    """
    複雑な推論タスクにCoTを適用する例

    ビジネス上の意思決定など、多角的な判断が必要な
    複雑なタスクへのCoT適用方法を示します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 複雑な推論タスクへのCoT適用 ---")

    # 多段階の判断が必要なビジネスシナリオ
    system_prompt = (
        "あなたはビジネスアナリストです。"
        "意思決定を行う際は必ず以下のフレームワークを使用してください:\n"
        "1. 状況の把握: 与えられた情報を整理する\n"
        "2. 課題の特定: 主要な問題や目標を明確にする\n"
        "3. 選択肢の検討: 考えられる解決策を列挙する\n"
        "4. 評価: 各選択肢のメリット・デメリットを分析する\n"
        "5. 推奨事項: 最良の選択肢を根拠とともに提示する"
    )

    business_scenario = """
    状況: スタートアップ企業ABCは月間1,000万円の売上を達成しています。
    現在、以下の選択肢を検討しています:

    選択肢A: 新しい機能開発に500万円投資する
    - 開発期間: 3ヶ月
    - 期待売上増加率: 30%
    - リスク: 開発失敗の可能性20%

    選択肢B: マーケティングに500万円投資する
    - 効果発現期間: 1ヶ月
    - 期待売上増加率: 20%
    - リスク: 効果が薄い可能性30%

    選択肢C: 現状維持（投資なし）
    - リスク: 競合に顧客を奪われる可能性

    どの選択肢を推奨しますか？
    """

    print(f"シナリオ:\n{business_scenario}")
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=600,
        system=system_prompt,
        messages=[
            {"role": "user", "content": business_scenario}
        ]
    )
    print(f"分析結果:\n{response.content[0].text}")


def cot_best_practices() -> None:
    """
    Chain of Thought のベストプラクティスを表示する

    APIリクエストを行わず、ベストプラクティスの解説のみ行います
    """
    print("\n--- Chain of Thought のベストプラクティス ---")

    best_practices = """
【✅ CoTが効果的なタスクの種類】

1. 数学・計算問題
   - 四則演算を含む文章問題
   - 確率・統計の計算
   - 単位変換を含む問題

2. 論理推論
   - 三段論法・推移的関係
   - 仮説の検証
   - 条件付き命題

3. 多段階の判断
   - ビジネス意思決定
   - トラブルシューティング
   - リスク評価

4. コーディング・アルゴリズム
   - アルゴリズムの設計
   - バグの特定と修正
   - 計算量の分析

【💡 Zero-shot CoT vs Few-shot CoT の選択基準】

Zero-shot CoT（「ステップバイステップで」を追加するだけ）:
  ✅ タスクがシンプル・直感的な場合
  ✅ 素早くCoTを試したい場合
  ✅ トークンを節約したい場合

Few-shot CoT（推論ステップの例を提示）:
  ✅ 特定の形式・スタイルの推論が必要な場合
  ✅ 高い精度が求められる場合
  ✅ 複雑なドメイン知識が必要な場合

【⚠️ CoTが効果的でない場合】

- 単純な事実確認（「東京の首都は？」）
- 創作タスク（文章生成、詩の作成）
- 主観的な判断（デザインの好み）

【💡 CCA試験のポイント】
- CoTは「ステップバイステップで考えてください」という一文が効果的
- CoTを使うと回答が長くなるため、max_tokensを十分に設定する
- Few-shot CoTはZero-shot CoTより精度が高いが、トークンが増加する
- CoTとXMLタグを組み合わせると推論過程を整理しやすい

【CoTとXMLタグの組み合わせ例】

プロンプト:
<problem>
太郎さんは...
</problem>

<instructions>
上記の問題を<thinking>タグ内でステップバイステップに考え、
<answer>タグ内に最終的な答えのみを記載してください。
</instructions>

期待される出力:
<thinking>
ステップ1: ...
ステップ2: ...
</thinking>
<answer>
73個
</answer>
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 50)
    print("Chain of Thought プロンプティング")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    zero_shot_cot_basic(client)
    zero_shot_cot_with_system(client)
    few_shot_cot_math(client)
    few_shot_cot_logic_puzzle(client)
    complex_reasoning_cot(client)
    cot_best_practices()

    print("\n✅ 完了！次は04_xml_tags.pyに進んでください。")

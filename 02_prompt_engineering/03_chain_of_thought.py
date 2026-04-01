"""
03_chain_of_thought.py - Chain of Thought プロンプティング

このファイルの目的:
- Chain of Thought（CoT）プロンプティングの概念と実装を学ぶ
- 段階的な思考プロセスを引き出してClaudeの推論精度を向上させる
- 数学問題・論理パズルへの応用を習得する

【Google Colabでの実行方法】
1. 最初にこれを実行:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 02_prompt_engineering/03_chain_of_thought.py
   または、コードをColabのセルに貼り付けて実行

【CCA試験ポイント】
- CoT は複雑な推論タスクで特に効果的
- 「ステップバイステップで考えてください」がシンプルな CoT 指示
- Zero-shot CoT: 例なしで思考ステップを要求する
- Few-shot CoT: 思考プロセスの例を示す
- 最終的な答えを明示させることで精度が向上する
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


def solve_without_cot(client: Anthropic, problem: str) -> str:
    """
    CoT なしでの問題解決（比較用）

    直接答えを求めると誤りが生じやすい。

    Args:
        client: Anthropicクライアント
        problem: 解くべき問題

    Returns:
        str: Claudeの回答
    """
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=128,
        messages=[
            {"role": "user", "content": problem}
        ]
    )
    return message.content[0].text


def solve_with_zero_shot_cot(client: Anthropic, problem: str) -> str:
    """
    Zero-shot CoT での問題解決

    「ステップバイステップで考えてください」を追加するだけで
    推論の質が大きく向上する。これが Zero-shot CoT。

    Args:
        client: Anthropicクライアント
        problem: 解くべき問題

    Returns:
        str: ステップごとの思考プロセスと最終回答
    """
    # 「ステップバイステップ」の指示を追加するだけ
    prompt = f"{problem}\n\nステップバイステップで考えて、最後に【答え】を明示してください。"

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def solve_with_few_shot_cot(client: Anthropic, problem: str) -> str:
    """
    Few-shot CoT での問題解決

    思考プロセスの例を示すことで、より構造化された
    推論を引き出す。複雑な問題に特に効果的。

    Args:
        client: Anthropicクライアント
        problem: 解くべき問題

    Returns:
        str: 構造化された思考プロセスと最終回答
    """
    # システムプロンプトで思考のスタイルを定義
    system = (
        "あなたは数学と論理の問題を解く専門家です。"
        "問題を解くとき、必ず以下の形式で回答してください：\n\n"
        "【思考プロセス】\n"
        "ステップ1: ...\n"
        "ステップ2: ...\n"
        "（必要なだけステップを続ける）\n\n"
        "【答え】\n"
        "（最終的な答えのみを記載）"
    )

    # Few-shot の例
    messages = [
        # 例1: 簡単な数学問題
        {
            "role": "user",
            "content": "りんごが3個、みかんが5個あります。合わせて何個ですか？"
        },
        {
            "role": "assistant",
            "content": (
                "【思考プロセス】\n"
                "ステップ1: りんごの数を確認する → 3個\n"
                "ステップ2: みかんの数を確認する → 5個\n"
                "ステップ3: 合計を計算する → 3 + 5 = 8\n\n"
                "【答え】\n"
                "8個"
            )
        },
        # 例2: 文章問題
        {
            "role": "user",
            "content": (
                "太郎君は毎分80mの速さで歩きます。"
                "学校まで2400mの距離があります。"
                "家を8時00分に出発すると、学校に着くのは何時何分ですか？"
            )
        },
        {
            "role": "assistant",
            "content": (
                "【思考プロセス】\n"
                "ステップ1: 速さを確認する → 80m/分\n"
                "ステップ2: 距離を確認する → 2400m\n"
                "ステップ3: 時間を計算する → 2400 ÷ 80 = 30分\n"
                "ステップ4: 到着時刻を計算する → 8時00分 + 30分 = 8時30分\n\n"
                "【答え】\n"
                "8時30分"
            )
        },
        # 実際の問題
        {
            "role": "user",
            "content": problem
        }
    ]

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system=system,
        messages=messages
    )
    return message.content[0].text


def solve_logic_puzzle(client: Anthropic) -> str:
    """
    論理パズルを CoT で解く

    CoT は論理的な推論を必要とするパズルや
    複数の条件を整理するタスクでも非常に効果的。

    Args:
        client: Anthropicクライアント

    Returns:
        str: 推論プロセスと答え
    """
    puzzle = """
3人の友人（田中、鈴木、佐藤）がそれぞれ異なる職業（医者、弁護士、エンジニア）に就いています。

手がかり:
1. 田中は医者ではない
2. 鈴木はエンジニアではない
3. 佐藤は弁護士ではない

それぞれの職業は何ですか？
"""

    prompt = f"{puzzle}\n\nステップバイステップで論理的に考え、最後に【答え】を明示してください。"

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def solve_business_analysis(client: Anthropic) -> str:
    """
    ビジネス分析を CoT で行う

    複雑なビジネス判断でも CoT を使うことで
    より信頼性の高い分析が得られる。

    Args:
        client: Anthropicクライアント

    Returns:
        str: 分析プロセスと推奨事項
    """
    scenario = """
あるECサイトで以下のデータがあります:
- 月間訪問者数: 10,000人
- コンバージョン率: 2%
- 平均注文金額: 5,000円
- 顧客獲得コスト（CAC）: 2,000円

新しいUI改善施策のコストは月間50万円で、
コンバージョン率が3%に向上すると予測されています。

この施策を実施すべきでしょうか？
"""

    prompt = f"{scenario}\n\nROIを計算するためにステップバイステップで考え、【推奨判断】を示してください。"

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


if __name__ == "__main__":
    print("=" * 60)
    print("Chain of Thought プロンプティング")
    print("=" * 60)

    client = get_client()

    # --- 数学問題: CoT あり/なしの比較 ---
    math_problem = (
        "花子さんはケーキを作るために卵を買いに行きました。"
        "1個のケーキに卵が3個必要で、5個のケーキを作りたいです。"
        "卵は6個入りパックで1パック300円です。"
        "必要な卵の数と、最小費用はいくらですか？"
    )

    print("\n【数学問題: CoT なし vs Zero-shot CoT の比較】")
    print(f"問題: {math_problem}")

    print("\n--- CoT なし ---")
    answer_no_cot = solve_without_cot(client, math_problem)
    print(answer_no_cot)

    print("\n--- Zero-shot CoT あり ---")
    answer_with_cot = solve_with_zero_shot_cot(client, math_problem)
    print(answer_with_cot)

    # --- Few-shot CoT での問題解決 ---
    print("\n\n【Few-shot CoT: 速さと距離の問題】")
    distance_problem = (
        "新幹線は時速300kmで走ります。"
        "東京から大阪まで500kmの距離があります。"
        "東京を10時00分に出発すると大阪に到着するのは何時何分ですか？"
    )
    print(f"問題: {distance_problem}")
    print("\n回答:")
    print(solve_with_few_shot_cot(client, distance_problem))

    # --- 論理パズル ---
    print("\n\n【論理パズル（CoT）】")
    print(solve_logic_puzzle(client))

    # --- ビジネス分析 ---
    print("\n\n【ビジネス分析（CoT）】")
    print(solve_business_analysis(client))

    print("\n✅ 完了！次は04_xml_tags.pyに進んでください。")

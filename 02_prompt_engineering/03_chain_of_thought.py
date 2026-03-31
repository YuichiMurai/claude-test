"""
03_chain_of_thought.py - 思考の連鎖（Chain of Thought）プロンプティング

このファイルでは以下を学びます：
- Chain of Thought（CoT）の基本概念と実装
- ステップバイステップで問題を解く手法
- 数学の問題や論理パズルへの応用
- Zero-shot CoT と Few-shot CoT の違い
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def solve_without_cot(client: Anthropic, problem: str) -> str:
    """
    CoTなしで問題を解く（比較用）。

    直接答えを求めるプロンプトを使用する。

    Args:
        client: Anthropicクライアント
        problem: 解く問題のテキスト

    Returns:
        str: 回答
    """
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=64,
        system="問題に対する最終的な答えのみを簡潔に出力してください。",
        messages=[{"role": "user", "content": problem}],
    )
    return response.content[0].text.strip()


def zero_shot_cot(client: Anthropic, problem: str) -> str:
    """
    Zero-shot CoT: 「ステップバイステップで考えてください」を追加するだけ。

    最もシンプルなCoTの実装。「Let's think step by step」や
    「ステップバイステップで考えてください」を追加するだけで
    推論の精度が向上することが知られている。

    Args:
        client: Anthropicクライアント
        problem: 解く問題のテキスト

    Returns:
        str: 思考過程と回答
    """
    # 「ステップバイステップで考えてください」を付加するだけでCoT効果が得られる
    cot_prompt = f"{problem}\n\nステップバイステップで考えてください。"

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system="数学の問題を解く際は、各ステップを明確に示してください。",
        messages=[{"role": "user", "content": cot_prompt}],
    )
    return response.content[0].text


def few_shot_cot_math(client: Anthropic, problem: str) -> str:
    """
    Few-shot CoT: 思考過程の例示を含む数学問題の解法。

    思考過程を含む例示を事前に提示することで、
    モデルが同様のステップで解くよう誘導する。

    Args:
        client: Anthropicクライアント
        problem: 解く問題のテキスト

    Returns:
        str: 思考過程と回答
    """
    messages = [
        # 例1: 文章題
        {
            "role": "user",
            "content": "リンゴが5個入った袋が3袋あり、さらにバラ売りのリンゴが4個あります。全部で何個ですか？",
        },
        {
            "role": "assistant",
            "content": (
                "ステップ1: 袋に入ったリンゴの数を計算します。\n"
                "  5個 × 3袋 = 15個\n\n"
                "ステップ2: バラ売りのリンゴを加えます。\n"
                "  15個 + 4個 = 19個\n\n"
                "答え: 19個"
            ),
        },
        # 例2: 割引の計算
        {
            "role": "user",
            "content": "定価3,000円の商品が20%オフで売られています。さらに会員割引で5%引きになる場合、最終的な価格はいくらですか？",
        },
        {
            "role": "assistant",
            "content": (
                "ステップ1: 20%オフの価格を計算します。\n"
                "  3,000円 × (1 - 0.20) = 3,000円 × 0.80 = 2,400円\n\n"
                "ステップ2: さらに5%引きを計算します。\n"
                "  2,400円 × (1 - 0.05) = 2,400円 × 0.95 = 2,280円\n\n"
                "答え: 2,280円"
            ),
        },
        # 実際の問題
        {"role": "user", "content": problem},
    ]

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system="数学の問題をステップバイステップで解いてください。",
        messages=messages,
    )
    return response.content[0].text


def logic_puzzle_with_cot(client: Anthropic, puzzle: str) -> str:
    """
    論理パズルをCoTで解く。

    推論が必要な問題に対して、CoTを使って
    思考過程を明示化することで精度を向上させる。

    Args:
        client: Anthropicクライアント
        puzzle: 論理パズルのテキスト

    Returns:
        str: 思考過程と答え
    """
    system_prompt = """論理パズルを解く際は、以下の手順で考えてください：

1. 与えられた条件を整理する
2. 各条件から導ける事実を導出する
3. 矛盾がないか確認する
4. 最終的な答えを明示する

途中の思考過程を詳しく示してください。"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=768,
        system=system_prompt,
        messages=[{"role": "user", "content": puzzle}],
    )
    return response.content[0].text


def structured_reasoning(client: Anthropic, question: str) -> dict:
    """
    構造化された思考プロセスで複雑な問題を解く。

    XMLタグや明確な区切りを使って、
    思考過程と結論を分けて出力させる。

    Args:
        client: Anthropicクライアント
        question: 分析する問題や質問

    Returns:
        dict: 思考過程と結論を含む辞書
    """
    system_prompt = """問題を分析する際は、以下の形式で回答してください：

<thinking>
問題の分析と思考過程をここに書く
</thinking>

<answer>
最終的な結論をここに書く
</answer>"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": question}],
    )

    text = response.content[0].text

    # thinkingとanswerを抽出
    thinking = ""
    answer = ""

    if "<thinking>" in text and "</thinking>" in text:
        start = text.index("<thinking>") + len("<thinking>")
        end = text.index("</thinking>")
        thinking = text[start:end].strip()

    if "<answer>" in text and "</answer>" in text:
        start = text.index("<answer>") + len("<answer>")
        end = text.index("</answer>")
        answer = text[start:end].strip()

    return {"thinking": thinking, "answer": answer, "full_response": text}


def main() -> None:
    """メイン処理：Chain of Thoughtの各テクニックを実演。"""
    load_dotenv()
    client = Anthropic()

    print("=== Chain of Thought（思考の連鎖）プロンプティング ===\n")

    # CoTありとなしの比較
    print("【CoTなし vs Zero-shot CoT の比較】\n")
    math_problem = (
        "ある工場では1時間に120個の製品を作れます。"
        "8時間の作業で目標の800個を達成するには、"
        "最初の3時間で何個作る必要がありますか？"
    )
    print(f"問題: {math_problem}\n")

    print("CoTなし（直接回答）:")
    answer_no_cot = solve_without_cot(client, math_problem)
    print(f"{answer_no_cot}\n")

    print("Zero-shot CoT（ステップバイステップ）:")
    answer_cot = zero_shot_cot(client, math_problem)
    print(f"{answer_cot}\n")

    # Few-shot CoT の数学問題
    print("【Few-shot CoT: 数学問題】\n")
    word_problems = [
        "スーパーでトマトが1個80円、きゅうりが1本60円で売っています。トマト4個とキュウリ6本を買い、1,000円を出した場合、おつりはいくらですか？",
        "電車が時速120kmで走っています。東京から大阪まで550kmある場合、途中30分の停車を含めると何時間何分かかりますか？",
    ]

    for problem in word_problems:
        print(f"問題: {problem}")
        solution = few_shot_cot_math(client, problem)
        print(f"解法:\n{solution}\n")
        print("-" * 60)

    # 論理パズル
    print("\n【論理パズル with CoT】\n")
    puzzle = """
    A, B, C, D の4人が並んでいます。
    - AはBより前にいます
    - CはDより後ろにいます
    - BはCより前にいます
    - AはDより後ろにいます

    前から順番に並んでいる順序を答えてください。
    """
    print(f"パズル: {puzzle}")
    solution = logic_puzzle_with_cot(client, puzzle)
    print(f"解答:\n{solution}\n")

    # 構造化された思考プロセス
    print("【構造化思考: ビジネス分析】\n")
    business_question = (
        "スタートアップが新しいSaaSプロダクトを市場に投入する際、"
        "最初の6ヶ月で取るべき最優先事項は何ですか？"
    )
    print(f"質問: {business_question}\n")

    result = structured_reasoning(client, business_question)
    print("思考過程:")
    print(result["thinking"])
    print("\n結論:")
    print(result["answer"])

    print("\n\n【まとめ: Chain of Thoughtのポイント】")
    print("1. Zero-shot CoT: 「ステップバイステップで」を追加するだけで効果的")
    print("2. Few-shot CoT: 思考過程の例示を提供するとより精度が上がる")
    print("3. 複雑な推論問題（数学、論理パズル）に特に有効")
    print("4. 思考過程を表示させることでデバッグや検証が容易になる")
    print("5. トークン消費は増えるが、精度向上のトレードオフとして合理的")


if __name__ == "__main__":
    main()

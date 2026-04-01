"""
exercise_03.py - 練習問題3: コスト最適化システム

難易度: ⭐⭐⭐ 中上級
目的: トークン管理とコスト最適化を実装した予算管理付き会話システムを作成する

【課題】
以下の機能を持つCostOptimizedChatクラスを完成させてください:
1. トークン数のカウント（概算）
2. コスト計算と予算管理（予算超過時は警告・停止）
3. 会話履歴の効率的な管理（トークン予算を超えたら古い履歴を削除）
4. max_tokens の動的調整（予算残量に応じて調整）
5. コスト削減戦略の実装

【期待される出力】
============================================================
コスト最適化チャットシステム
============================================================
予算: $0.01 | モデル: claude-sonnet-4-20250514

--- 会話1 ---
ユーザー: Pythonとは？
  推定入力: 12トークン
  実際 → 入力: 18トークン, 出力: 42トークン, コスト: $0.000684
  累積: $0.000684 (6.8% 使用)
Claude: Pythonはシンプルな文法...

--- 会話2 ---
ユーザー: その特徴を詳しく
  推定入力: 75トークン（履歴込み）
  実際 → 入力: 82トークン, 出力: 95トークン, コスト: $0.001671
  累積: $0.002355 (23.6% 使用)
Claude: Pythonの主な特徴は...

--- 会話3（予算80%超過時の動的調整） ---
ユーザー: もっと詳しく
  ⚠️  予算の80%を超えました。max_tokensを削減します: 1024 → 200
  実際 → 入力: 160トークン, 出力: 48トークン, コスト: $0.001200
  累積: $0.009000 (90.0% 使用)

=== 最終コストレポート ===
総会話ターン: 3
総入力トークン: 260
総出力トークン: 185
総コスト: $0.009000
予算: $0.01
残余予算: $0.001000
コスト削減率: 0% (ベースラインと比較)

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
"""

import os
import re
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic

# 使用するモデル名
MODEL_NAME = "claude-sonnet-4-20250514"

# コスト設定（USD / 1Mトークン）
COST_PER_MILLION_INPUT = 3.00
COST_PER_MILLION_OUTPUT = 15.00

# トークン管理の設定
DEFAULT_MAX_TOKENS = 1024      # デフォルトの最大出力トークン数
REDUCED_MAX_TOKENS = 200       # 予算節約モードの最大出力トークン数
HISTORY_TOKEN_BUDGET = 2000    # 会話履歴のトークン予算
BUDGET_WARNING_THRESHOLD = 0.8  # 予算警告の閾値（80%）


def get_client() -> Anthropic:
    """APIクライアントを取得する（Colab・ローカル両対応）"""
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return Anthropic(api_key=api_key)


@dataclass
class TurnCost:
    """1ターンのコスト情報"""
    turn_number: int
    user_message: str
    input_tokens: int
    output_tokens: int

    @property
    def cost_usd(self) -> float:
        """このターンのコスト（USD）"""
        input_cost = (self.input_tokens / 1_000_000) * COST_PER_MILLION_INPUT
        output_cost = (self.output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT
        return input_cost + output_cost

    def __str__(self) -> str:
        return (
            f"入力: {self.input_tokens}トークン, "
            f"出力: {self.output_tokens}トークン, "
            f"コスト: ${self.cost_usd:.6f}"
        )


def estimate_tokens(text: str) -> int:
    """
    テキストのトークン数を概算する

    Args:
        text: テキスト

    Returns:
        int: 概算トークン数

    TODO: 以下の方法でトークン数を概算してください
    1. 英語部分: 英単語数 × 1.3
    2. 日本語部分: 日本語文字数 × 1.5
    3. その他（数字・記号等）: 文字数 × 0.5
    4. 合計の切り上げ（最低1）

    ヒント:
    - import re
    - re.findall(r'[a-zA-Z]+', text) で英単語を取得
    - re.findall(r'[^\x00-\x7F]', text) で非ASCII文字を取得
    """
    # TODO: ここに実装してください
    # 仮の実装（単純な文字数 / 4）
    return max(1, len(text) // 4)


def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    トークン数からコストを計算する

    Args:
        input_tokens: 入力トークン数
        output_tokens: 出力トークン数

    Returns:
        float: コスト（USD）

    TODO: 以下の計算式を実装してください
    - 入力コスト = (input_tokens / 1,000,000) × COST_PER_MILLION_INPUT
    - 出力コスト = (output_tokens / 1,000,000) × COST_PER_MILLION_OUTPUT
    - 合計コスト = 入力コスト + 出力コスト
    """
    # TODO: ここに実装してください
    return 0.0  # 仮の実装


class CostOptimizedChat:
    """
    コスト最適化機能を持つチャットクラス

    TODO: このクラスの以下のメソッドを実装してください:
    1. _trim_history(): トークン予算超過時に古い履歴を削除
    2. _get_dynamic_max_tokens(): 予算残量に応じて max_tokens を調整
    3. chat(): コスト追跡付きチャット関数
    """

    def __init__(self, client: Anthropic, budget_usd: float = 0.01) -> None:
        """
        コスト最適化チャットを初期化する

        Args:
            client: Anthropicクライアント
            budget_usd: 予算（USD）
        """
        self.client = client
        self.budget_usd = budget_usd
        self.messages: list[dict] = []
        self.turn_costs: list[TurnCost] = []
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0

    @property
    def total_cost(self) -> float:
        """累積コスト（USD）"""
        return calculate_cost(self.total_input_tokens, self.total_output_tokens)

    @property
    def budget_used_ratio(self) -> float:
        """予算使用率（0.0〜1.0）"""
        if self.budget_usd <= 0:
            return 1.0
        return min(1.0, self.total_cost / self.budget_usd)

    @property
    def remaining_budget(self) -> float:
        """残余予算（USD）"""
        return max(0.0, self.budget_usd - self.total_cost)

    def estimate_history_tokens(self) -> int:
        """
        現在の会話履歴の推定トークン数を計算する

        Returns:
            int: 推定トークン数

        TODO: 以下を実装してください
        1. messages の各エントリの content を estimate_tokens() で推定
        2. メッセージごとに 4 トークンのオーバーヘッドを追加
        3. 合計を返す

        ヒント:
        - for msg in self.messages:
        -     total += estimate_tokens(msg.get("content", "")) + 4
        """
        # TODO: ここに実装してください
        return 0  # 仮の実装

    def _trim_history(self) -> int:
        """
        トークン予算を超えた場合に古い会話を削除する

        Returns:
            int: 削除したメッセージ数

        TODO: 以下を実装してください
        1. self.estimate_history_tokens() が HISTORY_TOKEN_BUDGET を超えている間ループ
        2. len(self.messages) > 2 の間だけ削除（最新の1ターンは残す）
        3. self.messages の先頭から削除する（pop(0)）
        4. 削除した後、先頭が "assistant" なら追加で削除（孤立メッセージを防ぐ）
        5. 削除件数を返す

        ヒント:
        - removed = 0
        - while self.estimate_history_tokens() > HISTORY_TOKEN_BUDGET and len(self.messages) > 2:
        -     self.messages.pop(0)
        -     removed += 1
        -     if self.messages and self.messages[0]["role"] == "assistant":
        -         self.messages.pop(0)
        -         removed += 1
        """
        # TODO: ここに実装してください
        return 0  # 仮の実装

    def _get_dynamic_max_tokens(self) -> int:
        """
        予算残量に応じて max_tokens を動的に調整する

        Returns:
            int: 調整された max_tokens

        TODO: 以下のロジックを実装してください
        1. budget_used_ratio が BUDGET_WARNING_THRESHOLD（0.8）を超えている場合:
           - 警告メッセージを表示: "⚠️  予算の80%を超えました。max_tokensを削減します"
           - REDUCED_MAX_TOKENS を返す
        2. それ以外は DEFAULT_MAX_TOKENS を返す

        ヒント:
        - if self.budget_used_ratio >= BUDGET_WARNING_THRESHOLD:
        """
        # TODO: ここに実装してください
        return DEFAULT_MAX_TOKENS  # 仮の実装

    def chat(self, user_message: str, system: Optional[str] = None) -> Optional[str]:
        """
        コスト最適化チャット

        Args:
            user_message: ユーザーメッセージ
            system: システムプロンプト

        Returns:
            Optional[str]: 応答テキスト、または None（予算超過・エラー時）

        TODO: 以下のフローを実装してください
        1. 予算チェック: budget_used_ratio >= 1.0 なら "❌ 予算を使い切りました" を表示して None を返す
        2. 動的 max_tokens を取得: _get_dynamic_max_tokens()
        3. 推定入力トークン数を表示
           - 現在の履歴 + 新しいユーザーメッセージの推定トークン数
           - print(f"  推定入力: {estimated}トークン")
        4. messages にユーザーメッセージを追加
        5. API リクエストを送信
        6. 成功時:
           - TurnCost を作成して turn_costs に追加
           - total_input_tokens, total_output_tokens を更新
           - コスト情報を表示
             例: "  実際 → 入力: Xトークン, 出力: Yトークン, コスト: $Z"
             例: "  累積: $A (B% 使用)"
           - messages にアシスタントの応答を追加
           - _trim_history() でトリミング
           - 応答テキストを返す
        7. エラー時: None を返す

        ヒント:
        - turn_number = len(self.turn_costs) + 1
        - current_msgs = self.messages + [{"role": "user", "content": user_message}]
        - estimated = sum(estimate_tokens(m["content"]) + 4 for m in current_msgs)
        - response = self.client.messages.create(model=MODEL_NAME, ...)
        - response.usage.input_tokens と response.usage.output_tokens でトークン数を取得
        """
        # TODO: ここに実装してください
        pass

    def cost_report(self) -> str:
        """
        コストレポートを生成する

        Returns:
            str: コストレポート文字列

        TODO: 以下の情報を含むレポートを作成してください
        - 総会話ターン数: len(self.turn_costs)
        - 総入力トークン数: total_input_tokens
        - 総出力トークン数: total_output_tokens
        - 総コスト: total_cost
        - 予算: budget_usd
        - 残余予算: remaining_budget
        - 予算使用率: budget_used_ratio * 100

        ヒント:
        - f-string でフォーマット
        - ${value:.6f} で小数点6桁
        """
        # TODO: ここに実装してください
        return "コストレポートは未実装です"  # 仮の実装


def run_demo(client: Anthropic) -> None:
    """
    デモを実行する

    Args:
        client: Anthropicクライアント
    """
    print("=" * 60)
    print("コスト最適化チャットシステム")
    print("=" * 60)

    # 少ない予算でデモ（実際の学習ではここの値を調整）
    budget = 0.01  # $0.01
    chat_system = CostOptimizedChat(client, budget_usd=budget)

    print(f"予算: ${budget:.2f} | モデル: {MODEL_NAME}\n")

    system_prompt = (
        "あなたは簡潔に答えるアシスタントです。"
        "回答は100文字以内にしてください。"
    )

    # 会話シナリオ
    conversation = [
        "Pythonとは何ですか？",
        "その主な用途は？",
        "初心者におすすめのリソースは？",
        "最初に学ぶべきことは？",
        "学習期間はどのくらいですか？",
    ]

    for i, user_msg in enumerate(conversation, 1):
        print(f"\n--- 会話 {i} ---")
        print(f"ユーザー: {user_msg}")

        response = chat_system.chat(user_msg, system=system_prompt)
        if response:
            print(f"Claude: {response}")
        else:
            print("（応答なし）")
            break

    # コストレポート
    print(f"\n{chat_system.cost_report()}")


if __name__ == "__main__":
    client = get_client()
    run_demo(client)

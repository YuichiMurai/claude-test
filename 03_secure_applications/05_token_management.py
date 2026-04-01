"""
05_token_management.py - トークン管理とコスト最適化

このファイルの目的:
- トークン数のカウント方法を学ぶ
- APIコストの計算と予算管理の実装を理解する
- max_tokensの動的調整方法を習得する
- 会話履歴のトークン管理を実装する
- コスト最適化戦略を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行
   または: !python 03_secure_applications/05_token_management.py

【トークンとは？】
Claudeは入力も出力も「トークン」という単位で処理します。
- 日本語: 1文字 ≈ 1〜2トークン
- 英語: 1単語 ≈ 1〜1.5トークン
- APIのコストはトークン数に比例するため、トークン管理は直接コストに影響します

【コスト構造（claude-sonnet-4-20250514 の目安）】
- 入力トークン: $3.00 / 1Mトークン
- 出力トークン: $15.00 / 1Mトークン
※ 実際の価格は Anthropic の公式サイトを確認してください
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"

# コスト設定（USD / 1Mトークン）
# 実際の価格は https://www.anthropic.com/pricing を確認
COST_PER_MILLION_INPUT_TOKENS = 3.00    # 入力トークンの単価
COST_PER_MILLION_OUTPUT_TOKENS = 15.00  # 出力トークンの単価

# トークン管理のパラメータ
CONTEXT_WINDOW_LIMIT = 200000  # claude-sonnet-4 のコンテキストウィンドウ上限
MAX_TOKENS_DEFAULT = 1024      # デフォルトのmax_tokens
HISTORY_TOKEN_BUDGET = 4000    # 会話履歴に使えるトークン予算


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
class TokenUsage:
    """1回のAPIコールのトークン使用量"""
    input_tokens: int = 0   # 入力トークン数
    output_tokens: int = 0  # 出力トークン数

    @property
    def total_tokens(self) -> int:
        """合計トークン数"""
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        """概算コスト（USD）"""
        input_cost = (self.input_tokens / 1_000_000) * COST_PER_MILLION_INPUT_TOKENS
        output_cost = (self.output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost

    def __str__(self) -> str:
        return (
            f"入力: {self.input_tokens:,} トークン, "
            f"出力: {self.output_tokens:,} トークン, "
            f"合計: {self.total_tokens:,} トークン, "
            f"コスト: ${self.cost_usd:.6f}"
        )


@dataclass
class CostTracker:
    """APIコストを累積追跡するクラス"""
    budget_usd: float = 1.0          # 予算（USD）
    total_input_tokens: int = 0      # 累積入力トークン数
    total_output_tokens: int = 0     # 累積出力トークン数
    total_requests: int = 0          # 総リクエスト数
    usage_history: list[TokenUsage] = field(default_factory=list)

    @property
    def total_cost_usd(self) -> float:
        """累積コスト（USD）"""
        input_cost = (self.total_input_tokens / 1_000_000) * COST_PER_MILLION_INPUT_TOKENS
        output_cost = (self.total_output_tokens / 1_000_000) * COST_PER_MILLION_OUTPUT_TOKENS
        return input_cost + output_cost

    @property
    def remaining_budget(self) -> float:
        """残余予算（USD）"""
        return max(0.0, self.budget_usd - self.total_cost_usd)

    @property
    def budget_used_percent(self) -> float:
        """予算使用率（%）"""
        if self.budget_usd <= 0:
            return 100.0
        return min(100.0, (self.total_cost_usd / self.budget_usd) * 100)

    def is_within_budget(self, safety_margin: float = 0.1) -> bool:
        """
        予算内かどうかを確認する

        Args:
            safety_margin: 安全マージン（予算の何%を残すか）

        Returns:
            bool: 予算内の場合True
        """
        return self.budget_used_percent < (100.0 - safety_margin * 100)

    def record(self, usage: TokenUsage) -> None:
        """使用量を記録する"""
        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.total_requests += 1
        self.usage_history.append(usage)

    def summary(self) -> str:
        """コストサマリーを返す"""
        return (
            f"=== コストサマリー ===\n"
            f"総リクエスト数: {self.total_requests}\n"
            f"入力トークン: {self.total_input_tokens:,}\n"
            f"出力トークン: {self.total_output_tokens:,}\n"
            f"合計トークン: {self.total_input_tokens + self.total_output_tokens:,}\n"
            f"累積コスト: ${self.total_cost_usd:.6f}\n"
            f"予算: ${self.budget_usd:.2f}\n"
            f"残余予算: ${self.remaining_budget:.6f}\n"
            f"予算使用率: {self.budget_used_percent:.1f}%"
        )


def estimate_token_count(text: str) -> int:
    """
    テキストのトークン数を概算する

    注意: これはあくまで概算です。正確なトークン数はAPIが計算します。
    日本語・英語混在テキストの場合の目安:
    - 英語: 1単語 ≈ 1.3トークン
    - 日本語: 1文字 ≈ 1.5トークン

    正確なカウントには client.beta.messages.count_tokens() を使用できます。

    Args:
        text: テキスト

    Returns:
        int: 概算トークン数
    """
    # 英語部分（ASCII文字）
    import re
    english_words = re.findall(r'[a-zA-Z]+', text)
    english_token_estimate = int(len(english_words) * 1.3)

    # 日本語部分（非ASCII文字）
    non_ascii_chars = re.findall(r'[^\x00-\x7F]', text)
    japanese_token_estimate = int(len(non_ascii_chars) * 1.5)

    # 記号や数字
    other_chars = len(text) - len(''.join(english_words)) - len(''.join(non_ascii_chars))
    other_token_estimate = int(other_chars * 0.5)

    return max(1, english_token_estimate + japanese_token_estimate + other_token_estimate)


def count_tokens_exact(client: Anthropic, messages: list[dict],
                        system: Optional[str] = None) -> int:
    """
    Anthropic APIを使ってトークン数を正確にカウントする

    注意: このAPIコールにもトークンが消費されます（少量）

    Args:
        client: Anthropicクライアント
        messages: メッセージリスト
        system: システムプロンプト

    Returns:
        int: 正確なトークン数
    """
    try:
        params: dict = {
            "model": MODEL_NAME,
            "messages": messages,
        }
        if system:
            params["system"] = system

        response = client.messages.count_tokens(**params)
        return response.input_tokens
    except Exception as e:
        # count_tokens が使えない場合は概算を返す
        print(f"  ⚠️  正確なカウントに失敗、概算を使用: {e}")
        total_text = " ".join(
            msg.get("content", "") if isinstance(msg.get("content"), str)
            else str(msg.get("content", ""))
            for msg in messages
        )
        if system:
            total_text += " " + system
        return estimate_token_count(total_text)


class ConversationManager:
    """
    会話履歴のトークン管理クラス

    長い会話では履歴が増えすぎてコンテキストウィンドウを超えることがあります。
    このクラスはトークン予算内で会話履歴を管理します。
    """

    def __init__(
        self,
        token_budget: int = HISTORY_TOKEN_BUDGET,
        system_prompt: Optional[str] = None
    ) -> None:
        """
        会話マネージャーを初期化する

        Args:
            token_budget: 会話履歴に使えるトークン予算
            system_prompt: システムプロンプト
        """
        self.token_budget = token_budget
        self.system_prompt = system_prompt
        self.messages: list[dict] = []
        self.cost_tracker = CostTracker()

    def estimate_messages_tokens(self) -> int:
        """現在の会話履歴の概算トークン数"""
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += estimate_token_count(content)
            total += 4  # メッセージのオーバーヘッド
        if self.system_prompt:
            total += estimate_token_count(self.system_prompt)
        return total

    def trim_history(self) -> int:
        """
        トークン予算を超えた場合に古い会話を削除する

        先頭のメッセージペア（user + assistant）を削除していきます。
        最新のコンテキストを保持するため、最後のメッセージは保持します。

        Returns:
            int: 削除したメッセージ数
        """
        removed = 0
        while self.estimate_messages_tokens() > self.token_budget and len(self.messages) > 2:
            # 最初のメッセージペア（user + assistant）を削除
            self.messages.pop(0)
            if self.messages and self.messages[0].get("role") == "assistant":
                self.messages.pop(0)
                removed += 2
            else:
                removed += 1

        return removed

    def add_turn(self, user_message: str, assistant_response: str,
                 usage: Optional[TokenUsage] = None) -> None:
        """
        会話のターンを追加する

        Args:
            user_message: ユーザーのメッセージ
            assistant_response: アシスタントの応答
            usage: トークン使用量（あれば記録）
        """
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": assistant_response})

        if usage:
            self.cost_tracker.record(usage)

        # トークン予算を超えた場合はトリミング
        trimmed = self.trim_history()
        if trimmed > 0:
            print(f"  📝 トークン予算超過のため、古い会話 {trimmed} メッセージを削除しました")

    def chat(self, client: Anthropic, user_message: str) -> str:
        """
        会話を行い、履歴を管理する

        Args:
            client: Anthropicクライアント
            user_message: ユーザーのメッセージ

        Returns:
            str: アシスタントの応答
        """
        # 予算チェック
        if not self.cost_tracker.is_within_budget():
            return "❌ 予算を超過しています。会話を継続できません。"

        # 現在のメッセージ履歴にユーザーメッセージを追加
        current_messages = self.messages + [{"role": "user", "content": user_message}]

        request_params: dict = {
            "model": MODEL_NAME,
            "max_tokens": MAX_TOKENS_DEFAULT,
            "messages": current_messages,
        }
        if self.system_prompt:
            request_params["system"] = self.system_prompt

        try:
            response = client.messages.create(**request_params)
            assistant_text = response.content[0].text

            # トークン使用量を記録
            usage = TokenUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens
            )
            print(f"  💰 {usage}")

            # 会話履歴に追加
            self.add_turn(user_message, assistant_text, usage)

            return assistant_text

        except Exception as e:
            return f"❌ エラー: {e}"

    def status(self) -> str:
        """現在の状態を返す"""
        return (
            f"会話状態:\n"
            f"  メッセージ数: {len(self.messages)}\n"
            f"  推定トークン数: {self.estimate_messages_tokens():,}\n"
            f"  トークン予算: {self.token_budget:,}\n"
            f"  {self.cost_tracker.summary()}"
        )


def demonstrate_token_counting(client: Anthropic) -> None:
    """
    トークンカウントのデモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- トークンカウントのデモ ---")

    test_texts = [
        "Hello, world!",
        "こんにちは、世界！",
        "Pythonプログラミングは楽しいです。Python programming is fun.",
        "A" * 100,  # 100文字の英語
        "あ" * 100,  # 100文字の日本語
    ]

    print(f"{'テキスト':<40} {'概算':<10} {'説明'}")
    print("-" * 70)
    for text in test_texts:
        display = text[:35] + "..." if len(text) > 35 else text
        estimated = estimate_token_count(text)
        print(f"{display:<40} {estimated:<10} ({len(text)}文字)")

    # APIを使った正確なカウント
    print("\n正確なカウント（API使用）:")
    messages = [{"role": "user", "content": "Pythonの特徴を教えてください。"}]
    exact_count = count_tokens_exact(client, messages)
    estimated_count = estimate_token_count("Pythonの特徴を教えてください。")
    print(f"  テキスト: 'Pythonの特徴を教えてください。'")
    print(f"  概算: {estimated_count} トークン")
    print(f"  正確: {exact_count} トークン")


def demonstrate_cost_tracking(client: Anthropic) -> None:
    """
    コスト追跡のデモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- コスト追跡のデモ ---")

    tracker = CostTracker(budget_usd=0.01)  # 予算: $0.01

    questions = [
        "Pythonとは何ですか？一言で。",
        "機械学習とは何ですか？一言で。",
        "APIとは何ですか？一言で。",
    ]

    for question in questions:
        print(f"\n質問: {question}")

        if not tracker.is_within_budget():
            print("  ❌ 予算超過のためスキップ")
            continue

        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=50,
            messages=[{"role": "user", "content": question}]
        )

        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens
        )
        tracker.record(usage)

        print(f"  応答: {response.content[0].text}")
        print(f"  使用量: {usage}")
        print(f"  予算使用率: {tracker.budget_used_percent:.2f}%")

    print(f"\n{tracker.summary()}")


def demonstrate_conversation_management(client: Anthropic) -> None:
    """
    会話履歴のトークン管理デモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 会話履歴のトークン管理デモ ---")

    # 小さなトークン予算で会話管理をデモ
    manager = ConversationManager(
        token_budget=500,  # 意図的に小さく設定してトリミングを示す
        system_prompt="あなたは簡潔に回答するアシスタントです。"
    )

    conversation = [
        "Pythonの主な特徴は？",
        "その中で最も重要なのは？",
        "型ヒントとはどういう意味ですか？",
    ]

    for user_msg in conversation:
        print(f"\nユーザー: {user_msg}")
        response = manager.chat(client, user_msg)
        print(f"Claude: {response[:100]}{'...' if len(response) > 100 else ''}")
        print(f"  履歴サイズ: {len(manager.messages)} メッセージ, "
              f"推定トークン: {manager.estimate_messages_tokens()}")

    print(f"\n{manager.status()}")


def token_management_best_practices() -> None:
    """
    トークン管理のベストプラクティスを表示する
    """
    print("\n--- トークン管理のベストプラクティス ---")

    best_practices = """
【✅ トークン管理のポイント】

1. max_tokens を適切に設定する
   - 必要以上に大きな値を設定しない（コスト最適化）
   - タスクの性質に合わせて動的に調整する
     例: 要約タスク → 小さめ / 詳細説明 → 大きめ
   - max_tokens=1 でもAPIリクエストは課金される（入力分）

2. システムプロンプトのトークンを意識する
   - 毎回のリクエストにシステムプロンプトが含まれる
   - 長いシステムプロンプトは全リクエストのコストに影響
   - 必要最小限の指示にする

3. 会話履歴のトークン管理
   - 長い会話では履歴が増えてコストが増大する
   - 古い会話を要約・削除してトークン数を抑制する
   - 重要な情報のみを残す戦略が効果的

4. 入力トークンを削減する戦略
   - 冗長な説明を削除する
   - 箇条書きや構造化されたプロンプトを使う
   - 例示は最小限にする（Few-shot は慎重に）
   - コンテキストの再利用（Prompt Caching）を活用する

5. 出力トークンを制限する
   - 「50文字以内で回答してください」等の指示を使う
   - max_tokens で上限を設定する
   - JSON形式等の構造化出力で余分な説明を省く

6. コスト見積もりと予算管理
   - 開発中は小さな予算でテストする
   - 本番環境は月次の上限を設定する
   - 使用量を定期的にモニタリングする

【⚠️ よくある間違い】

1. max_tokens=4096 をデフォルトに → 不要に高いコストが発生
2. 会話履歴を無制限に保持 → トークン数と課金が増大
3. 毎回長いシステムプロンプトを繰り返す → プロンプトキャッシングを検討
4. テスト中に大量のAPIコール → モックやキャッシュを活用する

【💡 CCA試験のポイント】
- トークンは入力と出力でそれぞれ課金される（出力の方が高い）
- コンテキストウィンドウは入力+出力の合計
- max_tokens は「最大」出力トークン数（保証値ではない）
- Prompt Caching でキャッシュされたトークンはコストが下がる（Claudeの機能）
- usage.input_tokens と usage.output_tokens でAPIから実際の使用量を取得できる
"""
    print(best_practices)


if __name__ == "__main__":
    print("=" * 60)
    print("トークン管理とコスト最適化")
    print("=" * 60)

    # ベストプラクティスの表示（APIなし）
    token_management_best_practices()

    # APIを使ったデモ
    print("\n--- API接続テスト ---")
    client = get_client()

    # トークンカウントのデモ
    demonstrate_token_counting(client)

    # コスト追跡のデモ
    demonstrate_cost_tracking(client)

    # 会話履歴管理のデモ
    demonstrate_conversation_management(client)

    print("\n✅ 完了！次はexercises/README.mdを読んで練習問題に挑戦してください。")

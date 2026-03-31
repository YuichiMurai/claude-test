"""
exercise_02.py - 練習問題2: 会話履歴を使った対話システム

【課題】
会話履歴を管理するシンプルなチャットボットクラスを実装してください。
3ターン以上の会話でコンテキストが維持されることを確認します。

【学習目標】
- 会話履歴の管理方法を習得する
- マルチターン会話の実装方法を理解する
- クラスを使った状態管理を学ぶ

【参考ファイル】
- 01_basics/04_message_history.py: 会話履歴の管理
"""

import os
from typing import List
from anthropic import Anthropic
from dotenv import load_dotenv


MessageHistory = List[dict]


class SimpleBot:
    """
    会話履歴を管理するシンプルなチャットボット。

    【TODO】
    以下のメソッドを実装してください：
    - __init__: クライアントとシステムプロンプトを受け取り初期化する
    - chat: ユーザー入力を受け取り、Claudeの回答を返す
    - get_history: 現在の会話履歴を返す
    - reset: 会話履歴をリセットする
    """

    def __init__(self, client: Anthropic, system_prompt: str = "") -> None:
        """
        ボットを初期化する。

        【TODO】
        以下を実装してください：
        1. client を self.client に保存する
        2. system_prompt を self.system_prompt に保存する
        3. 空の会話履歴 self.history を [] で初期化する

        Args:
            client: Anthropicクライアント
            system_prompt: ボットの振る舞いを定義するシステムプロンプト
        """
        # --- ここから実装 ---
        self.client = client
        self.system_prompt = system_prompt
        self.history: MessageHistory = []
        # --- ここまで実装 ---

    def chat(self, user_input: str) -> str:
        """
        1ターンの会話を進める。

        【TODO】
        以下を実装してください：
        1. ユーザーメッセージを self.history に追加する
           形式: {"role": "user", "content": user_input}
        2. APIを呼び出す（system_promptが空でない場合は system パラメータを設定）
        3. Claudeの回答を self.history にアシスタントメッセージとして追加する
           形式: {"role": "assistant", "content": 回答テキスト}
        4. 回答テキストを返す

        Args:
            user_input: ユーザーからの入力

        Returns:
            str: Claudeからの回答テキスト
        """
        # --- ここから実装 ---
        # ユーザーメッセージを履歴に追加
        self.history.append({"role": "user", "content": user_input})

        # APIリクエストのパラメータを構築
        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": self.history,
        }
        if self.system_prompt:
            kwargs["system"] = self.system_prompt

        # APIを呼び出す
        response = self.client.messages.create(**kwargs)
        assistant_text = response.content[0].text

        # アシスタントの回答を履歴に追加
        self.history.append({"role": "assistant", "content": assistant_text})
        return assistant_text
        # --- ここまで実装 ---

    def get_history(self) -> MessageHistory:
        """
        現在の会話履歴を返す。

        Returns:
            MessageHistory: 会話履歴のリスト
        """
        # --- ここから実装 ---
        return self.history
        # --- ここまで実装 ---

    def reset(self) -> None:
        """会話履歴をリセットしてゼロから始める。"""
        # --- ここから実装 ---
        self.history = []
        # --- ここまで実装 ---


def main() -> None:
    """メイン処理：3ターン以上の会話でコンテキスト維持を確認。"""
    load_dotenv()
    client = Anthropic()

    system_prompt = (
        "あなたは親切な料理アドバイザーです。"
        "ユーザーの好みや条件を覚えながら、具体的なアドバイスをしてください。"
    )

    bot = SimpleBot(client, system_prompt)

    print("=== 練習問題2: 会話履歴を使った対話システム ===\n")

    # ターン1: 最初の質問
    user1 = "今日のランチに何を食べればいいですか？"
    print(f"ユーザー: {user1}")
    response1 = bot.chat(user1)
    print(f"ボット: {response1}\n")

    # ターン2: 前の会話を踏まえた追加条件
    user2 = "カロリーが少ないものがいいです"
    print(f"ユーザー: {user2}")
    response2 = bot.chat(user2)
    print(f"ボット: {response2}\n")

    # ターン3: さらに絞り込む
    user3 = "その中で一番おすすめは何ですか？理由も教えてください。"
    print(f"ユーザー: {user3}")
    response3 = bot.chat(user3)
    print(f"ボット: {response3}\n")

    # ターン4: 別の質問（コンテキストを引き継ぐ）
    user4 = "それは自宅で簡単に作れますか？"
    print(f"ユーザー: {user4}")
    response4 = bot.chat(user4)
    print(f"ボット: {response4}\n")

    # 会話履歴の確認
    history = bot.get_history()
    print(f"会話ターン数: {len(history) // 2}")
    print(f"総メッセージ数: {len(history)}")

    print("\n=== リセット後の新しい会話 ===\n")

    # リセットして新しい話題
    bot.reset()
    print(f"リセット後の履歴数: {len(bot.get_history())}")

    user_new = "今日の夕食に何を作ればいいですか？"
    print(f"ユーザー: {user_new}")
    response_new = bot.chat(user_new)
    print(f"ボット: {response_new}\n")


if __name__ == "__main__":
    main()

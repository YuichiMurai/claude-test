"""
04_message_history.py - 会話履歴の管理

このファイルの目的:
- マルチターン会話の実装方法を学ぶ
- 会話履歴の管理方法を理解する
- コンテキストウィンドウの概念を学ぶ

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このコードを実行:
   !python 01_basics/04_message_history.py
   または、コードをColabのセルに貼り付けて実行

【会話履歴とは？】
Claude APIはステートレス（状態を保持しない）なので、
毎回のリクエストに会話の全履歴を含める必要があります。
これにより、前の会話の文脈を踏まえた返答が可能になります。
"""

import os
from typing import List, Dict
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


def basic_conversation(client: Anthropic) -> None:
    """
    基本的な会話履歴の例

    会話履歴はmessagesリストに追加していくことで管理します

    Args:
        client: Anthropicクライアント
    """
    print("\n--- 基本的な会話履歴 ---")

    # 会話履歴を格納するリスト
    # 各要素は {"role": "user" または "assistant", "content": "テキスト"} の辞書
    messages: List[Dict[str, str]] = []

    # ターン1: 最初の質問
    user_message_1 = "Pythonのリストについて教えてください。"
    messages.append({"role": "user", "content": user_message_1})

    print(f"ユーザー: {user_message_1}")

    response_1 = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=messages  # 現在の会話履歴を渡す
    )

    # アシスタントの返答を履歴に追加
    assistant_message_1 = response_1.content[0].text
    messages.append({"role": "assistant", "content": assistant_message_1})

    print(f"Claude: {assistant_message_1[:100]}...")

    # ターン2: 前の会話を踏まえた追加質問
    user_message_2 = "具体的なコード例を見せてください。"
    messages.append({"role": "user", "content": user_message_2})

    print(f"\nユーザー: {user_message_2}")

    # 会話履歴全体（ターン1 + ターン2）を渡す
    response_2 = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        messages=messages  # 2ターン分の履歴を渡す
    )

    assistant_message_2 = response_2.content[0].text
    messages.append({"role": "assistant", "content": assistant_message_2})

    print(f"Claude: {assistant_message_2[:200]}...")

    print(f"\n[会話履歴のターン数: {len(messages) // 2}]")


class ConversationManager:
    """
    会話履歴を管理するクラス

    このクラスを使うことで、会話履歴の管理が簡単になります
    """

    def __init__(self, client: Anthropic, system: str = "", max_history: int = 20):
        """
        初期化

        Args:
            client: Anthropicクライアント
            system: systemプロンプト（オプション）
            max_history: 保持する最大メッセージ数（メモリ管理のため）
        """
        self.client = client
        self.system = system
        self.max_history = max_history
        self.messages: List[Dict[str, str]] = []

    def chat(self, user_message: str, max_tokens: int = 1024) -> str:
        """
        ユーザーメッセージを送信してレスポンスを返す

        Args:
            user_message: ユーザーのメッセージ
            max_tokens: 最大トークン数

        Returns:
            str: Claudeの返答
        """
        # ユーザーメッセージを履歴に追加
        self.messages.append({"role": "user", "content": user_message})

        # APIリクエストを送信
        kwargs = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "messages": self.messages,
        }

        # systemプロンプトが設定されている場合は追加
        if self.system:
            kwargs["system"] = self.system

        response = self.client.messages.create(**kwargs)

        # アシスタントの返答を履歴に追加
        assistant_message = response.content[0].text
        self.messages.append({"role": "assistant", "content": assistant_message})

        # 履歴が上限を超えた場合、古いものを削除
        if len(self.messages) > self.max_history * 2:
            self.messages = self.messages[2:]  # 最古のターンを削除

        return assistant_message

    def clear_history(self) -> None:
        """会話履歴をリセットする"""
        self.messages = []
        print("✅ 会話履歴をリセットしました")

    def get_history_count(self) -> int:
        """会話のターン数を返す"""
        return len(self.messages) // 2

    def display_history(self) -> None:
        """会話履歴を表示する"""
        print("\n[会話履歴]")
        for msg in self.messages:
            role = "👤 ユーザー" if msg["role"] == "user" else "🤖 Claude"
            print(f"{role}: {msg['content'][:100]}...")
            print()


def demo_conversation_manager(client: Anthropic) -> None:
    """
    ConversationManagerクラスを使ったデモ

    Args:
        client: Anthropicクライアント
    """
    print("\n--- ConversationManagerのデモ ---")

    # Python学習アシスタントとして設定
    assistant = ConversationManager(
        client=client,
        system="あなたはPython学習の専門家です。"
               "初心者にも分かりやすく、ステップバイステップで説明してください。"
               "コード例は必ず含めてください。",
        max_history=10
    )

    # 会話1
    response = assistant.chat("関数とは何ですか？")
    print(f"ユーザー: 関数とは何ですか？")
    print(f"Claude: {response[:150]}...\n")

    # 会話2: 前の会話の文脈を活用
    response = assistant.chat("引数と戻り値について詳しく教えてください。")
    print(f"ユーザー: 引数と戻り値について詳しく教えてください。")
    print(f"Claude: {response[:150]}...\n")

    # 会話3: さらに深掘り
    response = assistant.chat("デフォルト引数の使い方を教えてください。")
    print(f"ユーザー: デフォルト引数の使い方を教えてください。")
    print(f"Claude: {response[:150]}...\n")

    print(f"合計ターン数: {assistant.get_history_count()}")


def demo_context_importance(client: Anthropic) -> None:
    """
    コンテキスト（会話履歴）の重要性を示すデモ

    同じ質問でも、会話履歴があるとないとでは返答が変わります

    Args:
        client: Anthropicクライアント
    """
    print("\n--- コンテキストの重要性デモ ---")

    # 履歴なしのリクエスト
    print("【履歴なし】")
    response_no_history = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "それをPythonで実装するとどうなりますか？"}
        ]
    )
    print(f"Claude: {response_no_history.content[0].text}")

    # 履歴ありのリクエスト
    print("\n【履歴あり（前の会話でバブルソートを説明）】")
    response_with_history = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=256,
        messages=[
            {"role": "user", "content": "バブルソートについて説明してください。"},
            {"role": "assistant", "content": "バブルソートは隣接する要素を比較して交換することでデータを並び替えるアルゴリズムです。"},
            {"role": "user", "content": "それをPythonで実装するとどうなりますか？"}
        ]
    )
    print(f"Claude: {response_with_history.content[0].text[:200]}...")


if __name__ == "__main__":
    print("=" * 50)
    print("会話履歴の管理")
    print("=" * 50)

    # クライアントを初期化
    client = get_client()

    # 各例を実行
    basic_conversation(client)
    demo_conversation_manager(client)
    demo_context_importance(client)

    print("\n✅ 完了！次はexercises/に進んで練習問題に取り組んでください。")

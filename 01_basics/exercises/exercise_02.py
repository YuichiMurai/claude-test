"""
exercise_02.py - 練習問題2: 会話履歴を使った対話システム

難易度: ⭐⭐ 初級
目的: マルチターン会話を実装する

【課題】
ユーザーとClaudeが自然な会話を続けられるチャットシステムを作成します。
前の会話内容を記憶して、文脈を踏まえた返答ができるようにします。

【期待される出力】
==============================
チャットシステム（会話履歴付き）
==============================
システム: Pythonプログラミングの先生として振る舞います

ターン1:
  ユーザー: 変数とは何ですか？
  Claude: 変数とは...（文脈を踏まえた回答）

ターン2:
  ユーザー: 型はどう確認しますか？
  Claude: 変数の型を確認するには...

ターン3:
  ユーザー: まとめてください
  Claude: これまでの内容をまとめると...

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
from typing import List, Dict
from anthropic import Anthropic


def get_client() -> Anthropic:
    """APIクライアントを取得する（Colab・ローカル両対応）"""
    try:
        from google.colab import userdata
        os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()

    return Anthropic()


def chat_with_history(
    client: Anthropic,
    messages: List[Dict[str, str]],
    system: str,
    user_message: str
) -> str:
    """
    会話履歴を使ってメッセージを送信する

    Args:
        client: Anthropicクライアント
        messages: これまでの会話履歴
        system: systemプロンプト
        user_message: 新しいユーザーメッセージ

    Returns:
        str: Claudeの回答

    TODO: この関数を実装してください
    ヒント:
    1. user_message を messages に追加する
       messages.append({"role": "user", "content": user_message})

    2. client.messages.create() でAPIを呼び出す
       - model: "claude-3-5-sonnet-20241022"
       - max_tokens: 512
       - system: system
       - messages: messages

    3. 回答テキストを messages に追加する
       messages.append({"role": "assistant", "content": response_text})

    4. 回答テキストを返す
    """
    # TODO: ここにコードを書いてください
    pass


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("チャットシステム（会話履歴付き）")
    print("=" * 30)

    # クライアントを初期化
    client = get_client()

    # systemプロンプトの設定
    system = "あなたはPythonプログラミングの先生です。初心者にも分かりやすく説明してください。"
    print(f"システム: {system}\n")

    # 会話履歴を格納するリスト（空から始まる）
    messages: List[Dict[str, str]] = []

    # 会話のシナリオ
    conversation = [
        "変数とは何ですか？",
        "型はどう確認しますか？",
        "これまでの内容をまとめてください",
    ]

    # TODO: 各ターンの会話を処理してください
    # ヒント: enumerate() を使ってターン番号を取得しながら繰り返す
    for i, user_message in enumerate(conversation, 1):
        print(f"ターン{i}:")
        print(f"  ユーザー: {user_message}")

        # TODO: chat_with_history() を呼び出して回答を取得してください
        # response = chat_with_history(client, messages, system, user_message)
        # print(f"  Claude: {response[:100]}...")
        pass

    print(f"\n合計ターン数: {len(messages) // 2}")
    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

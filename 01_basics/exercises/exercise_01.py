"""
exercise_01.py - 練習問題1: 簡単な質問応答システム

難易度: ⭐ 初級
目的: 基本的なAPI呼び出しをマスターする

【課題】
指定されたトピックについて質問を受け付け、Claudeが回答するシステムを作成します。

【期待される出力】
==============================
質問応答システム
==============================
質問: Pythonの特徴を教えてください
回答: Pythonは...（Claudeの回答）

質問: なぜ人気があるのですか？
回答: ...（Claudeの回答）

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


def ask_question(client: Anthropic, question: str) -> str:
    """
    質問を送信して回答を返す

    Args:
        client: Anthropicクライアント
        question: 質問テキスト

    Returns:
        str: Claudeの回答

    TODO: この関数を実装してください
    ヒント:
    - client.messages.create() を使う
    - model: "claude-3-5-sonnet-20241022"
    - max_tokens: 512
    - messages: [{"role": "user", "content": question}]
    - message.content[0].text で回答テキストを取得
    """
    # TODO: ここにコードを書いてください
    pass


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("質問応答システム")
    print("=" * 30)

    # クライアントを初期化
    client = get_client()

    # 質問リスト
    questions = [
        "Pythonの特徴を教えてください",
        "なぜ人気があるのですか？",
        "初心者が最初に学ぶべきことは何ですか？",
    ]

    # TODO: 各質問を処理して回答を表示してください
    # ヒント: for ループで questions を繰り返し処理する
    for question in questions:
        print(f"\n質問: {question}")
        # TODO: ask_question() を呼び出して回答を取得し表示してください
        pass

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

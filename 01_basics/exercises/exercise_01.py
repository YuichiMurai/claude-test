"""
exercise_01.py - 練習問題1: 簡単な質問応答システム

【課題】
ユーザーからの質問を受け取り、Claudeで回答を生成するQ&Aシステムを実装してください。

【学習目標】
- Claude APIの基本的な呼び出し方を習得する
- システムプロンプトの設定方法を理解する
- レスポンスの解析方法を習得する

【参考ファイル】
- 01_basics/01_api_setup.py    : クライアントの初期化方法
- 01_basics/02_first_request.py: リクエストの送信とレスポンス解析
"""

import os
from anthropic import Anthropic
from dotenv import load_dotenv


def ask_question(client: Anthropic, question: str) -> str:
    """
    質問を送信してClaudeから回答を取得する。

    【TODO】
    以下を実装してください：
    1. client.messages.create() を使ってAPIを呼び出す
    2. モデルは "claude-3-5-sonnet-20241022" を使用する
    3. max_tokens は 512 に設定する
    4. システムプロンプトで「簡潔に日本語で回答してください」と指示する
    5. レスポンスのテキストを返す

    Args:
        client: Anthropicクライアント
        question: ユーザーからの質問

    Returns:
        str: Claudeからの回答テキスト
    """
    # --- ここから実装 ---
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=512,
        system="あなたは親切な日本語アシスタントです。簡潔に日本語で回答してください。",
        messages=[
            {"role": "user", "content": question}
        ],
    )
    return response.content[0].text
    # --- ここまで実装 ---


def ask_with_context(client: Anthropic, question: str, context: str) -> str:
    """
    コンテキスト（背景情報）を付与して質問する。

    【TODO】
    以下を実装してください：
    1. context と question を組み合わせたメッセージを作成する
       例: f"【背景情報】\n{context}\n\n【質問】\n{question}"
    2. ask_question() を呼び出して回答を取得する
    3. 回答を返す

    Args:
        client: Anthropicクライアント
        question: ユーザーからの質問
        context: 質問に関連する背景情報

    Returns:
        str: Claudeからの回答テキスト
    """
    # --- ここから実装 ---
    combined_message = f"【背景情報】\n{context}\n\n【質問】\n{question}"
    return ask_question(client, combined_message)
    # --- ここまで実装 ---


def main() -> None:
    """メイン処理：質問応答システムの動作確認。"""
    load_dotenv()
    client = Anthropic()

    print("=== 練習問題1: 質問応答システム ===\n")

    # 基本的な質問
    questions = [
        "Pythonのリスト内包表記とは何ですか？",
        "APIとは何か、一文で説明してください。",
        "機械学習と深層学習の違いは何ですか？",
    ]

    for question in questions:
        print(f"質問: {question}")
        answer = ask_question(client, question)
        print(f"回答: {answer}\n")

    print("=== コンテキスト付き質問 ===\n")

    # コンテキストを付与した質問
    context = "Pythonのリスト内包表記は [式 for 変数 in イテラブル] という形式で書く"
    question = "この方法を使って1から10の偶数だけのリストを作るにはどう書きますか？"

    print(f"コンテキスト: {context}")
    print(f"質問: {question}")
    answer = ask_with_context(client, question, context)
    print(f"回答: {answer}\n")


if __name__ == "__main__":
    main()

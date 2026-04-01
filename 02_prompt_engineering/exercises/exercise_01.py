"""
exercise_01.py - 練習問題1: カスタムアシスタントの作成

難易度: ⭐⭐⭐ 中級
目的: システムプロンプトを設計して特定用途のアシスタントを作成する

【課題】
「料理レシピアドバイザー」のシステムプロンプトを設計し、
複数のリクエストに対して一貫した形式で回答するアシスタントを実装します。

【期待される出力】
==============================
料理レシピアドバイザー
==============================

質問: 簡単なパスタレシピを教えてください

回答:
【料理名】ガーリックパスタ
【調理時間】20分
【材料】（2人前）
- パスタ: 200g
...
【手順】
1. ...
【初心者へのアドバイス】...
【アレルギー情報】小麦

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


def create_recipe_system_prompt() -> str:
    """
    料理レシピアドバイザー用のシステムプロンプトを作成する

    Returns:
        str: システムプロンプト

    TODO: 以下の要件を満たすシステムプロンプトを作成してください
    要件:
    - プロの料理人として振る舞う
    - 常に以下のフォーマットで回答する:
        【料理名】
        【調理時間】
        【材料】
        【手順】
        【初心者へのアドバイス】
        【アレルギー情報】
    - 初心者向けの分かりやすい説明を含める
    - アレルギー情報を必ず明記する

    ヒント:
    - システムプロンプトで出力形式を具体的に指定する
    - ペルソナの口調や特徴を定義する
    - 「必ず」「常に」などの強い指示語を使う
    """
    # TODO: ここにシステムプロンプトを書いてください
    system_prompt = ""

    return system_prompt


def ask_recipe(client: Anthropic, system_prompt: str, question: str) -> str:
    """
    レシピアドバイザーに質問する

    Args:
        client: Anthropicクライアント
        system_prompt: 作成したシステムプロンプト
        question: レシピのリクエスト

    Returns:
        str: アドバイザーの回答

    TODO: この関数を実装してください
    ヒント:
    - client.messages.create() を使う
    - system パラメータに system_prompt を渡す
    - model: "claude-3-5-sonnet-20241022"
    - max_tokens: 1024
    """
    # TODO: ここにコードを書いてください
    pass


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("料理レシピアドバイザー")
    print("=" * 30)

    client = get_client()

    # システムプロンプトを作成
    # TODO: create_recipe_system_prompt() が完成したらコメントを外す
    system_prompt = create_recipe_system_prompt()

    if not system_prompt:
        print("❌ システムプロンプトが設定されていません。")
        print("   create_recipe_system_prompt() を実装してください。")
        return

    # テスト用の質問リスト
    questions = [
        "簡単なパスタレシピを教えてください",
        "卵を使わないデザートを作りたいです",
        "15分で作れる健康的な朝食を教えてください",
    ]

    for question in questions:
        print(f"\n質問: {question}")
        print("-" * 40)

        # TODO: ask_recipe() を呼び出して回答を取得し表示してください
        answer = ask_recipe(client, system_prompt, question)
        if answer:
            print(f"回答:\n{answer}")

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

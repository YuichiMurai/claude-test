"""
exercise_03.py - 練習問題3: ストリーミングを使ったリアルタイム翻訳

難易度: ⭐⭐ 初級
目的: ストリーミングAPIを活用する

【課題】
入力した日本語テキストを英語にリアルタイムで翻訳するシステムを作成します。
翻訳結果が生成されるにつれてリアルタイムで表示されます。

【期待される出力】
==============================
リアルタイム翻訳システム
==============================

翻訳するテキスト:
"人工知能は、人間の知的な振る舞いをコンピュータで模倣する技術です。"

翻訳中...
Artificial intelligence is a technology...（リアルタイム表示）

翻訳完了！
使用トークン: 入力 XX, 出力 XX

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


def translate_streaming(client: Anthropic, text: str) -> None:
    """
    テキストをリアルタイムでストリーミング翻訳する

    Args:
        client: Anthropicクライアント
        text: 翻訳する日本語テキスト

    TODO: この関数を実装してください
    ヒント:
    1. client.messages.stream() を使う（with文で囲む）
       - model: "claude-3-5-sonnet-20241022"
       - max_tokens: 1024
       - system: 翻訳専門家としてのsystemプロンプト
       - messages: 翻訳リクエストを含むメッセージ

    2. stream.text_stream でテキストチャンクを受け取る
       for text_chunk in stream.text_stream:
           print(text_chunk, end="", flush=True)

    3. ストリーミング完了後に最終メッセージを取得してトークン数を表示
       final_message = stream.get_final_message()
       print(f"入力: {final_message.usage.input_tokens}")
       print(f"出力: {final_message.usage.output_tokens}")
    """
    # TODO: ここにコードを書いてください
    pass


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("リアルタイム翻訳システム")
    print("=" * 30)

    # クライアントを初期化
    client = get_client()

    # 翻訳するテキストのリスト
    texts_to_translate = [
        "人工知能は、人間の知的な振る舞いをコンピュータで模倣する技術です。",
        "機械学習とは、データからパターンを学習してタスクを実行する手法です。",
        "Claudeは、Anthropicが開発した高性能なAIアシスタントです。",
    ]

    # TODO: 各テキストを翻訳してください
    for text in texts_to_translate:
        print(f"\n翻訳するテキスト:\n\"{text}\"")
        print("\n翻訳中...")

        # TODO: translate_streaming() を呼び出してください
        # translate_streaming(client, text)
        pass

        print("\n" + "-" * 40)

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

"""
exercise_02.py - 練習問題2: Few-shot でのテキスト分類

難易度: ⭐⭐⭐ 中級
目的: Few-shot learning を使って独自の分類システムを構築する

【課題】
ニュース記事を5つのカテゴリに分類するシステムを
Few-shot learning で実装します。

カテゴリ:
- tech（テクノロジー）
- politics（政治）
- sports（スポーツ）
- business（ビジネス・経済）
- entertainment（エンタメ）

【期待される出力】
==============================
ニュース分類システム（Few-shot）
==============================

記事: 新型AIチップが発表され、処理速度が従来の3倍に
分類: tech

記事: 日本代表がワールドカップ予選を突破
分類: sports

...

正解率: X/10

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


def build_few_shot_messages(article: str) -> list[dict[str, str]]:
    """
    ニュース分類のための Few-shot メッセージリストを構築する

    Args:
        article: 分類するニュース記事

    Returns:
        list[dict[str, str]]: Few-shot の例を含むメッセージリスト

    TODO: 各カテゴリに2つ以上の例を追加してください
    形式:
        [
            {"role": "user", "content": "記事: ...\nカテゴリ:"},
            {"role": "assistant", "content": "tech"},
            ...
            {"role": "user", "content": f"記事: {article}\nカテゴリ:"},
        ]

    ヒント:
    - 各カテゴリ（tech/politics/sports/business/entertainment）の
      典型的な例を選ぶ
    - 境界が曖昧なケースも含めると精度が上がる
    - 最後の要素が実際の分類対象記事になる
    """
    messages = [
        # TODO: tech の例を2つ追加してください
        # 各例は user と assistant のペアで記述します。例:
        # {"role": "user", "content": "記事: 新型スマートフォンが発売、カメラ性能が大幅向上\nカテゴリ:"},
        # {"role": "assistant", "content": "tech"},

        # TODO: politics の例を2つ追加してください

        # TODO: sports の例を2つ追加してください

        # TODO: business の例を2つ追加してください

        # TODO: entertainment の例を2つ追加してください

        # 分類対象の記事（最後に配置する）
        {
            "role": "user",
            "content": f"記事: {article}\nカテゴリ:"
        }
    ]

    return messages


def classify_article(client: Anthropic, article: str) -> str:
    """
    ニュース記事をカテゴリに分類する

    Args:
        client: Anthropicクライアント
        article: 分類するニュース記事

    Returns:
        str: カテゴリラベル（tech/politics/sports/business/entertainment）

    TODO: この関数を実装してください
    ヒント:
    - build_few_shot_messages() でメッセージリストを構築する
    - client.messages.create() でAPIを呼び出す
    - max_tokens は小さく設定する（カテゴリラベルだけで十分）
    - 結果の前後の空白を strip() で除去する
    """
    # TODO: ここにコードを書いてください
    pass


def evaluate_accuracy(
    client: Anthropic,
    test_data: list[dict[str, str]]
) -> None:
    """
    テストデータを使って分類精度を評価する

    Args:
        client: Anthropicクライアント
        test_data: テストデータ（article と expected_category を持つ辞書のリスト）

    TODO: この関数を完成させてください
    ヒント:
    - classify_article() を呼び出して各記事を分類する
    - 予測カテゴリと期待カテゴリを比較して正解数をカウントする
    - 正解率を計算して表示する
    """
    correct = 0
    total = len(test_data)

    for item in test_data:
        article = item["article"]
        expected = item["expected_category"]

        # TODO: classify_article() を呼び出して予測カテゴリを取得する
        predicted = None  # TODO: ここを実装してください

        is_correct = predicted == expected
        if is_correct:
            correct += 1

        print(f"記事: {article[:50]}...")
        print(f"  期待: {expected} | 予測: {predicted} | {'✅' if is_correct else '❌'}")

    # TODO: 正解率を表示してください
    # 例: print(f"\n正解率: {correct}/{total} ({accuracy:.0%})")


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("ニュース分類システム（Few-shot）")
    print("=" * 30)

    client = get_client()

    # テストデータ（記事と期待するカテゴリ）
    test_data = [
        {"article": "新型AIチップが発表され、処理速度が従来の3倍になると発表",
         "expected_category": "tech"},
        {"article": "衆議院選挙の投票率が過去最低を記録",
         "expected_category": "politics"},
        {"article": "サッカー日本代表がワールドカップ予選を突破",
         "expected_category": "sports"},
        {"article": "大手銀行が金利を0.1%引き上げると発表",
         "expected_category": "business"},
        {"article": "人気アニメ映画が興行収入100億円を突破",
         "expected_category": "entertainment"},
        {"article": "量子コンピュータの商用化が2025年に実現か",
         "expected_category": "tech"},
        {"article": "与野党が税制改革案で合意に達する",
         "expected_category": "politics"},
        {"article": "プロ野球シーズン開幕、各球団の展望",
         "expected_category": "sports"},
        {"article": "スタートアップ企業が100億円の資金調達に成功",
         "expected_category": "business"},
        {"article": "著名歌手の引退コンサートにファン5万人が集結",
         "expected_category": "entertainment"},
    ]

    print("\n【分類結果】")
    evaluate_accuracy(client, test_data)

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

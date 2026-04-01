"""
exercise_03.py - 練習問題3: 複雑な推論タスク

難易度: ⭐⭐⭐ 中級
目的: Chain of Thought と XML タグを組み合わせて複雑な推論を実装する

【課題】
プロジェクトの優先度を多角的に評価して順位付けする
「プロジェクト優先度評価システム」を実装します。

評価基準:
- ビジネスインパクト（1〜10点）
- 実現可能性（1〜10点）
- 緊急度（1〜10点）
- 総合スコア = 各評価点の加重平均

【期待される出力】
==============================
プロジェクト優先度評価システム
==============================

評価プロセス:

【プロジェクトA: 顧客ポータルのリニューアル】
思考ステップ1: ビジネスインパクトを評価...（スコア: X/10）
思考ステップ2: 実現可能性を評価...（スコア: X/10）
思考ステップ3: 緊急度を評価...（スコア: X/10）
総合スコア: XX/30

...

【優先度ランキング】
1位: プロジェクトA（スコア: XX）
2位: プロジェクトB（スコア: XX）
3位: プロジェクトC（スコア: XX）

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


def build_evaluation_prompt(projects: list[dict[str, str]]) -> str:
    """
    プロジェクト評価用のプロンプトを XML タグで構築する

    Args:
        projects: プロジェクト情報のリスト
                  各要素は name, description, deadline, resources を持つ辞書

    Returns:
        str: XML タグを使った構造化プロンプト

    TODO: この関数を実装してください
    要件:
    - 各プロジェクトを <project> タグで囲む
    - プロジェクト名、説明、締め切り、リソース状況を含める
    - CoT の指示を含める（ステップバイステップで評価するよう指示）
    - 最終的なランキングを出力するよう指示する

    ヒント:
    - <projects> タグで全プロジェクトをまとめる
    - <evaluation_criteria> タグで評価基準を定義する
    - <output_format> タグで出力形式を指定する
    - 「各プロジェクトについて、ステップバイステップで考えて」と指示する
    """
    # TODO: XML タグを使ってプロジェクト情報を構造化してください

    # プロジェクト情報を XML タグで構築する
    projects_xml = ""
    for i, project in enumerate(projects, 1):
        # TODO: 各プロジェクトを <project> タグで囲んでください
        # 例:
        # projects_xml += f"""<project id="{i}">
        #   <name>{project['name']}</name>
        #   <description>{project['description']}</description>
        #   <deadline>{project['deadline']}</deadline>
        #   <resources>{project['resources']}</resources>
        # </project>
        # """
        projects_xml += ""  # TODO: この行を上記の実装に置き換えてください

    # TODO: 完全なプロンプトを組み立ててください
    # 評価基準・出力形式・CoT の指示を含めてください
    prompt = ""

    return prompt


def create_evaluation_system_prompt() -> str:
    """
    プロジェクト評価アシスタント用のシステムプロンプトを作成する

    Returns:
        str: システムプロンプト

    TODO: この関数を実装してください
    要件:
    - プロジェクトマネージャーの専門家として振る舞う
    - 各評価基準（ビジネスインパクト・実現可能性・緊急度）を
      1〜10点で採点する
    - 必ず思考プロセスを示しながら評価する
    - 最後に優先度ランキングを提示する

    ヒント:
    - 評価基準の定義を明確にする
    - スコアリングの基準（何点ならどの水準か）を定義する
    """
    # TODO: ここにシステムプロンプトを書いてください
    return ""


def evaluate_projects(
    client: Anthropic,
    projects: list[dict[str, str]]
) -> str:
    """
    プロジェクトを評価してランキングを返す

    Args:
        client: Anthropicクライアント
        projects: 評価するプロジェクトのリスト

    Returns:
        str: 評価結果とランキング

    TODO: この関数を実装してください
    ヒント:
    - create_evaluation_system_prompt() でシステムプロンプトを取得する
    - build_evaluation_prompt() でユーザープロンプトを構築する
    - client.messages.create() でAPIを呼び出す
    - max_tokens は 1500 以上に設定する（詳細な評価が必要なため）
    """
    # TODO: ここにコードを書いてください
    pass


def main() -> None:
    """メイン処理"""
    print("=" * 30)
    print("プロジェクト優先度評価システム")
    print("=" * 30)

    client = get_client()

    # 評価対象のプロジェクト
    projects = [
        {
            "name": "顧客ポータルのリニューアル",
            "description": (
                "既存の顧客ポータルサイトをモダンな UI/UX に刷新する。"
                "顧客満足度の向上と問い合わせ削減を目指す。"
            ),
            "deadline": "3ヶ月後",
            "resources": "フロントエンドエンジニア2名、デザイナー1名が確保済み",
        },
        {
            "name": "社内業務の自動化ツール開発",
            "description": (
                "手動で行っている月次レポート作成を自動化する。"
                "現在は毎月20時間の工数がかかっている。"
            ),
            "deadline": "6ヶ月後",
            "resources": "バックエンドエンジニア1名のみ。外部ライブラリの調査が必要。",
        },
        {
            "name": "セキュリティ脆弱性の修正",
            "description": (
                "先日の外部監査で発見されたSQLインジェクションの脆弱性を修正する。"
                "対応しない場合、個人情報漏洩のリスクがある。"
            ),
            "deadline": "2週間後（監査報告の期限）",
            "resources": "セキュリティエンジニア1名。修正方法は特定済み。",
        },
        {
            "name": "新機能「AI チャットサポート」の開発",
            "description": (
                "AI を活用したチャットサポート機能を追加する。"
                "競合他社がすでに同様の機能をリリース済み。"
            ),
            "deadline": "4ヶ月後",
            "resources": "フルスタックエンジニア2名が必要だが、1名しか確保できていない。",
        },
    ]

    print("\n【評価プロセス】\n")

    # TODO: evaluate_projects() を呼び出して評価結果を表示してください
    result = evaluate_projects(client, projects)

    if result:
        print(result)
    else:
        print("❌ evaluate_projects() を実装してください。")

    print("\n✅ 完了！")


if __name__ == "__main__":
    main()

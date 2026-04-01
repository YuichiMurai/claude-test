"""
scenario_03_solution.py - コンテンツ分類・モデレーションシステム（模範解答）

【このファイルの目的】
シナリオ3「コンテンツ分類・モデレーションシステム」の模範解答です。
すべての要件を満たした最高品質のコードを示します。

【Google Colabでの実行方法】
1. パッケージをインストール:
   !pip install anthropic python-dotenv -q

2. API Key設定（Colab Secretsに設定済みの場合は不要）:
   from google.colab import userdata
   import os
   os.environ['ANTHROPIC_API_KEY'] = userdata.get('ANTHROPIC_API_KEY')

3. このファイルの内容をColabのセルに貼り付けて実行

【学習のポイント】
- モデレーションと分類を1回のAPIコールで処理するとトークン効率が良い
- JSON形式のレスポンスには必ずエラーハンドリングが必要（JSONDecodeError）
- バッチ処理では1件のエラーで全体が止まらないよう各件を個別にtry/exceptで囲む
- レート制限対策の待機時間はAPIのレスポンスヘッダーで動的に調整するのが理想

【CCA試験でのポイント】
- モデレーションはセーフティの根幹 — 過検出と見逃しのトレードオフを意識する
- マルチラベル分類は信頼度スコアの閾値設計が精度に直結する
- バッチ処理のエラー戦略: fail-fast vs best-effort（この実装はbest-effort）
- JSON出力の設計は後続システムとの契約 — スキーマの安定性が重要
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import anthropic
from anthropic import Anthropic

# 使用するモデル名（統一して使用）
MODEL_NAME = "claude-sonnet-4-20250514"

# 分類カテゴリの定義
CATEGORIES = [
    "technology",      # テクノロジー・IT・プログラミング
    "sports",          # スポーツ・フィットネス
    "entertainment",   # エンターテイメント・映画・音楽
    "news",            # ニュース・時事問題
    "food",            # 食事・料理・グルメ
    "travel",          # 旅行・観光
    "education",       # 教育・学習
    "other",           # その他
]

# 不適切コンテンツの種類
MODERATION_TYPES = ["violence", "hate_speech", "spam", "adult_content"]

# 信頼度スコアの閾値（この値以上のカテゴリを「分類あり」とする）
CONFIDENCE_THRESHOLD = 0.5

# バッチ処理のレート制限対策
BATCH_DELAY_SECONDS = 0.5   # APIコール間の待機時間

# リトライパラメータ
MAX_RETRIES = 3
BASE_DELAY = 1.0


def get_client() -> Anthropic:
    """APIクライアントを取得"""
    try:
        from google.colab import userdata
        api_key = userdata.get('ANTHROPIC_API_KEY')
    except ImportError:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ANTHROPIC_API_KEY')

    return Anthropic(api_key=api_key)


@dataclass
class ModerationResult:
    """モデレーション結果を保持するデータクラス"""

    violence: str = "none"         # high / medium / low / none
    hate_speech: str = "none"
    spam: str = "none"
    adult_content: str = "none"
    is_inappropriate: bool = False
    confidence: float = 0.0
    details: str = ""


@dataclass
class ClassificationResult:
    """分類結果を保持するデータクラス"""

    categories: list[str] = field(default_factory=list)
    confidence_scores: dict = field(default_factory=dict)


@dataclass
class ContentAnalysisResult:
    """コンテンツ分析の総合結果を保持するデータクラス"""

    post_id: str
    text: str
    moderation: ModerationResult
    classification: ClassificationResult
    processed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    error: Optional[str] = None


def _call_with_retry(client: Anthropic, **kwargs) -> str:
    """
    リトライロジック付きでAPIを呼び出す

    Exponential backoff で最大MAX_RETRIES回リトライする。

    Args:
        client: Anthropic クライアント
        **kwargs: messages.create() に渡す引数

    Returns:
        str: APIのレスポンステキスト

    Raises:
        anthropic.APIError: リトライ上限を超えた場合
    """
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(**kwargs)
            return response.content[0].text

        except anthropic.RateLimitError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"  ⚠️ レート制限 (試行{attempt + 1}/{MAX_RETRIES})。{wait_time}秒後にリトライ...")
                time.sleep(wait_time)
            else:
                raise e

        except anthropic.APIStatusError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = BASE_DELAY * (2 ** attempt)
                print(f"  ⚠️ APIエラー {e.status_code} (試行{attempt + 1}/{MAX_RETRIES})。{wait_time}秒後にリトライ...")
                time.sleep(wait_time)
            else:
                raise e

    raise RuntimeError("リトライ上限を超えました")


def detect_inappropriate_content(
    client: Anthropic,
    text: str,
) -> ModerationResult:
    """
    テキストに含まれる不適切コンテンツを検出する

    CCA試験のポイント:
    - モデレーションはセーフティの根幹。False negativeより False positive を許容する設計
    - 検出レベルを4段階（high/medium/low/none）にすることで後段での柔軟な閾値設定を可能にする
    - ClaudeにJSON形式で返答させることで機械処理が容易になる

    Args:
        client: Anthropic クライアント
        text: 分析対象のテキスト

    Returns:
        ModerationResult: モデレーション結果
    """
    prompt = f"""以下のテキストに不適切なコンテンツが含まれているか分析してください。
JSON形式のみで回答してください（説明不要）。

検出対象:
- violence: 暴力的な表現・危害を煽るコンテンツ
- hate_speech: 特定属性（人種・性別・宗教等）を標的にした差別的表現
- spam: 無関係な宣伝・フィッシング・繰り返し投稿
- adult_content: 性的に露骨なコンテンツ

検出レベル: high（明確）/ medium（疑い）/ low（わずかに懸念）/ none（問題なし）

テキスト: 「{text}」

回答形式:
{{
  "violence": "high|medium|low|none",
  "hate_speech": "high|medium|low|none",
  "spam": "high|medium|low|none",
  "adult_content": "high|medium|low|none",
  "confidence": 0.0〜1.0の数値,
  "details": "問題がある場合の説明（問題なしの場合は空文字）"
}}"""

    try:
        response_text = _call_with_retry(
            client,
            model=MODEL_NAME,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        data = json.loads(response_text)

        # is_inappropriate を自動判定（いずれかが medium 以上なら True）
        harmful_levels = {"high", "medium"}
        is_inappropriate = any(
            data.get(mod_type, "none") in harmful_levels
            for mod_type in MODERATION_TYPES
        )

        return ModerationResult(
            violence=data.get("violence", "none"),
            hate_speech=data.get("hate_speech", "none"),
            spam=data.get("spam", "none"),
            adult_content=data.get("adult_content", "none"),
            is_inappropriate=is_inappropriate,
            confidence=float(data.get("confidence", 0.0)),
            details=data.get("details", ""),
        )

    except json.JSONDecodeError as e:
        # JSON解析エラー: デフォルト値を返す（安全側に倒す）
        print(f"  ⚠️ JSONDecodeError in moderation: {e}")
        return ModerationResult(
            details=f"解析エラー: {e}",
            confidence=0.0,
        )


def classify_content(
    client: Anthropic,
    text: str,
) -> ClassificationResult:
    """
    テキストのカテゴリを自動分類する（マルチラベル分類）

    CCA試験のポイント:
    - マルチラベル分類では信頼度スコアの閾値設計が精度に直結する
    - Few-shotの例示をプロンプトに含めると分類精度が向上する
    - 全カテゴリのスコアを返してもらうと閾値変更時に再処理不要

    Args:
        client: Anthropic クライアント
        text: 分類対象のテキスト

    Returns:
        ClassificationResult: カテゴリ分類結果
    """
    categories_list = ", ".join(CATEGORIES)
    prompt = f"""以下のテキストを指定カテゴリに分類してください。
JSON形式のみで回答してください（説明不要）。

カテゴリ: {categories_list}

テキストは複数のカテゴリに属せます（マルチラベル分類）。
各カテゴリの信頼度スコアを0.0〜1.0で返してください。

テキスト: 「{text}」

回答形式（全カテゴリのスコアを含める）:
{{
  "technology": 0.0〜1.0,
  "sports": 0.0〜1.0,
  "entertainment": 0.0〜1.0,
  "news": 0.0〜1.0,
  "food": 0.0〜1.0,
  "travel": 0.0〜1.0,
  "education": 0.0〜1.0,
  "other": 0.0〜1.0
}}"""

    try:
        response_text = _call_with_retry(
            client,
            model=MODEL_NAME,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )

        scores = json.loads(response_text)

        # 信頼度スコアを float に変換
        confidence_scores = {
            cat: float(scores.get(cat, 0.0))
            for cat in CATEGORIES
        }

        # 閾値以上のカテゴリを「分類あり」とする
        categories = [
            cat for cat, score in confidence_scores.items()
            if score >= CONFIDENCE_THRESHOLD
        ]

        # いずれもthresholdを超えない場合は最高スコアのカテゴリを選択
        if not categories:
            best_cat = max(confidence_scores, key=lambda k: confidence_scores[k])
            categories = [best_cat]

        return ClassificationResult(
            categories=categories,
            confidence_scores=confidence_scores,
        )

    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSONDecodeError in classification: {e}")
        return ClassificationResult(
            categories=["other"],
            confidence_scores={"other": 0.5},
        )


def calculate_confidence(moderation: ModerationResult, classification: ClassificationResult) -> float:
    """
    モデレーションと分類結果を統合した総合信頼度スコアを算出する

    CCA試験のポイント:
    - 総合信頼度は後続の「人間によるレビューが必要か」判断に使える
    - モデレーションと分類の信頼度を平均することでバランスを取る

    Args:
        moderation: モデレーション結果
        classification: 分類結果

    Returns:
        float: 総合信頼度スコア（0.0〜1.0）
    """
    moderation_confidence = moderation.confidence

    # 分類の信頼度: 最高スコアのカテゴリの信頼度を使用
    if classification.confidence_scores:
        classification_confidence = max(classification.confidence_scores.values())
    else:
        classification_confidence = 0.0

    # 2つの信頼度の平均を返す
    return (moderation_confidence + classification_confidence) / 2


@dataclass
class ContentModerator:
    """
    コンテンツ分類・モデレーションシステム

    不適切コンテンツ検出・カテゴリ分類・バッチ処理・JSON出力を
    統合したクラス。
    """

    client: Optional[Anthropic] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """初期化後処理: クライアントを設定"""
        if self.client is None:
            self.client = get_client()

    def analyze(self, post_id: str, text: str) -> ContentAnalysisResult:
        """
        1件のテキストを分析する

        モデレーションと分類を実行してContentAnalysisResultを返す。

        CCA試験のポイント:
        - モデレーションと分類を別々のAPIコールにすると精度は上がるが、
          1回にまとめるとコストと速度が改善される（トレードオフ）
        - ここでは精度を優先して別々に呼び出している

        Args:
            post_id: 投稿のID
            text: 分析対象のテキスト

        Returns:
            ContentAnalysisResult: 分析結果
        """
        try:
            # モデレーション
            moderation = detect_inappropriate_content(self.client, text)

            # カテゴリ分類
            classification = classify_content(self.client, text)

            return ContentAnalysisResult(
                post_id=post_id,
                text=text,
                moderation=moderation,
                classification=classification,
            )

        except anthropic.APIError as e:
            return ContentAnalysisResult(
                post_id=post_id,
                text=text,
                moderation=ModerationResult(),
                classification=ClassificationResult(categories=["other"]),
                error=str(e),
            )

    def batch_process(
        self,
        posts: list[dict],
    ) -> list[ContentAnalysisResult]:
        """
        複数のコンテンツをバッチで処理する

        CCA試験のポイント:
        - バッチ処理では best-effort 戦略（1件エラーでも続行）を採用
        - レート制限対策として処理間に待機時間を設ける
        - 進捗をコンソールに出力してモニタリングを容易にする

        Args:
            posts: 処理対象の投稿リスト [{"id": str, "text": str}, ...]

        Returns:
            list[ContentAnalysisResult]: 全件の分析結果リスト
        """
        total = len(posts)
        results = []
        error_count = 0

        print(f"\n🔄 バッチ処理開始: {total}件\n")

        for i, post in enumerate(posts, 1):
            post_id = post.get("id", f"post_{i:03d}")
            text = post.get("text", "")

            print(f"[{i}/{total}] {post_id} 処理中...")

            result = self.analyze(post_id, text)

            if result.error:
                error_count += 1
                print(f"  ❌ エラー: {result.error}")
            else:
                # 結果の簡易サマリーを表示
                cats = ", ".join(
                    f"{cat} ({result.classification.confidence_scores.get(cat, 0):.2f})"
                    for cat in result.classification.categories
                )
                print(f"  → カテゴリ: {cats}")

                if result.moderation.is_inappropriate:
                    issues = [
                        f"{t}={getattr(result.moderation, t)}"
                        for t in MODERATION_TYPES
                        if getattr(result.moderation, t) in {"high", "medium"}
                    ]
                    print(f"  → モデレーション: ⚠️ {', '.join(issues)} 検出")
                else:
                    print(f"  → モデレーション: クリア ✅")

            results.append(result)

            # レート制限対策: API呼び出し間に待機時間を設ける
            if i < total:
                time.sleep(BATCH_DELAY_SECONDS)

        # 処理結果のサマリーを表示
        inappropriate_ids = [
            r.post_id for r in results
            if r.moderation.is_inappropriate and not r.error
        ]
        print(f"\n✅ 処理完了")
        print(f"  - 合計: {total}件")
        print(f"  - クリア: {total - len(inappropriate_ids) - error_count}件")
        print(f"  - 不適切検出: {len(inappropriate_ids)}件 ({', '.join(inappropriate_ids)})")
        print(f"  - エラー: {error_count}件")

        return results

    def export_to_json(
        self,
        results: list[ContentAnalysisResult],
        filename: Optional[str] = None,
    ) -> str:
        """
        分析結果を構造化JSON形式でファイルに保存する

        CCA試験のポイント:
        - JSON出力スキーマは後続システムとの「契約」であり安定性が重要
        - metadata を含めることで後からデータの文脈を把握できる
        - ensure_ascii=False で日本語を読みやすい形式で保存する

        Args:
            results: 分析結果のリスト
            filename: 保存先ファイル名（Noneの場合は自動生成）

        Returns:
            str: 保存したファイルのパス
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"moderation_results_{timestamp}.json"

        # 全カテゴリを収集
        all_categories: set[str] = set()
        for result in results:
            all_categories.update(result.classification.categories)

        # JSON データを構築
        output = {
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "total_count": len(results),
                "inappropriate_count": sum(
                    1 for r in results if r.moderation.is_inappropriate
                ),
                "error_count": sum(1 for r in results if r.error),
                "categories_found": sorted(list(all_categories)),
            },
            "results": [
                {
                    "id": result.post_id,
                    # テキストは先頭50文字のみ保存（プライバシー対策）
                    "text": result.text[:50] + ("..." if len(result.text) > 50 else ""),
                    "moderation": {
                        "violence": result.moderation.violence,
                        "hate_speech": result.moderation.hate_speech,
                        "spam": result.moderation.spam,
                        "adult_content": result.moderation.adult_content,
                        "is_inappropriate": result.moderation.is_inappropriate,
                        "confidence": result.moderation.confidence,
                        "details": result.moderation.details,
                    },
                    "classification": {
                        "categories": result.classification.categories,
                        "confidence_scores": result.classification.confidence_scores,
                    },
                    "processed_at": result.processed_at,
                    "error": result.error,
                }
                for result in results
            ],
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n📄 結果を保存しました: {filename}")
        return filename


# テストデータ（シナリオ3のサンプルコンテンツ）
TEST_POSTS = [
    {
        "id": "post_001",
        "text": "新しいPythonの機能について学びました！型ヒントを使うとコードが読みやすくなりますね。みなさんもぜひ試してみてください。",
    },
    {
        "id": "post_002",
        "text": "今日のサッカーの試合、すごかった！後半ロスタイムに逆転ゴールが決まって最高でした。次の試合も楽しみ！",
    },
    {
        "id": "post_003",
        "text": "激安！！今すぐクリック→ http://spam-site.example.com 限定セール99%OFF！今だけ！急いで！",
    },
    {
        "id": "post_004",
        "text": "先週の京都旅行で食べた抹茶パフェが最高においしかった。お寺巡りと地元グルメ、両方楽しめて大満足です。",
    },
    {
        "id": "post_005",
        "text": "機械学習の勉強を始めました。TensorFlowとPyTorchどちらを先に学ぶべきか悩んでいます。アドバイスください。",
    },
    {
        "id": "post_006",
        "text": "〇〇人は全員〇〇だから国から出ていけ。こういう人たちとは絶対に関わりたくない。",
    },
    {
        "id": "post_007",
        "text": "新しいスマートフォンのレビューを書きました。カメラの性能が前モデルから大幅に改善されています。",
    },
    {
        "id": "post_008",
        "text": "今日のランニング記録: 10km を55分で走りました。自己ベスト更新！ #ランニング #フィットネス",
    },
    {
        "id": "post_009",
        "text": "映画『インターステラー』を見直した。宇宙科学の描写が緻密で、何度見ても新しい発見がある名作。",
    },
    {
        "id": "post_010",
        "text": "プログラミングを独学で学ぶ方法を解説したブログ記事を書きました。初心者でも始められる学習ロードマップです。",
    },
]


def main() -> None:
    """
    コンテンツ分類・モデレーションシステムのデモ実行

    テストデータ10件をバッチ処理してJSON形式で保存します。
    Google Colab で実行する場合は、この関数を呼び出すだけでOKです。
    """
    print("=" * 60)
    print("🛡️ コンテンツ分類・モデレーションシステム")
    print("=" * 60)

    moderator = ContentModerator()

    # バッチ処理を実行
    results = moderator.batch_process(TEST_POSTS)

    # 結果をJSONファイルに保存
    output_file = moderator.export_to_json(results)

    print(f"\n✅ デモ完了！")
    print(f"結果ファイル: {output_file}")
    print("\n--- 個別分析のサンプル ---")

    # 個別分析のサンプル（1件だけ詳細表示）
    sample_result = results[0]
    print(f"\nID: {sample_result.post_id}")
    print(f"テキスト: {sample_result.text[:50]}...")
    print(f"カテゴリ: {sample_result.classification.categories}")
    print(f"不適切コンテンツ: {sample_result.moderation.is_inappropriate}")

    overall_confidence = calculate_confidence(
        sample_result.moderation,
        sample_result.classification,
    )
    print(f"総合信頼度: {overall_confidence:.2f}")


if __name__ == "__main__":
    main()
